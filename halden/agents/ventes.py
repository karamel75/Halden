"""Agent 1 · Ventes : qualifier les leads et préparer les réservations.

Étape du parcours : réservation. Le prix vient de la grille du promoteur, jamais de l'agent.
"""
from __future__ import annotations

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte


class AgentVentes(Agent):
    nom = "Ventes"
    etape = "1 · Réservation"
    mission = "Scorer chaque lead, proposer le bon lot disponible, préparer le dossier de réservation."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        db, out = ctx.db, []
        dispo = db.where("Unites", statut="DISPONIBLE")
        for lead in db.rows("Leads"):
            if lead["statut"] not in ("NOUVEAU", "RÉSERVATION DEMANDÉE"):
                continue
            score, unite = rules.score_lead(lead, dispo, ctx.today)
            lead["score"] = score
            lead["unite_proposee"] = unite["unite_id"] if unite else None
            projet = ctx.ctx_projet(unite["projet_id"]) if unite else db.rows("Projets")[0]
            if lead["statut"] == "RÉSERVATION DEMANDÉE" and unite:
                acompte = rules.montant_echeance(unite["prix_aed"], 10)
                lead["statut"] = "DOSSIER PRÉPARÉ"
                out.append(self.p(
                    tache_id="T13", action="ESCALADE", unite_id=unite["unite_id"], engage_promoteur=True,
                    montants_regles=[unite["prix_aed"], acompte], montant=acompte,
                    resume=f"Réservation à signer · {lead['nom']} · {unite['unite_id']} · {rules.fmt_aed(unite['prix_aed'])}",
                    brouillon=f"Dossier de réservation préparé pour {lead['nom']} ({lead['nationalite']}).\n"
                              f"Lot {unite['unite_id']} ({unite['type']}, {unite['surface_sqft']} sq ft), prix grille "
                              f"{rules.fmt_aed(unite['prix_aed'])}, plan 60/40, acompte de réservation 10 % = "
                              f"{rules.fmt_aed(acompte)}.\nÀ faire par l'équipe : vérifier identité, faire signer le "
                              f"formulaire de réservation, encaisser l'acompte sur le compte escrow.",
                    cle=f"RESA:{lead['lead_id']}"))
                continue
            if score >= 60 and unite:
                lead["statut"] = "QUALIFIÉ"
                objet, texte, meta = ctx.rediger("suivi_lead", "EN", {
                    "nom": lead["nom"], "projet": projet["nom"], "unite": unite["unite_id"], "type": unite["type"],
                    "surface": unite["surface_sqft"], "prix": rules.fmt_aed(unite["prix_aed"]),
                    "promoteur": projet["promoteur"]})
                out.append(self.p(tache_id="T09", action="MESSAGE", canal="whatsapp", objet=objet, brouillon=texte,
                                  montants_regles=[unite["prix_aed"]], unite_id=unite["unite_id"],
                                  resume=f"Lead {lead['nom']} (score {score}) → proposer {unite['unite_id']}",
                                  payload={"lead_id": lead["lead_id"]}, cle=f"LEAD:{lead['lead_id']}", **meta))
            else:
                lead["statut"] = "À NOURRIR"
                ctx.log(self.nom, "LEAD_SCORÉ", lead["lead_id"],
                        f"Score {score} < 60 ou aucun lot compatible : mis en nurturing.", "AUTONOME")
        return out
