"""Journal d'audit chaîné : chaque ligne contient le hash de la précédente.

Si quelqu'un modifie une ligne après coup dans Excel, `verifier()` le détecte.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json

from .db import Database


def _digest(prev: str, fields: dict) -> str:
    payload = json.dumps(fields, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256((prev + payload).encode("utf-8")).hexdigest()[:16]


HASHED = ("n", "date_simulee", "acteur", "couche", "action", "objet", "detail", "niveau")


def log(db: Database, today: dt.date, acteur: str, couche: str, action: str,
        objet: str = "", detail: str = "", niveau: str = "") -> dict:
    rows = db.rows("Journal_Audit")
    prev = rows[-1]["hash"] if rows else "GENESE"
    rec = {"n": len(rows) + 1, "horodatage": dt.datetime.now().replace(microsecond=0),
           "date_simulee": today, "acteur": acteur, "couche": couche, "action": action,
           "objet": objet, "detail": detail, "niveau": niveau}
    rec["hash_precedent"] = prev
    rec["hash"] = _digest(prev, {k: rec[k] or "" for k in HASHED})
    return db.add("Journal_Audit", rec)


def verifier(db: Database) -> tuple[bool, int | None]:
    """Renvoie (intègre, numéro de la première ligne altérée)."""
    prev = "GENESE"
    for r in db.rows("Journal_Audit"):
        if r["hash_precedent"] != prev or _digest(prev, {k: r[k] or "" for k in HASHED}) != r["hash"]:
            return False, r["n"]
        prev = r["hash"]
    return True, None
