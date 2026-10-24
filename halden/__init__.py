"""Halden · POC du moteur agentique pour promoteurs off-plan (Dubaï).

Every promise, carried through.
"""
from pathlib import Path

__version__ = "0.1.0"

RACINE = Path(__file__).resolve().parent.parent
BASE = RACINE / "donnees" / "halden_base.xlsx"
ENTREES = RACINE / "donnees" / "entrees"
SORTIES = RACINE / "sorties"
LOGO_PNG = RACINE / "docs" / "assets" / "halden-logo-nuit.png"
