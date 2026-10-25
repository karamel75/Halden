"""Couche 5 · Garde-fous : chaque proposition passe ici avant toute exécution.

1. Liste noire : l'IA ne bouge jamais d'argent et ne prend aucun engagement juridique.
2. Règle d'approbation du pilote : tout message vers un acheteur est validé par un humain.
   Elle est écrite ici, dans le code : aucune note de la grille Excel ne peut la lever.
3. Grille de décision : niveau d'autonomie de la tâche (onglet Grille_Decision), jamais
   plus libre que le plancher fixé dans le code (PLANCHERS).
4. Test « argent ou juridique ? » : si oui, jamais d'exécution autonome.
5. Contrôle des nombres : tout montant, pourcentage, date ou nombre écrit dans un message
   doit venir des faits calculés par le moteur de règles, quelle que soit l'écriture
   (« AED 321,000 », « 321,000 AED », « 321k », « ٣٢١٬٠٠٠ درهم », « 40 % », « 12/12/2026 »).
6. Mode shadow : rien ne sort, tout est préparé et journalisé.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any, Iterable

from . import rules
from .db import Database
from .proposition import Proposition

ACTIONS_INTERDITES = {
    "VIREMENT": "un agent ne déclenche jamais de virement",
    "REMBOURSEMENT": "un remboursement est une décision humaine, exécutée hors de Halden",
    "MODIFIER_PRIX": "le prix est fixé par le promoteur, pas par un agent",
    "ANNULER_CONTRAT": "une résiliation relève du juridique (loi Dubaï 13/2008, à vérifier par avocat)",
    "ACCORDER_DELAI": "un report d'échéance engage le promoteur : décision humaine",
}

# Règle d'approbation du pilote (décision d'équipe, 25 octobre 2026) : chaque message
# vers un acheteur est « agent + validation ». Constante de code, pas de paramètre Excel.
MESSAGES_ACHETEUR_VALIDES = True

# Plancher par tâche : la grille Excel peut rendre une tâche plus stricte, jamais plus libre.
PLANCHERS = {
    "T01": rules.VALIDATION, "T04": rules.VALIDATION, "T07": rules.VALIDATION, "T08": rules.VALIDATION,
    "T09": rules.VALIDATION, "T16": rules.VALIDATION, "T17": rules.VALIDATION, "T18": rules.VALIDATION,
    "T05": rules.VALIDATION, "T06": rules.VALIDATION, "T12": rules.HUMAIN, "T13": rules.HUMAIN,
    "T14": rules.HUMAIN,
}


# --- Extraction des nombres, quelle que soit l'écriture -----------------------------------
_CHIFFRES = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_SEP = {"٬": ",", "٫": ".", "،": ",", " ": " ", " ": " "}
MOIS = {m: i for i, noms in enumerate([
    (), ("january", "jan", "janvier", "يناير"), ("february", "feb", "février", "fevrier", "فبراير"),
    ("march", "mar", "mars", "مارس"), ("april", "apr", "avril", "أبريل", "ابريل"), ("may", "mai", "مايو"),
    ("june", "jun", "juin", "يونيو"), ("july", "jul", "juillet", "يوليو"),
    ("august", "aug", "août", "aout", "أغسطس"), ("september", "sep", "sept", "septembre", "سبتمبر"),
    ("october", "oct", "octobre", "أكتوبر"), ("november", "nov", "novembre", "نوفمبر"),
    ("december", "dec", "décembre", "decembre", "ديسمبر")]) for m in noms}
_MOIS_RE = "|".join(sorted(map(re.escape, MOIS), key=len, reverse=True))

DATE_RES = [
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), ("a", "m", "j")),
    (re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b"), ("j", "m", "a")),
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th|er)?\s+({_MOIS_RE})\.?,?\s+(\d{{4}})\b", re.I), ("j", "M", "a")),
    (re.compile(rf"\b({_MOIS_RE})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I), ("M", "j", "a")),
    (re.compile(rf"\b({_MOIS_RE})\s+(\d{{4}})\b", re.I), ("M", "a")),
]
# Identifiants (références, lots, IBAN, téléphones) : retirés avant de lire les nombres.
IDENT_RE = re.compile(r"\bAE\d{2}(?:\s?\d{4}){4,5}(?:\s?\d{1,3})?|\b[A-Z]{2,}-?\d[\w-]*|\+\d[\d\s]{7,}\d")
NOMBRE_RE = re.compile(
    r"(?<![\w.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{1,3}(?: \d{3})+(?=\s?(?:AED|DHS?|درهم|د\.إ))(?:\.\d+)?|\d+(?:[.,]\d+)?)"
    r"\s?(k|K|m|M|mn|million|millions|ألف|مليون)?(?![\w])\s?(%|٪|pc|percent)?", re.I)


def normaliser(texte: str) -> str:
    t = (texte or "").translate(_CHIFFRES)
    for a, b in _SEP.items():
        t = t.replace(a, b)
    return t


def _date_de(groupes: tuple, ordre: tuple) -> tuple:
    v = dict(zip(ordre, groupes))
    m = MOIS.get(v["M"].lower().rstrip(".")) if "M" in v else int(v["m"])
    return (int(v["a"]), m, int(v["j"])) if "j" in v else (int(v["a"]), m)


def extraire(texte: str) -> tuple[list[float], list[tuple]]:
    """Renvoie (nombres, dates) lus dans un texte, dans toute écriture."""
    t = normaliser(texte)
    dates: list[tuple] = []
    for rx, ordre in DATE_RES:
        for m in rx.finditer(t):
            try:
                dates.append(_date_de(m.groups(), ordre))
            except (ValueError, TypeError):
                continue
        t = rx.sub(" ", t)
    t = IDENT_RE.sub(" ", t)
    nombres = []
    for m in NOMBRE_RE.finditer(t):
        brut, suffixe = m.group(1), (m.group(2) or "").lower()
        if re.fullmatch(r"\d+,\d{1,2}", brut):        # virgule décimale (écriture française)
            brut = brut.replace(",", ".")
        x = float(brut.replace(",", "").replace(" ", ""))
        x *= {"k": 1e3, "ألف": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "millions": 1e6, "مليون": 1e6}.get(suffixe, 1)
        nombres.append(round(x, 2))
    return nombres, dates


def _valeurs(faits: Any) -> Iterable[Any]:
    if isinstance(faits, dict):
        for v in faits.values():
            yield from _valeurs(v)
    elif isinstance(faits, (list, tuple, set)):
        for v in faits:
            yield from _valeurs(v)
    else:
        yield faits


def autorises(p: Proposition) -> tuple[set[float], set[tuple]]:
    """Nombres et dates qu'un brouillon a le droit de contenir : ceux des faits du moteur."""
    nombres = {round(float(x), 2) for x in p.montants_regles}
    dates: set[tuple] = set()
    for v in list(_valeurs(p.faits)) + [p.modele_texte]:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            nombres.add(round(float(v), 2))
        elif isinstance(v, (dt.date, dt.datetime)):
            dates |= {(v.year, v.month, v.day), (v.year, v.month)}
            nombres |= {float(v.day), float(v.year)}
        elif v:
            n, d = extraire(str(v))
            nombres |= set(n)
            dates |= set(d) | {x[:2] for x in d}
    return nombres, dates


def controler_nombres(p: Proposition, texte: str | None = None) -> list[str]:
    """Liste des nombres ou dates du brouillon qui ne viennent pas du moteur de règles."""
    ok_n, ok_d = autorises(p)
    n, d = extraire(f"{p.objet or ''}\n{p.brouillon if texte is None else texte}")
    fautes = [f"nombre « {x:,.2f} »" for x in n if round(x, 2) not in ok_n]
    fautes += [f"date « {'-'.join(map(str, x))} »" for x in d if x not in ok_d]
    return fautes


# Rétrocompatibilité : montants précédés d'une devise.
def montants_dans_texte(texte: str) -> list[float]:
    return extraire(texte)[0]


def message_acheteur(p: Proposition) -> bool:
    return bool(p.canal) and p.acheteur_id not in (None, "") and p.action in ("MESSAGE", "APPEL_DE_FONDS")


def evaluer(db: Database, p: Proposition) -> Proposition:
    raisons: list[str] = []

    if p.action in ACTIONS_INTERDITES:
        p.niveau = rules.BLOQUE
        p.raisons = [f"Action interdite : {ACTIONS_INTERDITES[p.action]}."]
        return p

    niveau = rules.niveau_tache(db, p.tache_id)
    raisons.append(f"Grille de décision {p.tache_id} → {niveau}.")
    plancher = PLANCHERS.get(p.tache_id)
    if plancher and rules.ORDRE[plancher] > rules.ORDRE[niveau]:
        niveau = plancher
        raisons.append(f"Plancher du code pour {p.tache_id} → {plancher} (la grille Excel ne peut pas l'assouplir).")

    if MESSAGES_ACHETEUR_VALIDES and message_acheteur(p) and rules.ORDRE[niveau] < rules.ORDRE[rules.VALIDATION]:
        niveau = rules.VALIDATION
        raisons.append("Règle du pilote : tout message vers un acheteur est validé par un humain.")

    if p.engage_promoteur and niveau in (rules.AUTONOME, rules.REGLE):
        niveau = rules.VALIDATION
        raisons.append("Test « argent ou juridique ? » = oui → validation humaine obligatoire.")

    if p.canal:   # tout ce qui peut sortir est contrôlé ; les notes internes vont à un humain
        fautes = controler_nombres(p)
        if fautes:
            niveau = rules.BLOQUE
            raisons.append("Contenu absent du moteur de règles : " + ", ".join(fautes[:5]) + " → brouillon rejeté.")

    if str(db.param("mode_shadow", "OUI")).upper() == "OUI" and p.canal:
        raisons.append("Mode shadow : message préparé, non envoyé.")

    p.niveau = niveau
    p.raisons = raisons
    return p
