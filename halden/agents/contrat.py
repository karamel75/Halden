"""Agent 2 · Contrat : suivre SPA, enregistrement Oqood et pièces KYC.

Étape du parcours : contrat et enregistrement au registre (DLD).
L'agent collecte et relance ; la validation des pièces et la signature restent humaines.
"""
from __future__ import annotations

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte

PIECES = {"kyc_passeport": "passport copy", "kyc_emirates_id": "Emirates ID (or visa page)",
          "kyc_justif_adresse": "proof of address"}


class AgentContrat(Agent):
    nom = "Contrat"
    etape = "2 · Contrat et registre"
    mission = "Relancer la signature du SPA, préparer le dossier Oqood, collecter les pièces KYC."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        db, out = ctx.db, []
        d_spa = int(db.pack("delai_signature_spa_jours", 30))
        d_oqood = int(db.pack("delai_enregistrement_oqood_jours", 30))
        for c in db.rows("Contrats"):
            a, u = ctx.acheteur(c["acheteur_id"]), ctx.unite(c["unite_id"])
            projet = ctx.ctx_projet(u["projet_id"])
            if c["spa_statut"] == "ENVOYÉ" and (ctx.today - c["date_reservation"]).days > d_spa:
                objet, texte = ctx.llm.rediger("relance_spa", a["langue"], {
                    "nom": a["nom"], "unite": u["unite_id"], "date": c["date_reservation"],
                    "promoteur": projet["promoteur"]})
                out.append(self.p(tache_id="T17", action="MESSAGE", acheteur_id=a["acheteur_id"],
                                  unite_id=u["unite_id"], canal=a["canal"], langue=a["langue"], objet=objet,
                                  brouillon=texte, engage_promoteur=True,
                                  resume=f"SPA non signé depuis {(ctx.today - c['date_reservation']).days} j · {a['nom']}",
                                  cle=f"SPA:{c['contrat_id']}"))
            if (c["spa_statut"] == "SIGNÉ" and c["oqood_statut"] == "EN ATTENTE" and c["date_spa"]
                    and (ctx.today - c["date_spa"]).days > d_oqood):
                frais = rules.montant_echeance(u["prix_aed"], float(db.pack("frais_oqood_pct", 4)))
                out.append(self.p(tache_id="T13", action="ESCALADE", acheteur_id=a["acheteur_id"],
                                  unite_id=u["unite_id"], engage_promoteur=True, montants_regles=[frais, u["prix_aed"]],
                                  resume=f"Oqood non enregistré · {u['unite_id']} · dossier prêt à soumettre à la DLD",
                                  brouillon=f"SPA signé le {c['date_spa']}, Oqood toujours en attente "
                                            f"({(ctx.today - c['date_spa']).days} j). Dossier préparé : SPA signé, "
                                            f"pièces KYC, échéancier. Frais DLD indicatifs (pack pays, à vérifier) : "
                                            f"{rules.fmt_aed(frais)}. Soumission par l'équipe juridique.",
                                  cle=f"OQOOD:{c['contrat_id']}"))
            manquantes = [lib for k, lib in PIECES.items() if str(a.get(k) or "").upper() != "OK"]
            if manquantes:
                objet, texte = ctx.llm.rediger("demande_kyc", a["langue"], {
                    "nom": a["nom"], "unite": u["unite_id"], "pieces": ", ".join(manquantes),
                    "promoteur": projet["promoteur"]})
                out.append(self.p(tache_id="T16", action="MESSAGE", acheteur_id=a["acheteur_id"],
                                  unite_id=u["unite_id"], canal=a["canal"], langue=a["langue"], objet=objet,
                                  brouillon=texte, resume=f"Pièces KYC manquantes · {a['nom']} : {', '.join(manquantes)}",
                                  cle=f"KYC:{a['acheteur_id']}:{len(manquantes)}"))
        return out
