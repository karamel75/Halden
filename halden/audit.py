"""Journal d'audit chaîné et signé : chaque ligne contient l'empreinte HMAC de la précédente.

- Modifier une ligne après coup dans Excel casse la chaîne : `verifier()` le voit.
- Recalculer toute la chaîne est impossible sans la clé secrète (HALDEN_CLE_AUDIT, ou le
  fichier donnees/.cle_audit créé au premier lancement, hors Git et hors du classeur).
- Tronquer la fin du journal se voit aussi : la dernière empreinte et le nombre de lignes
  sont recopiés dans une ancre (donnees/.ancre_audit), hors du classeur.
En production : clé dans AWS KMS / Secrets Manager et ancre dans un stockage WORM (S3 Object Lock).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

from .db import Database

HASHED = ("n", "date_simulee", "acteur", "couche", "action", "objet", "detail", "niveau")


def _dossier(db: Database) -> Path:
    return Path(db.path).resolve().parent


def _cle(db: Database) -> bytes:
    if os.environ.get("HALDEN_CLE_AUDIT"):
        return os.environ["HALDEN_CLE_AUDIT"].encode()
    f = _dossier(db) / ".cle_audit"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(secrets.token_hex(32), encoding="utf-8")
    return f.read_text(encoding="utf-8").strip().encode()


def _digest(cle: bytes, prev: str, fields: dict) -> str:
    payload = json.dumps(fields, sort_keys=True, default=str, ensure_ascii=False)
    return hmac.new(cle, (prev + payload).encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _ancre(db: Database) -> Path:
    return _dossier(db) / f".ancre_audit_{Path(db.path).stem}"


def log(db: Database, today: dt.date, acteur: str, couche: str, action: str,
        objet: str = "", detail: str = "", niveau: str = "") -> dict:
    rows = db.rows("Journal_Audit")
    prev = rows[-1]["hash"] if rows else "GENESE"
    rec = {"n": len(rows) + 1, "horodatage": dt.datetime.now().replace(microsecond=0),
           "date_simulee": today, "acteur": acteur, "couche": couche, "action": action,
           "objet": objet, "detail": detail, "niveau": niveau}
    rec["hash_precedent"] = prev
    rec["hash"] = _digest(_cle(db), prev, {k: rec[k] or "" for k in HASHED})
    return db.add("Journal_Audit", rec)


def ancrer(db: Database) -> None:
    """Recopie la tête de chaîne hors du classeur (appelé à chaque sauvegarde)."""
    rows = db.rows("Journal_Audit")
    if rows:
        _ancre(db).write_text(f"{len(rows)} {rows[-1]['hash']}", encoding="utf-8")


def reinitialiser_ancre(db: Database) -> None:
    _ancre(db).unlink(missing_ok=True)


def verifier(db: Database) -> tuple[bool, int | None]:
    """Renvoie (intègre, numéro de la première ligne altérée ou manquante)."""
    cle, prev = _cle(db), "GENESE"
    rows = db.rows("Journal_Audit")
    for r in rows:
        if r["hash_precedent"] != prev or _digest(cle, prev, {k: r[k] or "" for k in HASHED}) != r["hash"]:
            return False, r["n"]
        prev = r["hash"]
    a = _ancre(db)
    if a.exists():
        n, h = a.read_text(encoding="utf-8").split()
        if len(rows) < int(n) or rows[int(n) - 1]["hash"] != h:
            return False, min(len(rows), int(n)) + (1 if len(rows) < int(n) else 0)
    return True, None
