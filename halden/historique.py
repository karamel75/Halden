"""Garde la trace de chaque cycle (pour la console) dans sorties/historique.json."""
from __future__ import annotations

import json

from . import SORTIES
from .orchestrator import Bilan

FICHIER = SORTIES / "historique.json"


def lire() -> list[dict]:
    try:
        return json.loads(FICHIER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def ajouter(b: Bilan, decisions: list[dict] | None = None) -> None:
    h = lire()
    h.append({"date": b.date.isoformat(), "imports": b.import_releve,
              "evenements": [e["label"] for e in b.evenements], "par_agent": b.par_agent,
              "decisions": decisions or []})
    SORTIES.mkdir(parents=True, exist_ok=True)
    FICHIER.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


def ajouter_decisions(decisions: list[dict]) -> None:
    h = lire()
    if h:
        h[-1]["decisions"] += decisions
        FICHIER.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


def reinitialiser() -> None:
    if FICHIER.exists():
        FICHIER.unlink()
