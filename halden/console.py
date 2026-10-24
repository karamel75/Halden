"""Console web Halden : un serveur local (bibliothèque standard uniquement) et un export statique.

    python -m halden console      → http://localhost:8765
    python -m halden export       → sorties/halden_console.html (page autonome, lecture seule)
"""
from __future__ import annotations

import datetime as dt
import json
import threading
import webbrowser
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import BASE, ENTREES, LOGO_PNG, RACINE, SORTIES, approvals, audit, cfo, historique, seed
from .agents import AGENTS
from .db import Database
from .llm import LLM
from .orchestrator import cycle

GABARIT = Path(__file__).with_name("console.html")
VERROU = threading.Lock()


def _json(o):
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    return str(o)


def _logo() -> str:
    f = RACINE / "docs" / "assets" / "halden-logo-blanc.svg"
    return f.read_text(encoding="utf-8") if f.exists() else "<b>HALDEN</b>"


def etat(db: Database) -> dict:
    today = db.param("date_simulation")
    hist = historique.lire()
    stats: dict[str, Counter] = {a.nom: Counter() for a in AGENTS}
    for h in hist:
        for nom, s in h["par_agent"].items():
            stats.setdefault(nom, Counter()).update(s)
    file = db.rows("File_Approbation")
    sortants = db.rows("Messages_Sortants")
    agents = []
    for a in AGENTS:
        dern = [f for f in file if f["agent"] == a.nom][-4:]
        auto = [m for m in sortants if m["agent"] == a.nom][-4:]
        agents.append({"nom": a.nom, "etape": a.etape, "mission": a.mission, "stats": dict(stats[a.nom]),
                       "derniers": [f["resume"] for f in dern] + [m["objet"] or "" for m in auto]})
    ok, n = audit.verifier(db)
    journal = db.rows("Journal_Audit")
    gf = Counter()
    for j in journal:
        if j["couche"] == "Garde-fous":
            gf[j["action"].split(" · ")[0]] += 1
    acheteurs = {a["acheteur_id"]: a["nom"] for a in db.rows("Acheteurs")}
    return {
        "date": today, "shadow": db.param("mode_shadow"), "llm": LLM(db.param("llm_mode")).libelle,
        "promoteur": db.param("promoteur"), "approbateur": db.param("approbateur"),
        "cfo": cfo.vue(db, today), "agents": agents, "historique": hist,
        "file": [dict(f, acheteur=acheteurs.get(f["acheteur_id"], f["acheteur_id"] or "")) for f in file],
        "sortants": [dict(m, acheteur=acheteurs.get(m["acheteur_id"], m["acheteur_id"] or "")) for m in sortants],
        "journal": journal[-160:], "journal_total": len(journal), "integre": ok, "altere": n,
        "grille": db.rows("Grille_Decision"), "pack": db.rows("Pack_Pays"), "projets": db.rows("Projets"),
        "flux": {
            "entrees": len(db.rows("Messages_Entrants")) + len(db.rows("Releve_Bancaire")) + len(db.rows("Jalons"))
                       + len(db.rows("Reserves")) + len(db.rows("Garantie")) + len(db.rows("Leads")),
            "ingestion": len(db.rows("Releve_Bancaire")),
            "evenements": sum(len(h["evenements"]) for h in hist),
            "propositions": sum(sum(s.get("propositions", 0) for s in h["par_agent"].values()) for h in hist),
            "autorise": gf["AUTORISÉ"], "en_file": gf["EN FILE"], "bloque": gf["BLOQUÉ"],
            "lignes": sum(len(t) for t in db.tables.values()),
            "sortants": len(sortants), "decisions": len([f for f in file if f["decide_par"]]),
        },
        "releve": db.rows("Releve_Bancaire"),
    }


def page(data: dict, statique: bool) -> str:
    html = GABARIT.read_text(encoding="utf-8")
    payload = json.dumps(data, default=_json, ensure_ascii=False).replace("</", "<\\/")
    return (html.replace("/*__DATA__*/null", payload)
                .replace("/*__STATIQUE__*/false", "true" if statique else "false")
                .replace("<!--__LOGO__-->", _logo()))


def exporter(sortie: str | None = None) -> Path:
    db = Database.load(BASE)
    f = Path(sortie) if sortie else SORTIES / "halden_console.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(page(etat(db), True), encoding="utf-8")
    return f


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _send(self, code: int, body: str, ctype: str = "application/json") -> None:
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        with VERROU:
            db = Database.load(BASE)
            if self.path.startswith("/api/etat"):
                return self._send(200, json.dumps(etat(db), default=_json, ensure_ascii=False))
            return self._send(200, page(etat(db), False), "text/html")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        req = json.loads(self.rfile.read(n) or b"{}")
        try:
            with VERROU:
                if self.path == "/api/reinitialiser":
                    seed.generer(BASE, ENTREES, LOGO_PNG)
                    historique.reinitialiser()
                    db = Database.load(BASE)
                elif self.path == "/api/cycle":
                    db = Database.load(BASE)
                    jour = dt.date.fromisoformat(req["date"]) if req.get("date") else db.param("date_simulation")
                    b = cycle(db, jour, LLM(db.param("llm_mode")), ENTREES)
                    historique.ajouter(b)
                    db.save(LOGO_PNG)
                elif self.path == "/api/decider":
                    db = Database.load(BASE)
                    it = approvals.decider(db, req["file_id"], bool(req["approuve"]),
                                           db.param("approbateur"), db.param("date_simulation"),
                                           req.get("commentaire", ""), req.get("brouillon"))
                    historique.ajouter_decisions([{"file_id": it["file_id"], "decision": it["statut"],
                                                   "resume": it["resume"]}])
                    db.save(LOGO_PNG)
                else:
                    return self._send(404, '{"erreur": "inconnu"}')
                return self._send(200, json.dumps(etat(db), default=_json, ensure_ascii=False))
        except (KeyError, ValueError) as e:
            return self._send(400, json.dumps({"erreur": str(e)}, ensure_ascii=False))


def servir(port: int = 8765, navigateur: bool = True) -> None:
    if not BASE.exists():
        seed.generer(BASE, ENTREES, LOGO_PNG)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"Console Halden : {url}  (Ctrl+C pour arrêter)")
    if navigateur:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
