"""Socle commun des agents : chaque agent lit la base et rend des propositions."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .. import audit
from ..db import Database
from ..llm import LLM
from ..proposition import Proposition


@dataclass
class Contexte:
    db: Database
    today: dt.date
    llm: LLM
    evenements: list[dict] = field(default_factory=list)
    suspendus: dict[str, str] = field(default_factory=dict)   # acheteur → raison (signaux du cycle)

    def promoteur(self, projet_id: str) -> str:
        p = self.ctx_projet(projet_id)
        return p["promoteur"] if p else "Halden"

    def ctx_projet(self, projet_id: str) -> dict | None:
        return self.db.get("Projets", projet_id=projet_id)

    def acheteur(self, acheteur_id: str) -> dict:
        return self.db.get("Acheteurs", acheteur_id=acheteur_id) or {"nom": "?", "langue": "EN", "canal": "email"}

    def unite(self, unite_id: str) -> dict | None:
        return self.db.get("Unites", unite_id=unite_id)

    def rediger(self, kind: str, langue: str, faits: dict) -> tuple[str, str, dict]:
        """Brouillon + ce que les garde-fous doivent connaître pour le contrôler."""
        objet, texte = self.llm.rediger(kind, langue, faits)
        return objet, texte, {"faits": faits, "modele_texte": self.llm.texte_fixe(kind, langue)}

    def log(self, acteur: str, action: str, objet: str = "", detail: str = "", niveau: str = "") -> None:
        audit.log(self.db, self.today, acteur, "Agents", action, objet, detail, niveau)

    def deja_fait(self, cle: str) -> bool:
        return bool(cle) and (any(r["cle"] == cle for r in self.db.rows("File_Approbation"))
                              or any(r["cle"] == cle for r in self.db.rows("Messages_Sortants")))


class Agent:
    nom = "Agent"
    etape = ""          # étape du parcours acheteur
    mission = ""

    def executer(self, ctx: Contexte) -> list[Proposition]:  # pragma: no cover - interface
        raise NotImplementedError

    def p(self, **kw) -> Proposition:
        return Proposition(agent=self.nom, **kw)
