"""Agent 4 · Relation acquéreurs : comprendre les messages entrants et préparer les réponses.

Étape du parcours : construction et modifications (questions, actualités, demandes).
"""
from __future__ import annotations

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte

LIBELLES = {"DIFFICULTE_PAIEMENT": "Difficulté de paiement", "RECLAMATION": "Réclamation", "AUTRE": "Demande"}
FAQ = {"FAQ_ECHEANCE", "FAQ_RELEVE", "FAQ_LIVRAISON", "FAQ_CHANTIER"}


class AgentRelation(Agent):
    nom = "Relation acquéreurs"
    etape = "4 · Construction et modifications"
    mission = "Classer chaque message, répondre seul aux questions factuelles, faire valider le reste."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        out: list[Proposition] = []
        for ev in ctx.evenements:
            if ev["type"] == "JALON_CERTIFIE":
                out += self.actualite(ctx, ev["jalon"])
        for m in ctx.db.where("Messages_Entrants", statut="NOUVEAU"):
            out += self.traiter(ctx, m)
        return out

    def _faits(self, ctx: Contexte, a: dict) -> dict:
        db = ctx.db
        u = next((x for x in db.rows("Unites") if x["acheteur_id"] == a["acheteur_id"]), None)
        projet = ctx.ctx_projet(u["projet_id"]) if u else db.rows("Projets")[0]
        lignes = sorted(db.where("Echeancier", acheteur_id=a["acheteur_id"]), key=lambda e: e["num"])
        prochaine = next((e for e in lignes if e["statut"] != "PAYÉ"), None)
        paye = sum(float(e["montant_paye_aed"] or 0) for e in lignes)
        f = {"nom": a["nom"], "unite": u["unite_id"] if u else "?", "projet": projet["nom"],
             "promoteur": projet["promoteur"], "avancement": projet["avancement_pct"],
             "livraison": projet["date_livraison"].strftime("%B %Y") if projet["date_livraison"] else "?",
             "paye": rules.fmt_aed(paye), "prix": rules.fmt_aed(u["prix_aed"]) if u else "?", "montants": [paye]}
        if u:
            f["montants"].append(float(u["prix_aed"]))
        if prochaine:
            quand = (f"due by {prochaine['date_limite']}" if prochaine["date_limite"]
                     else f"payable when {prochaine['libelle']} is certified")
            f.update(num=prochaine["num"], libelle=prochaine["libelle"], ref=prochaine["reference"],
                     montant=rules.fmt_aed(rules.reste_du(prochaine)), quand=quand)
            f["montants"].append(rules.reste_du(prochaine))
        return f

    def traiter(self, ctx: Contexte, m: dict) -> list[Proposition]:
        c = ctx.llm.classer(m["texte"])
        m["categorie"], m["langue_detectee"], m["statut"] = c.categorie, c.langue, "TRAITÉ"
        a = ctx.acheteur(m["acheteur_id"])
        f = self._faits(ctx, a)
        langue = c.langue if c.langue in ("EN", "FR", "AR") else a["langue"]
        ctx.log(self.nom, "MESSAGE_CLASSÉ", m["msg_id"], f"{c.categorie} ({langue}) · {c.resume}", "AUTONOME")
        base = dict(acheteur_id=a["acheteur_id"], unite_id=f["unite"], canal=m["canal"], langue=langue,
                    montants_regles=f["montants"], cle=f"REPONSE:{m['msg_id']}")

        if c.categorie in FAQ:
            kind = {"FAQ_ECHEANCE": "faq_echeance", "FAQ_RELEVE": "faq_releve",
                    "FAQ_LIVRAISON": "faq_livraison", "FAQ_CHANTIER": "faq_chantier"}[c.categorie]
            if kind == "faq_echeance" and "num" not in f:
                kind = "faq_releve"
            objet, texte = ctx.llm.rediger(kind, langue, f)
            return [self.p(tache_id="T04", action="MESSAGE", objet=objet, brouillon=texte,
                           resume=f"Réponse FAQ ({c.categorie}) à {a['nom']}", **base)]

        if c.categorie == "MODIFICATION":
            objet, texte = ctx.llm.rediger("modification", langue, {**f, "demande": m["texte"][:120]})
            return [self.p(tache_id="T08", action="MESSAGE", objet=objet, brouillon=texte, engage_promoteur=True,
                           resume=f"Demande de modification de {a['nom']} : accusé + étude de faisabilité", **base)]

        attente = ctx.llm.rediger("attente_humaine", langue, f)
        accuse = self.p(tache_id="T04", action="MESSAGE", objet=attente[0], brouillon=attente[1],
                        resume=f"Accusé de réception d'attente à {a['nom']} (sans engagement)",
                        **{**base, "cle": f"ATTENTE:{m['msg_id']}"})
        if c.categorie == "ANNULATION_REMBOURSEMENT":
            # L'agent traduit fidèlement la demande en action… que les garde-fous bloquent.
            return [accuse, self.p(tache_id="T13", action="REMBOURSEMENT", acheteur_id=a["acheteur_id"],
                                   unite_id=f["unite"], engage_promoteur=True,
                                   resume=f"{a['nom']} demande annulation et remboursement",
                                   brouillon=f"Message reçu : « {m['texte']} »", cle=f"DEMANDE:{m['msg_id']}")]
        lignes = sorted(ctx.db.where("Echeancier", acheteur_id=a["acheteur_id"]), key=lambda e: e["num"])
        prochaine = next((e for e in lignes if e["statut"] != "PAYÉ"), None)
        tache = "T12" if c.categorie == "DIFFICULTE_PAIEMENT" else "T14"
        return [accuse, self.p(tache_id=tache, action="ESCALADE", acheteur_id=a["acheteur_id"], unite_id=f["unite"],
                               engage_promoteur=True,
                               resume=f"{LIBELLES.get(c.categorie, c.categorie)} · {a['nom']} : décision humaine",
                               montant=rules.reste_du(prochaine) if prochaine else None,
                               brouillon=f"Message reçu : « {m['texte']} »\n\nSynthèse : {c.resume}. "
                                         f"Payé à date : {f['paye']} sur {f['prix']}.",
                               montants_regles=f["montants"], cle=f"DEMANDE:{m['msg_id']}")]

    def actualite(self, ctx: Contexte, jalon: dict) -> list[Proposition]:
        projet = ctx.ctx_projet(jalon["projet_id"])
        objet, texte = ctx.llm.rediger("actualite", "EN", {
            "projet": projet["nom"], "jalon": jalon["libelle"], "certificat": jalon["certificat_ref"],
            "date": jalon["date_certificat"], "niveau": 8, "promoteur": projet["promoteur"],
            "livraison": projet["date_livraison"].strftime("%B %Y")})
        n = len({u["acheteur_id"] for u in ctx.db.where("Unites", projet_id=projet["projet_id"]) if u["acheteur_id"]})
        return [self.p(tache_id="T07", action="MESSAGE", acheteur_id="TOUS", canal="email", objet=objet,
                       brouillon=texte, resume=f"Actualité chantier {projet['nom']} pour {n} acquéreurs",
                       payload={"diffusion": projet["projet_id"]}, cle=f"ACTU:{jalon['jalon_id']}")]
