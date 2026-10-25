"""Agent 6 · Garantie : instruire les réclamations après livraison.

Étape du parcours : garantie. La règle dit quelle garantie s'applique ; un litige va à un humain.
"""
from __future__ import annotations

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte

LITIGE = ("lawyer", "avocat", "legal action", "court", "tribunal", "compensation", "dédommagement")


class AgentGarantie(Agent):
    nom = "Garantie"
    etape = "6 · Garantie"
    mission = "Appliquer la bonne garantie, accuser réception, missionner l'intervenant, escalader les litiges."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        db, out = ctx.db, []
        for g in db.where("Garantie", statut="NOUVEAU"):
            a, u = ctx.acheteur(g["acheteur_id"]), ctx.unite(g["unite_id"])
            projet = ctx.ctx_projet(u["projet_id"])
            cat = rules.categoriser(g["description"])
            garantie, couverte = rules.garantie_applicable(db, cat, u["date_livraison"], ctx.today)
            g.update(categorie=cat, garantie_applicable=garantie, couverte="OUI" if couverte else "NON", statut="INSTRUITE")
            ctx.log(self.nom, "GARANTIE_APPLICABLE", g["reclamation_id"],
                    f"{cat} · {garantie} · livré le {u['date_livraison']} → {'couverte' if couverte else 'hors garantie'}",
                    "RÈGLE")
            st = next((s for s in db.rows("Sous_Traitants")
                       if s["specialite"].lower().startswith(cat[:5])), db.rows("Sous_Traitants")[0])
            f = {"nom": a["nom"], "ref": g["reclamation_id"], "demande": g["description"][:90], "garantie": garantie,
                 "sous_traitant": st["nom"], "sla": 5, "livraison": u["date_livraison"],
                 "promoteur": projet["promoteur"]}
            base = dict(acheteur_id=a["acheteur_id"], unite_id=u["unite_id"], cle=f"GARANTIE:{g['reclamation_id']}")
            if cat == "structure" or any(m in g["description"].lower() for m in LITIGE):
                out.append(self.p(tache_id="T14", action="ESCALADE", engage_promoteur=True,
                                  resume=f"Réclamation sensible ({cat}) · {a['nom']} · {u['unite_id']}",
                                  brouillon=f"Réclamation : « {g['description']} »\nGarantie applicable (règle) : "
                                            f"{garantie} ({'couverte' if couverte else 'hors délai'}). "
                                            f"Expertise et position juridique à décider par l'équipe.", **base))
            elif couverte:
                objet, texte, meta = ctx.rediger("accuse_garantie", a["langue"], f)
                out.append(self.p(tache_id="T18", action="MESSAGE", canal=a["canal"], langue=a["langue"], objet=objet,
                                  brouillon=texte, resume=f"Garantie couverte · {a['nom']} · {cat} → {st['nom']}", **base, **meta))
            else:
                objet, texte, meta = ctx.rediger("refus_garantie", a["langue"], f)
                out.append(self.p(tache_id="T18", action="MESSAGE", canal=a["canal"], langue=a["langue"], objet=objet,
                                  brouillon=texte, engage_promoteur=True,
                                  resume=f"Hors garantie · {a['nom']} · {cat} : réponse à valider", **base, **meta))
        return out
