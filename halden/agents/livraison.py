"""Agent 5 · Livraison et réserves : trier les réserves (snags) et sécuriser la remise des clés.

Étape du parcours : livraison. Règle : pas de remise des clés tant qu'un solde reste dû.
"""
from __future__ import annotations

import datetime as dt

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte

SPECIALITE = {"plomberie": "Plomberie", "électricité": "Électricité", "climatisation": "Climatisation",
              "menuiserie": "Menuiserie", "finitions": "Finitions", "autre": "Finitions"}


class AgentLivraison(Agent):
    nom = "Livraison & réserves"
    etape = "5 · Livraison et réserves"
    mission = "Classer chaque réserve, l'affecter au bon sous-traitant avec un délai, bloquer les remises de clés impayées."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        db, out = ctx.db, []
        for r in db.where("Reserves", statut="NOUVEAU"):
            cat = rules.categoriser(r["description"], rules.CATEGORIES_RESERVES)
            grav = rules.gravite_reserve(r["description"])
            st = next((s for s in db.rows("Sous_Traitants") if s["specialite"] == SPECIALITE[cat]), None)
            sla = ctx.today + dt.timedelta(days=rules.SLA_JOURS[grav])
            r.update(categorie=cat, gravite=grav)
            objet, texte, meta = ctx.rediger("ordre_reserve", "FR", {
                "ref": r["reserve_id"], "unite": r["unite_id"], "sous_traitant": st["nom"] if st else "?",
                "description": r["description"], "localisation": r["localisation"], "gravite": grav, "sla": sla})
            out.append(self.p(tache_id="T03", action="ORDRE_RESERVE", unite_id=r["unite_id"], canal="email",
                              langue="FR", objet=objet, brouillon=texte,
                              resume=f"Réserve {r['reserve_id']} ({cat}, {grav}) → {st['nom'] if st else '?'} avant le {sla}",
                              payload={"reserve_id": r["reserve_id"], "st": st["st_id"] if st else None,
                                       "sla": sla.isoformat()},
                              cle=f"RESERVE:{r['reserve_id']}", **meta))
        for u in db.where("Unites", statut="PRÊTE · SOLDE DÛ"):
            du = sum(rules.reste_du(e) for e in db.where("Echeancier", unite_id=u["unite_id"]) if e["statut"] != "PAYÉ")
            cle = f"BLOCAGE:{u['unite_id']}:{du:.0f}"
            if du > 0 and not any(j["objet"] == cle for j in db.rows("Journal_Audit")):
                ctx.log(self.nom, "REMISE_CLÉS_BLOQUÉE", cle,
                        f"Lot {u['unite_id']} prêt mais {rules.fmt_aed(du)} restent dus : remise des clés bloquée (règle).",
                        "RÈGLE")
        return out
