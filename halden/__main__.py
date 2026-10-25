"""Ligne de commande Halden.

    python -m halden demo                 # scénario complet en 3 journées simulées
    python -m halden console              # console web locale (http://localhost:8765)
    python -m halden init                 # recrée la base Excel fictive
    python -m halden cycle --date 2026-11-02
    python -m halden file                 # file d'approbation
    python -m halden approuver APP-0001   # ou: rejeter APP-0001 --commentaire "..."
    python -m halden cfo                  # vue CFO
    python -m halden audit                # vérifie la chaîne du journal d'audit
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

from . import BASE, ENTREES, LOGO_PNG, approvals, audit, cfo, historique, rules, seed
from .agents import AGENTS
from .db import Database
from .llm import LLM
from .orchestrator import Bilan, cycle

if os.name == "nt":
    os.system("")  # active les couleurs ANSI dans le terminal Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

OR, GRIS, BLANC, ROUGE, VERT, RESET, GRAS = ("\033[38;5;179m", "\033[38;5;245m", "\033[97m", "\033[38;5;167m",
                                             "\033[38;5;108m", "\033[0m", "\033[1m")
COULEUR = {"AUTONOME": VERT, "RÈGLE": VERT, "VALIDATION": OR, "HUMAIN": ROUGE, "BLOQUÉ": ROUGE}


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]


def date_fr(d: dt.date) -> str:
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def titre(t: str) -> None:
    print(f"\n{OR}{'─' * 78}{RESET}\n{GRAS}{BLANC}  {t}{RESET}\n{OR}{'─' * 78}{RESET}")


def banniere() -> None:
    print(f"""{OR}
    ╭──╮   {BLANC}{GRAS}H  A  L  D  E  N{RESET}{OR}
    │││││   {GRIS}Every promise, carried through.{OR}
   ─┴┴┴┴┴─  {GRIS}POC · moteur agentique supervisé · données fictives{RESET}""")


def afficher_bilan(b: Bilan) -> None:
    titre(f"Cycle du {date_fr(b.date)}")
    for f in b.import_releve:
        print(f"  {GRIS}Ingestion{RESET}  relevé importé : {f}")
    for e in b.evenements:
        print(f"  {GRIS}Événement{RESET}  {e['label']}")
    print()
    for agent in AGENTS:
        if agent.nom not in b.par_agent:
            continue
        s = b.par_agent.get(agent.nom, {})
        detail = "  ".join(f"{COULEUR.get(k, '')}{k.lower()} {v}{RESET}" for k, v in s.items()
                           if k != "propositions" and v)
        print(f"  {OR}{agent.etape:<34}{RESET}{BLANC}{agent.nom:<22}{RESET}{s.get('propositions', 0):>3} prop.  {detail}")
    print()
    for p in b.propositions:
        c = COULEUR.get(p.niveau, "")
        print(f"   {c}● {p.niveau:<10}{RESET} {GRIS}{p.agent:<20}{RESET} {p.resume[:92]}")


def ouvrir(path=BASE) -> Database:
    if not path.exists():
        print("Base absente : génération des données fictives…")
        seed.generer(path, ENTREES, LOGO_PNG)
    return Database.load(path)


def sauver(db: Database) -> None:
    db.save(LOGO_PNG)


def jour(db: Database, s: str | None) -> dt.date:
    return dt.date.fromisoformat(s) if s else db.param("date_simulation")


def decider_lot(db: Database, today: dt.date, regle, interactif: bool) -> list[dict]:
    """Simule le CFO qui passe sur la file : `regle(item)` renvoie (approuve, commentaire) ou None."""
    par = db.param("approbateur", "Approbateur")
    faits = []
    for item in list(approvals.en_attente(db)):
        choix = regle(item)
        if interactif and item["niveau"] == "VALIDATION":
            print(f"\n{OR}{item['file_id']}{RESET} {item['resume']}\n{GRIS}{(item['brouillon'] or '')[:400]}{RESET}")
            rep = input(f"  Approuver ? [o]ui / [n]on / [p]asser : ").strip().lower()
            choix = None if rep.startswith("p") else ((True, "") if rep.startswith("o") else (False, "Rejeté en séance"))
        if choix is None:
            continue
        ok, com = choix
        approvals.decider(db, item["file_id"], ok, par, today, com)
        faits.append({"file_id": item["file_id"], "decision": "APPROUVÉ" if ok else "REJETÉ", "resume": item["resume"]})
        c = VERT if ok else ROUGE
        print(f"   {c}{'✓ approuvé' if ok else '✗ rejeté '}{RESET}  {GRIS}{par}{RESET}  {item['resume'][:80]}")
    return faits


def demo(interactif: bool = False, vision: bool = False) -> None:
    banniere()
    llm = LLM()
    print(f"\n  Moteur IA : {OR}{llm.libelle}{RESET} · base : {BASE.relative_to(BASE.parent.parent)}")
    print(f"  Périmètre : {OR}{'VISION · les six agents' if vision else 'PILOTE · encaissements, Dubaï'}{RESET}"
          f" · règle : chaque message vers un acheteur est validé par un humain")
    seed.generer(BASE, ENTREES, LOGO_PNG)
    historique.reinitialiser()
    db = Database.load(BASE)
    if vision:
        db.set_param("perimetre", "VISION")

    # Jour 1 : le certificat 40 % arrive, les messages du week-end aussi.
    b = cycle(db, dt.date(2026, 11, 2), llm, ENTREES)
    afficher_bilan(b)
    titre("Le CFO passe sur la file d'approbation (2 nov.)")
    rejet_lead = {"LEAD:LEAD-006"}

    def regle_j1(item):
        if item["niveau"] != "VALIDATION":
            return None
        if item["cle"] in rejet_lead:
            return False, "Lead hors cible, ne pas relancer."
        return True, ""
    d = decider_lot(db, b.date, regle_j1, interactif)
    historique.ajouter(b, d)
    sauver(db)

    # Jour 2 : le relevé escrow du 28 nov. est déposé.
    db = Database.load(BASE)
    b = cycle(db, dt.date(2026, 11, 28), llm, ENTREES)
    afficher_bilan(b)
    titre("Le CFO valide les rapprochements ambigus (28 nov.)")
    def regle_j2(item):
        if item["niveau"] != "VALIDATION":
            return None
        if item["action"] == "LETTRAGE" and "autre acheteur" in item["resume"]:
            return False, "Payeur différent du titulaire : appeler les deux acheteurs avant d'affecter."
        if item["action"] in ("LETTRAGE", "ANNULER_LETTRAGE"):
            return True, "Vérifié sur l'avis de virement" if item["action"] == "LETTRAGE" else "Rejet confirmé par la banque"
        return None
    d = decider_lot(db, b.date, regle_j2, interactif)
    historique.ajouter(b, d)
    sauver(db)

    # Jour 3 : les minuteries tournent.
    db = Database.load(BASE)
    b = cycle(db, dt.date(2026, 12, 5), llm, ENTREES)
    afficher_bilan(b)
    historique.ajouter(b)
    sauver(db)

    titre("Vue CFO du matin · 5 décembre 2026")
    print(cfo.texte(cfo.vue(db, b.date)))
    ok, n = audit.verifier(db)
    titre("Journal d'audit")
    print(f"  {len(db.rows('Journal_Audit'))} entrées · chaîne de hash {'intègre ✓' if ok else f'ALTÉRÉE à la ligne {n}'}")
    print(f"\n  Base Excel mise à jour : {OR}{BASE}{RESET}")
    print(f"  Console web : {OR}python -m halden console{RESET}\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="halden", description="POC du moteur agentique Halden")
    sp = ap.add_subparsers(dest="cmd")
    d = sp.add_parser("demo", help="scénario complet en 3 journées")
    d.add_argument("--interactif", action="store_true", help="vous validez vous-même la file")
    d.add_argument("--vision", action="store_true", help="les six agents (par défaut : pilote encaissements)")
    r = sp.add_parser("reactiver", help="réactive le contact automatique d'un acheteur après décision humaine")
    r.add_argument("acheteur_id")
    r.add_argument("--par")
    sp.add_parser("init", help="recrée la base Excel fictive")
    c = sp.add_parser("cycle", help="lance un cycle des agents")
    c.add_argument("--date")
    sp.add_parser("file", help="affiche la file d'approbation")
    for nom in ("approuver", "rejeter"):
        x = sp.add_parser(nom)
        x.add_argument("file_id")
        x.add_argument("--commentaire", default="")
        x.add_argument("--par")
    sp.add_parser("cfo", help="vue CFO")
    sp.add_parser("audit", help="vérifie le journal d'audit")
    k = sp.add_parser("console", help="console web locale")
    k.add_argument("--port", type=int, default=8765)
    k.add_argument("--sans-navigateur", action="store_true")
    s = sp.add_parser("export", help="exporte la console en une page HTML autonome")
    s.add_argument("--sortie")
    a = ap.parse_args(argv)

    if a.cmd in (None, "demo"):
        demo(getattr(a, "interactif", False), getattr(a, "vision", False))
    elif a.cmd == "reactiver":
        db = ouvrir()
        ach = db.get("Acheteurs", acheteur_id=a.acheteur_id)
        par = a.par or db.param("approbateur")
        if not approvals.autorise(db, par):
            raise SystemExit(f"{par} n'est pas autorisé")
        ancien, ach["contact_auto"] = ach["contact_auto"], "ACTIF"
        audit.log(db, db.param("date_simulation"), par, "Humain", "CONTACT_AUTO_RÉACTIVÉ", a.acheteur_id,
                  f"était : {ancien}", "HUMAIN")
        sauver(db)
        print(f"{a.acheteur_id} : contact automatique réactivé")
    elif a.cmd == "init":
        seed.generer(BASE, ENTREES, LOGO_PNG)
        historique.reinitialiser()
        print(f"Base fictive créée : {BASE}")
    elif a.cmd == "cycle":
        db = ouvrir()
        b = cycle(db, jour(db, a.date), LLM(db.param("llm_mode")), ENTREES)
        afficher_bilan(b)
        historique.ajouter(b)
        sauver(db)
    elif a.cmd == "file":
        db = ouvrir()
        for f in approvals.en_attente(db):
            print(f"{OR}{f['file_id']}{RESET} {COULEUR.get(f['niveau'], '')}{f['niveau']:<10}{RESET} "
                  f"{GRIS}{f['agent']:<20}{RESET} {f['resume']}")
    elif a.cmd in ("approuver", "rejeter"):
        db = ouvrir()
        it = approvals.decider(db, a.file_id, a.cmd == "approuver", a.par or db.param("approbateur"),
                               db.param("date_simulation"), a.commentaire)
        historique.ajouter_decisions([{"file_id": it["file_id"], "decision": it["statut"], "resume": it["resume"]}])
        sauver(db)
        print(f"{it['file_id']} → {it['statut']}")
    elif a.cmd == "cfo":
        db = ouvrir()
        print(cfo.texte(cfo.vue(db, db.param("date_simulation"))))
    elif a.cmd == "audit":
        db = ouvrir()
        ok, n = audit.verifier(db)
        print("Journal intègre ✓" if ok else f"Journal ALTÉRÉ à partir de la ligne {n}")
    elif a.cmd == "console":
        from .console import servir
        servir(a.port, not a.sans_navigateur)
    elif a.cmd == "export":
        from .console import exporter
        print(exporter(a.sortie))


if __name__ == "__main__":
    main()
