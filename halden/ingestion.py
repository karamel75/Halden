"""Couche 2 · Ingestion : lire les fichiers du promoteur et les ranger dans la base.

Pilote = fichiers (relevés escrow CSV, Excel d'échéanciers). Ensuite = Open Finance (AlTareq),
WhatsApp Business, e-mail. Vision = API de la DLD (Oqood, Trust Account).
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from . import audit
from .db import Database


def importer_releves(db: Database, dossier: Path | str, today: dt.date) -> list[str]:
    """Importe chaque `releve_escrow_AAAA-MM-JJ.csv` daté au plus tard aujourd'hui, une seule fois."""
    deja = {r["fichier_source"] for r in db.rows("Releve_Bancaire")}
    importes = []
    for f in sorted(Path(dossier).glob("releve_escrow_*.csv")):
        try:
            jour = dt.date.fromisoformat(f.stem.split("_")[-1])
        except ValueError:
            continue
        if jour > today or f.name in deja:
            continue
        n = 0
        with f.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                montant = float(row["credit_aed"] or 0)
                if montant <= 0:
                    continue
                db.add("Releve_Bancaire", {
                    "ligne_id": db.next_id("Releve_Bancaire", "BNK-"),
                    "date_valeur": dt.date.fromisoformat(row["date_valeur"]), "montant_aed": montant,
                    "libelle": row["libelle"], "donneur_ordre": row["donneur_ordre"],
                    "fichier_source": f.name, "statut": "NOUVEAU"})
                n += 1
        audit.log(db, today, "Ingestion", "Ingestion", "IMPORT_RELEVÉ", f.name, f"{n} crédits importés")
        importes.append(f"{f.name} ({n} lignes)")
    return importes
