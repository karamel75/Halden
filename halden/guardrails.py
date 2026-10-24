"""Couche 5 · Garde-fous : chaque proposition passe ici avant toute exécution.

1. Liste noire : l'IA ne bouge jamais d'argent et ne prend aucun engagement juridique.
2. Grille de décision : niveau d'autonomie de la tâche (onglet Grille_Decision).
3. Test « argent ou juridique ? » : si oui, jamais d'exécution autonome.
4. Contrôle des montants : tout montant écrit par l'IA doit venir du moteur de règles.
5. Mode shadow : rien ne sort, tout est préparé et journalisé.
"""
from __future__ import annotations

import re

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

MONTANT_RE = re.compile(r"(?:AED|DHS?|د\.إ)\s?([\d][\d,]*(?:\.\d{1,2})?)", re.I)


def montants_dans_texte(texte: str) -> list[float]:
    return [float(m.replace(",", "")) for m in MONTANT_RE.findall(texte or "")]


def evaluer(db: Database, p: Proposition) -> Proposition:
    raisons: list[str] = []

    if p.action in ACTIONS_INTERDITES:
        p.niveau = rules.BLOQUE
        p.raisons = [f"Action interdite : {ACTIONS_INTERDITES[p.action]}."]
        return p

    niveau = rules.niveau_tache(db, p.tache_id)
    raisons.append(f"Grille de décision {p.tache_id} → {niveau}.")

    if p.engage_promoteur and niveau in (rules.AUTONOME, rules.REGLE):
        niveau = rules.VALIDATION
        raisons.append("Test « argent ou juridique ? » = oui → validation humaine obligatoire.")

    autorises = {round(x, 2) for x in p.montants_regles}
    for m in montants_dans_texte(p.brouillon):
        if round(m, 2) not in autorises:
            niveau = rules.BLOQUE
            raisons.append(f"Montant {rules.fmt_aed(m)} absent du moteur de règles : brouillon rejeté.")

    if str(db.param("mode_shadow", "OUI")).upper() == "OUI" and p.canal:
        raisons.append("Mode shadow : message préparé, non envoyé.")

    p.niveau = niveau
    p.raisons = raisons
    return p
