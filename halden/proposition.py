"""Ce qu'un agent rend : une proposition d'action, jamais l'action elle-même."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Proposition:
    agent: str                      # ex. "Collections"
    tache_id: str                   # renvoie à la Grille_Decision
    action: str                     # APPEL_DE_FONDS, MESSAGE, LETTRAGE, ESCALADE, ...
    resume: str                     # une phrase lisible par le CFO
    acheteur_id: str | None = None
    unite_id: str | None = None
    brouillon: str = ""             # texte préparé (message, note)
    montants_regles: list[float] = field(default_factory=list)  # montants calculés par les règles
    engage_promoteur: bool = False  # engage le promoteur (argent ou juridique) ?
    canal: str | None = None
    objet: str | None = None        # objet du message
    langue: str = "EN"
    payload: dict[str, Any] = field(default_factory=dict)
    montant: float | None = None    # montant affiché au CFO (sinon le premier des montants_regles)
    cle: str = ""                   # clé de dédoublonnage (une même proposition n'est pas refaite)
    # Rempli par les garde-fous :
    niveau: str = ""
    raisons: list[str] = field(default_factory=list)
