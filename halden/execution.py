"""Couche 7 · Sorties : exécuter une proposition autorisée (en mode shadow, rien ne sort).

C'est le seul endroit qui modifie l'échéancier ou crée un message sortant.
Aucune fonction ici ne déplace d'argent : un « lettrage » constate un virement déjà reçu.
"""
from __future__ import annotations

import datetime as dt
import json

from . import audit, rules
from .db import Database


def _sortant(db: Database, today: dt.date, item: dict, statut: str) -> None:
    db.add("Messages_Sortants", {
        "sortant_id": db.next_id("Messages_Sortants", "OUT-"), "date": today, "acheteur_id": item.get("acheteur_id"),
        "canal": item.get("canal"), "langue": item.get("langue"), "objet": item.get("objet"),
        "texte": item.get("brouillon"), "agent": item["agent"], "statut": statut, "cle": item["cle"]})


def executer(db: Database, item: dict, today: dt.date, acteur: str) -> str:
    """`item` est une ligne de File_Approbation (ou une proposition autonome mise au même format)."""
    payload = item["payload"] if isinstance(item["payload"], dict) else json.loads(item["payload"] or "{}")
    item = {**{k: payload.get(k) for k in ("canal", "langue", "objet")},
            **{k: v for k, v in item.items() if v is not None}}
    shadow = str(db.param("mode_shadow", "OUI")).upper() == "OUI"
    statut_msg = "SHADOW · NON ENVOYÉ" if shadow else "ENVOYÉ"
    action = item["action"]

    if action == "APPEL_DE_FONDS":
        e = db.get("Echeancier", echeance_id=payload["echeance_id"])
        e.update(statut="APPELÉ", date_appel=today, date_limite=dt.date.fromisoformat(payload["date_limite"]))
        _sortant(db, today, item, statut_msg)
        detail = f"{e['echeance_id']} appelée, limite {e['date_limite']}"
    elif action == "MESSAGE":
        _sortant(db, today, item, statut_msg)
        if "relance" in payload:
            r = payload["relance"]
            db.add("Relances", {"relance_id": db.next_id("Relances", "REL-"), "date": today,
                                "echeance_id": r["echeance_id"], "acheteur_id": item.get("acheteur_id"),
                                "niveau": r["niveau"], "jours_retard": r["retard"], "canal": item.get("canal"),
                                "statut": statut_msg})
        if "lead_id" in payload:
            db.get("Leads", lead_id=payload["lead_id"])["statut"] = "CONTACTÉ"
        detail = f"message « {item.get('objet')} » · {statut_msg}"
    elif action == "LETTRAGE":
        ligne = db.get("Releve_Bancaire", ligne_id=payload["ligne_id"])
        restant = round(float(ligne["montant_aed"]), 2)
        for eid in payload["echeances"]:
            e = db.get("Echeancier", echeance_id=eid)
            part = min(restant, rules.reste_du(e))
            e["montant_paye_aed"] = round(float(e["montant_paye_aed"] or 0) + part, 2)
            restant = round(restant - part, 2)
            e["statut"] = "PAYÉ" if rules.reste_du(e) <= 0.009 else "PARTIEL"
        ligne.update(statut="LETTRÉ", echeance_id=", ".join(payload["echeances"]))
        detail = f"{ligne['ligne_id']} lettrée sur {', '.join(payload['echeances'])}" + (
            f" · excédent {rules.fmt_aed(restant)} à traiter" if restant > 0 else "")
    elif action == "ORDRE_RESERVE":
        r = db.get("Reserves", reserve_id=payload["reserve_id"])
        st = db.get("Sous_Traitants", st_id=payload["st"])
        r.update(statut="ASSIGNÉE", sous_traitant=st["nom"] if st else None,
                 date_sla=dt.date.fromisoformat(payload["sla"]))
        _sortant(db, today, item, statut_msg)
        detail = f"{r['reserve_id']} → {r['sous_traitant']}"
    else:  # ESCALADE, IDENTIFIER_ENCAISSEMENT : la décision humaine est la sortie
        detail = "pris en charge par un humain, hors Halden"
    audit.log(db, today, acteur, "Sorties", f"EXÉCUTÉ · {action}", item.get("file_id") or item["cle"], detail,
              item.get("niveau", ""))
    return detail
