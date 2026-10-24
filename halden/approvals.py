"""Couche 7 · File d'approbation : un humain approuve, rejette ou prend en charge."""
from __future__ import annotations

import datetime as dt

from . import audit
from .db import Database
from .execution import executer


def en_attente(db: Database) -> list[dict]:
    return db.where("File_Approbation", statut="EN ATTENTE")


def decider(db: Database, file_id: str, approuve: bool, par: str, today: dt.date,
            commentaire: str = "", brouillon_modifie: str | None = None) -> dict:
    item = db.get("File_Approbation", file_id=file_id)
    if item is None:
        raise KeyError(f"{file_id} introuvable")
    if item["statut"] != "EN ATTENTE":
        raise ValueError(f"{file_id} est déjà {item['statut']}")
    if brouillon_modifie:
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
