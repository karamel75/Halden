"""Couche 2 · Ingestion : lire les fichiers du promoteur et les ranger dans la base.

Pilote = fichiers : relevés escrow en CSV (plusieurs mises en page de banque) et MT940.
Le PDF n'est pas encore lu (à faire exporter en CSV par la banque, ou lot suivant).
Ensuite = Open Finance (AlTareq), WhatsApp Business, e-mail. Vision = API de la DLD.

Chaque mouvement est lu, crédits ET débits (un virement rejeté revient en débit), et
dédoublonné sur son contenu (date, montant, sens, libellé, donneur d'ordre), pas sur le
nom du fichier : un même relevé déposé deux fois sous deux noms n'est compté qu'une fois.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import re
from pathlib import Path

from . import audit
from .db import Database

ALIAS = {
    "date_valeur": ["date_valeur", "value date", "value_date", "valuedate", "date", "booking date", "transaction date"],
    "libelle": ["libelle", "description", "narrative", "details", "remarks", "reference", "libellé"],
    "donneur_ordre": ["donneur_ordre", "remitter", "ordering party", "payer", "sender", "counterparty", "from"],
    "credit": ["credit_aed", "credit", "cr", "deposit", "amount in", "credit amount"],
    "debit": ["debit_aed", "debit", "dr", "withdrawal", "amount out", "debit amount"],
    "montant": ["amount", "montant", "amount_aed"],
}


def montant(txt: str | None) -> float:
    """« 1,234.56 », « 1.234,56 », « 1 234,56 », « (105.00) » → nombre."""
    t = (txt or "").strip().replace("AED", "").replace(" ", "").replace(" ", "")
    if not t:
        return 0.0
    neg = t.startswith("(") and t.endswith(")") or t.startswith("-")
    t = t.strip("()-+")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?|\d+,\d{1,2}", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "")
    v = float(t)
    return -v if neg else v


def _date(txt: str) -> dt.date:
    txt = txt.strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %b %Y", "%d-%b-%Y", "%y%m%d"):
        try:
            return dt.datetime.strptime(txt, f).date()
        except ValueError:
            continue
    raise ValueError(f"date illisible : {txt}")


def _colonnes(entetes: list[str]) -> dict[str, str]:
    bas = {h.strip().lower(): h for h in entetes if h}
    return {cle: next((bas[a] for a in alias if a in bas), None) for cle, alias in ALIAS.items()}


def lire_csv(contenu: str) -> list[dict]:
    try:
        dialecte = csv.Sniffer().sniff(contenu[:2000], delimiters=",;\t|")
    except csv.Error:
        dialecte = csv.excel
    lecteur = csv.DictReader(io.StringIO(contenu), dialect=dialecte)
    col = _colonnes(lecteur.fieldnames or [])
    if not col["date_valeur"]:
        raise ValueError("colonne de date introuvable")
    out = []
    for row in lecteur:
        if not (row.get(col["date_valeur"]) or "").strip():
            continue
        if col["montant"] and not (col["credit"] or col["debit"]):
            v = montant(row.get(col["montant"]))
        else:
            v = montant(row.get(col["credit"])) - abs(montant(row.get(col["debit"])))
        if abs(v) < 0.005:
            continue
        out.append({"date_valeur": _date(row[col["date_valeur"]]), "montant": v,
                    "libelle": (row.get(col["libelle"]) or "").strip() if col["libelle"] else "",
                    "donneur_ordre": (row.get(col["donneur_ordre"]) or "").strip() if col["donneur_ordre"] else ""})
    return out


def lire_mt940(contenu: str) -> list[dict]:
    """Lecture minimale du SWIFT MT940 : lignes :61: (mouvement) et :86: (libellé)."""
    out, courant = [], None
    for ligne in contenu.splitlines():
        if ligne.startswith(":61:"):
            m = re.match(r":61:(\d{6})(\d{4})?(R?[CD])([A-Z]?)(\d+,\d*)", ligne)
            if not m:
                continue
            v = float(m.group(5).replace(",", "."))
            courant = {"date_valeur": _date(m.group(1)), "montant": v if m.group(3).endswith("C") else -v,
                       "libelle": ligne[m.end():].strip(), "donneur_ordre": ""}
            out.append(courant)
        elif ligne.startswith(":86:") and courant is not None:
            texte = ligne[4:].strip()
            courant["libelle"] = f"{courant['libelle']} {texte}".strip()
            m = re.search(r"(?:/ORDP/|ORDERING PARTY:?|FROM:?)\s*([A-Z][A-Z .'-]+)", texte.upper())
            if m:
                courant["donneur_ordre"] = m.group(1).strip()
    return out


def empreinte(m: dict) -> str:
    cle = f"{m['date_valeur']}|{m['montant']:.2f}|{m['libelle'].upper()}|{m['donneur_ordre'].upper()}"
    return hashlib.sha256(cle.encode("utf-8")).hexdigest()[:16]


def importer_releves(db: Database, dossier: Path | str, today: dt.date) -> list[str]:
    """Importe chaque `releve_escrow_AAAA-MM-JJ.(csv|sta|mt940)` daté au plus tard aujourd'hui."""
    vus = {r["empreinte"] for r in db.rows("Releve_Bancaire") if r.get("empreinte")}
    importes = []
    for f in sorted(Path(dossier).glob("releve_escrow_*.*")):
        if f.suffix.lower() not in (".csv", ".sta", ".mt940", ".txt"):
            continue
        try:
            jour = dt.date.fromisoformat(f.stem.split("_")[-1])
        except ValueError:
            continue
        if jour > today:
            continue
        contenu = f.read_text(encoding="utf-8-sig")
        try:
            mouvements = lire_mt940(contenu) if contenu.lstrip().startswith((":20:", "{1:")) else lire_csv(contenu)
        except ValueError as e:
            audit.log(db, today, "Ingestion", "Ingestion", "RELEVÉ_ILLISIBLE", f.name, str(e))
            continue
        n = doublons = 0
        for m in mouvements:
            h = empreinte(m)
            if h in vus:
                doublons += 1
                continue
            vus.add(h)
            db.add("Releve_Bancaire", {
                "ligne_id": db.next_id("Releve_Bancaire", "BNK-"), "date_valeur": m["date_valeur"],
                "montant_aed": abs(m["montant"]), "sens": "CRÉDIT" if m["montant"] > 0 else "DÉBIT",
                "libelle": m["libelle"], "donneur_ordre": m["donneur_ordre"], "fichier_source": f.name,
                "statut": "NOUVEAU", "empreinte": h})
            n += 1
        if n or doublons:
            audit.log(db, today, "Ingestion", "Ingestion", "IMPORT_RELEVÉ", f.name,
                      f"{n} mouvements importés" + (f" · {doublons} doublon(s) ignoré(s)" if doublons else ""))
        if n:
            importes.append(f"{f.name} ({n} lignes)")
    return importes
