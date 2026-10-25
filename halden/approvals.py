"""Couche 7 · File d'approbation : un humain approuve, rejette ou prend en charge."""
from __future__ import annotations

import datetime as dt

import json

from . import audit, guardrails, rules
from .db import Database
from .execution import executer
from .proposition import Proposition


def autorise(db: Database, par: str) -> bool:
    """POC : liste de noms dans Parametres. Pilote : vraie connexion (SSO du promoteur) obligatoire."""
    liste = [x.strip() for x in str(db.param("approbateurs_autorises", "") or "").split(";") if x.strip()]
    return not liste or par in liste


def en_attente(db: Database) -> list[dict]:
    return db.where("File_Approbation", statut="EN ATTENTE")


def decider(db: Database, file_id: str, approuve: bool, par: str, today: dt.date,
            commentaire: str = "", brouillon_modifie: str | None = None) -> dict:
    item = db.get("File_Approbation", file_id=file_id)
    if item is None:
        raise KeyError(f"{file_id} introuvable")
    if item["statut"] != "EN ATTENTE":
        raise ValueError(f"{file_id} est déjà {item['statut']}")
    if not autorise(db, par):
        audit.log(db, today, par, "Humain", "DÉCISION_REFUSÉE", file_id, "approbateur non autorisé", item["niveau"])
        raise PermissionError(f"{par} n'est pas dans approbateurs_autorises")
    if brouillon_modifie:
        # Un brouillon modifié par un humain repasse le contrôle des nombres, comme celui de l'IA.
        payload = json.loads(item["payload"] or "{}")
        c = payload.get("controle", {})
        p = Proposition(agent=item["agent"], tache_id=item["tache_id"], action=item["action"], resume="",
                        brouillon=brouillon_modifie, objet=payload.get("objet"), canal=payload.get("canal"),
                        montants_regles=c.get("montants", []), faits=c.get("faits", {}),
                        modele_texte=c.get("modele_texte", ""))
        fautes = guardrails.controler_nombres(p) if p.canal else []
        if fautes:
            audit.log(db, today, par, "Garde-fous", "BROUILLON_MODIFIÉ_REJETÉ", file_id, ", ".join(fautes), rules.BLOQUE)
            raise ValueError(f"Brouillon modifié rejeté : {', '.join(fautes)} absent(s) du moteur de règles")
        item["brouillon"] = brouillon_modifie
        commentaire = (commentaire + " · brouillon modifié").strip(" ·")
    item.update(decide_par=par, date_decision=today, commentaire=commentaire)
    if not approuve:
        item["statut"] = "REJETÉ"
        audit.log(db, today, par, "Humain", "REJETÉ", file_id, commentaire or item["resume"], item["niveau"])
        return item
    item["statut"] = "APPROUVÉ" if item["niveau"] == "VALIDATION" else "PRIS EN CHARGE"
    audit.log(db, today, par, "Humain", item["statut"], file_id, commentaire or item["resume"], item["niveau"])
    executer(db, item, today, par)
    return item
