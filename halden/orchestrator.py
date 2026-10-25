"""Couche 3 · Orchestrateur : détecter les événements, router vers les agents,
passer chaque proposition aux garde-fous, puis exécuter ou mettre en file d'approbation.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

from . import audit, guardrails, ingestion, rules, signaux
from .agents import AGENTS, agents_actifs
from .agents.base import Contexte
from .db import Database
from .execution import executer
from .llm import LLM
from .proposition import Proposition


@dataclass
class Bilan:
    date: dt.date
    evenements: list[dict] = field(default_factory=list)
    par_agent: dict[str, dict[str, int]] = field(default_factory=dict)
    propositions: list[Proposition] = field(default_factory=list)
    import_releve: list[str] = field(default_factory=list)


def detecter(db: Database, today: dt.date) -> list[dict]:
    ev = []
    for j in db.where("Jalons", statut="CERTIFIÉ"):
        if j["date_certificat"] and j["date_certificat"] <= today:
            ev.append({"type": "JALON_CERTIFIE", "jalon": j, "label": f"Certificat {j['certificat_ref']} · {j['libelle']}"})
    for ligne in db.where("Releve_Bancaire", statut="NOUVEAU"):
        sens = "Débit" if ligne.get("sens") == "DÉBIT" else "Virement"
        ev.append({"type": "LIGNE_BANCAIRE", "ligne": ligne,
                   "label": f"{sens} {rules.fmt_aed(float(ligne['montant_aed']))} · {ligne['donneur_ordre']}"})
    n = len(db.where("Messages_Entrants", statut="NOUVEAU"))
    if n:
        ev.append({"type": "MESSAGES", "label": f"{n} message(s) d'acquéreurs"})
    return ev


def cycle(db: Database, today: dt.date, llm: LLM | None = None, entrees_dir=None) -> Bilan:
    llm = llm or LLM(db.param("llm_mode"))
    bilan = Bilan(today)
    db.set_param("date_simulation", today)
    audit.log(db, today, "Orchestrateur", "Orchestrateur", "DÉBUT_CYCLE", today.isoformat(),
              f"Moteur IA : {llm.libelle} · shadow = {db.param('mode_shadow')}")

    # Couche 2 · Ingestion des fichiers déposés (relevés escrow)
    if entrees_dir:
        bilan.import_releve = ingestion.importer_releves(db, entrees_dir, today)

    bilan.evenements = detecter(db, today)
    for ev in bilan.evenements:
        audit.log(db, today, "Orchestrateur", "Orchestrateur", f"ÉVÉNEMENT · {ev['type']}", "", ev["label"])

    ctx = Contexte(db=db, today=today, llm=llm, evenements=bilan.evenements)
    # Signaux d'abord : un acheteur qui écrit « j'ai payé » ou « avocat » ne reçoit plus rien d'automatique.
    for m in db.where("Messages_Entrants", statut="NOUVEAU"):
        sig = signaux.detecter(m["texte"])
        if sig:
            m["signaux"] = ", ".join(sig)
            ctx.suspendus[m["acheteur_id"]] = f"signal {m['signaux']} ({m['msg_id']})"
            signaux.suspendre(db, today, m["acheteur_id"], m["signaux"])
            audit.log(db, today, "Orchestrateur", "Garde-fous", "CONTACT_AUTO_SUSPENDU", m["acheteur_id"],
                      f"Signal {m['signaux']} dans {m['msg_id']}", rules.HUMAIN)

    actifs = agents_actifs(db)
    par_agent: dict[str, list[Proposition]] = {}
    for agent in actifs:
        par_agent[agent.nom] = [p for p in agent.executer(ctx) if not ctx.deja_fait(p.cle)]

    # Une seule conversation par acheteur : si un dossier part chez un humain, aucune relance ne part.
    # Et si l'acheteur vient d'écrire, la réponse passe avant la relance (qui attend le cycle suivant).
    escalades = {p.acheteur_id for ps in par_agent.values() for p in ps if p.action == "ESCALADE" and p.acheteur_id}
    reponses = {p.acheteur_id for ps in par_agent.values() for p in ps
                if p.action == "MESSAGE" and p.cle.startswith(("REPONSE:", "ATTENTE:"))}
    for nom, ps in par_agent.items():
        garder = []
        for p in ps:
            if "relances" in p.payload and p.acheteur_id in escalades | reponses:
                pourquoi = ("un dossier de cet acheteur part chez un humain" if p.acheteur_id in escalades
                            else "une réponse à son message est en préparation")
                audit.log(db, today, nom, "Orchestrateur", "RELANCE_RETIRÉE", p.acheteur_id,
                          f"{p.resume} · {pourquoi} dans ce cycle", rules.REGLE)
                continue
            garder.append(p)
        par_agent[nom] = garder

    for agent in actifs:
        stats = {"propositions": 0, "AUTONOME": 0, "RÈGLE": 0, "VALIDATION": 0, "HUMAIN": 0, "BLOQUÉ": 0}
        for p in par_agent[agent.nom]:
            guardrails.evaluer(db, p)
            stats["propositions"] += 1
            stats[p.niveau] = stats.get(p.niveau, 0) + 1
            traiter(db, p, today)
            bilan.propositions.append(p)
        bilan.par_agent[agent.nom] = stats

    for ev in bilan.evenements:
        if ev["type"] == "JALON_CERTIFIE":
            ev["jalon"]["statut"] = "TRAITÉ"
            projet = db.get("Projets", projet_id=ev["jalon"]["projet_id"])
            projet["avancement_pct"] = max(projet["avancement_pct"] or 0, ev["jalon"]["seuil_pct"])
    for e in llm.journal:      # chaque repli est journalisé, pas seulement le premier
        audit.log(db, today, "Orchestrateur", "IA", "REPLI_MODE_SIMULÉ", "", e)
    llm.journal.clear()
    if llm.usage["appels"]:
        audit.log(db, today, "Orchestrateur", "IA", "CONSOMMATION_IA", llm.model,
                  f"{llm.usage['appels']} appels · {llm.usage['entree']} tokens entrée · {llm.usage['sortie']} sortie "
                  f"· ≈ USD {llm.cout_usd():.4f} (prix API publics)")
    audit.log(db, today, "Orchestrateur", "Orchestrateur", "FIN_CYCLE", today.isoformat(),
              f"{len(bilan.propositions)} propositions")
    return bilan


def _ligne_file(db: Database, p: Proposition, today: dt.date, statut: str) -> dict:
    return db.add("File_Approbation", {
        "file_id": db.next_id("File_Approbation", "APP-"), "date": today, "agent": p.agent, "tache_id": p.tache_id,
        "niveau": p.niveau, "acheteur_id": p.acheteur_id, "unite_id": p.unite_id, "resume": p.resume,
        "brouillon": p.brouillon, "montant_aed": p.montant if p.montant is not None else (p.montants_regles[0] if p.montants_regles else None),
        "raisons": " ".join(p.raisons), "statut": statut, "action": p.action,
        "payload": json.dumps({**p.payload, "canal": p.canal, "langue": p.langue, "objet": p.objet,
                               "controle": {"faits": p.faits, "montants": p.montants_regles,
                                            "modele_texte": p.modele_texte}},
                              ensure_ascii=False, default=str),
        "cle": p.cle})


def traiter(db: Database, p: Proposition, today: dt.date) -> None:
    if p.niveau in (rules.AUTONOME, rules.REGLE):
        item = {"agent": p.agent, "acheteur_id": p.acheteur_id, "canal": p.canal, "langue": p.langue,
                "objet": p.objet, "brouillon": p.brouillon, "cle": p.cle, "action": p.action,
                "payload": p.payload, "niveau": p.niveau}
        audit.log(db, today, p.agent, "Garde-fous", f"AUTORISÉ · {p.action}", p.cle, " ".join(p.raisons), p.niveau)
        executer(db, item, today, p.agent)
        return
    if p.niveau == rules.BLOQUE:
        ligne = _ligne_file(db, p, today, "BLOQUÉ")
        audit.log(db, today, "Garde-fous", "Garde-fous", f"BLOQUÉ · {p.action}", ligne["file_id"], " ".join(p.raisons),
                  p.niveau)
        esc = Proposition(agent=p.agent, tache_id="T13", action="ESCALADE", acheteur_id=p.acheteur_id,
                          unite_id=p.unite_id, resume=f"Action bloquée par les garde-fous → humain : {p.resume}",
                          brouillon=p.brouillon, montants_regles=p.montants_regles, engage_promoteur=True,
                          cle=f"{p.cle}:ESCALADE", niveau=rules.HUMAIN,
                          raisons=[f"Proposition {ligne['file_id']} bloquée : décision humaine requise."])
        ligne2 = _ligne_file(db, esc, today, "EN ATTENTE")
        audit.log(db, today, "Garde-fous", "Garde-fous", "ESCALADE · HUMAIN", ligne2["file_id"], esc.resume, rules.HUMAIN)
        return
    ligne = _ligne_file(db, p, today, "EN ATTENTE")
    audit.log(db, today, p.agent, "Garde-fous", f"EN FILE · {p.action}", ligne["file_id"], " ".join(p.raisons), p.niveau)
