"""Agent 3 · Collections (le pilote) : appels de fonds, rapprochement bancaire, relances.

Étape du parcours : paiements échelonnés pendant la construction.
"""
from __future__ import annotations

import datetime as dt

from .. import rules
from ..proposition import Proposition
from .base import Agent, Contexte


class AgentCollections(Agent):
    nom = "Collections"
    etape = "3 · Paiements échelonnés"
    mission = "Préparer les appels de fonds, lettrer les virements, relancer à J+3/J+10, escalader à J+30."

    def executer(self, ctx: Contexte) -> list[Proposition]:
        out: list[Proposition] = []
        for ev in ctx.evenements:
            if ev["type"] == "JALON_CERTIFIE":
                out += self.appels_de_fonds(ctx, ev["jalon"])
            elif ev["type"] == "LIGNE_BANCAIRE":
                out += self.rapprocher(ctx, ev["ligne"])
        # Une échéance en cours de lettrage dans ce cycle n'est pas relancée.
        ciblees = {eid for p in out if p.action == "LETTRAGE" for eid in p.payload.get("echeances", [])}
        out += self.relances(ctx, ciblees)
        return out

    # 1. Jalon certifié → appels de fonds (montants calculés par les règles)
    def appels_de_fonds(self, ctx: Contexte, jalon: dict) -> list[Proposition]:
        db, out = ctx.db, []
        projet = ctx.ctx_projet(jalon["projet_id"])
        delai = int(db.pack("delai_paiement_appel_jours", 30))
        date_limite = ctx.today + dt.timedelta(days=delai)
        for e in db.where("Echeancier", declencheur=f"JALON:{jalon['jalon_id']}", statut="À VENIR"):
            u, a = ctx.unite(e["unite_id"]), ctx.acheteur(e["acheteur_id"])
            montant = rules.montant_echeance(u["prix_aed"], e["pourcentage"])
            ok = abs(montant - float(e["montant_aed"])) < 0.01
            objet, texte = ctx.llm.rediger("appel_de_fonds", a["langue"], {
                "nom": a["nom"], "projet": projet["nom"], "jalon": jalon["libelle"],
                "certificat": jalon["certificat_ref"], "num": e["num"], "montant": rules.fmt_aed(montant),
                "date_limite": date_limite.isoformat(), "escrow": projet["compte_escrow"],
                "ref": e["reference"], "promoteur": projet["promoteur"], "unite": e["unite_id"]})
            out.append(self.p(
                tache_id="T05", action="APPEL_DE_FONDS", acheteur_id=e["acheteur_id"], unite_id=e["unite_id"],
                resume=f"Appel de fonds n°{e['num']} · {e['unite_id']} · {rules.fmt_aed(montant)}"
                       + ("" if ok else " · ÉCART avec l'échéancier, à vérifier"),
                brouillon=texte, objet=objet, canal=a["canal"], langue=a["langue"],
                montants_regles=[montant], engage_promoteur=True,
                payload={"echeance_id": e["echeance_id"], "date_limite": date_limite.isoformat()},
                cle=f"APPEL:{e['echeance_id']}"))
        return out

    # 2. Ligne de relevé escrow → lettrage
    def rapprocher(self, ctx: Contexte, ligne: dict) -> list[Proposition]:
        r = rules.rapprocher(ctx.db, ligne)
        ligne["score"], ligne["methode"] = r.score, r.methode
        montant = round(float(ligne["montant_aed"]), 2)
        cible = ", ".join(e["echeance_id"] for e in r.echeances) or "à identifier"
        note = ctx.llm.rediger("note_rapprochement", "FR", {
            "ligne": ligne["ligne_id"], "date": ligne["date_valeur"], "montant": rules.fmt_aed(montant),
            "donneur": ligne["donneur_ordre"], "libelle": ligne["libelle"], "explication": r.explication,
            "cible": cible})[1]
        base = dict(acheteur_id=r.acheteur_id, unite_id=r.echeances[0]["unite_id"] if r.echeances else None,
                    brouillon=note, montants_regles=[montant] + [rules.reste_du(e) for e in r.echeances],
                    payload={"ligne_id": ligne["ligne_id"], "echeances": [e["echeance_id"] for e in r.echeances]},
                    cle=f"LETTRAGE:{ligne['ligne_id']}")
        if r.methode == "REF_EXACTE":
            ligne["statut"] = "EN COURS"
            return [self.p(tache_id="T15", action="LETTRAGE",
                           resume=f"Lettrage exact {ligne['ligne_id']} → {cible} ({rules.fmt_aed(montant)})", **base)]
        if r.methode == "INCONNU":
            ligne["statut"] = "INCONNU"
            return [self.p(tache_id="T06", action="IDENTIFIER_ENCAISSEMENT",
                           resume=f"Encaissement non identifié {rules.fmt_aed(montant)} de « {ligne['donneur_ordre']} »",
                           **base)]
        ligne["statut"] = "EN VALIDATION"
        return [self.p(tache_id="T06", action="LETTRAGE",
                       resume=f"Rapprochement probable ({r.score:.0%}) {ligne['ligne_id']} → {cible} · {r.methode}",
                       **base)]

    # 3. Minuteries J+3 / J+10 / J+30
    def relances(self, ctx: Contexte, ciblees: set[str] = frozenset()) -> list[Proposition]:
        db, out = ctx.db, []
        for e in db.rows("Echeancier"):
            if (e["statut"] not in ("APPELÉ", "PARTIEL", "EN RETARD") or not e["date_limite"]
                    or e["echeance_id"] in ciblees):
                continue
            retard = rules.jours_retard(e, ctx.today)
            niveau = rules.niveau_relance(db, retard)
            if not niveau:
                continue
            e["statut"] = "EN RETARD" if e["statut"] == "APPELÉ" else e["statut"]
            deja = {r["niveau"] for r in db.where("Relances", echeance_id=e["echeance_id"])}
            if niveau in deja:
                continue
            a, u = ctx.acheteur(e["acheteur_id"]), ctx.unite(e["unite_id"])
            projet = ctx.ctx_projet(e["projet_id"])
            reste = rules.reste_du(e)
            fx = {"nom": a["nom"], "num": e["num"], "unite": e["unite_id"], "montant": rules.fmt_aed(float(e["montant_aed"])),
                  "reste": rules.fmt_aed(reste), "date_limite": e["date_limite"].isoformat(), "retard": retard,
                  "ref": e["reference"], "promoteur": projet["promoteur"],
                  "relances": ", ".join(sorted(deja)) or "aucune"}
            if niveau == "J+30":
                objet, note = ctx.llm.rediger("escalade", "FR", fx)
                out.append(self.p(
                    tache_id="T12", action="ESCALADE", acheteur_id=e["acheteur_id"], unite_id=e["unite_id"],
                    resume=f"J+{retard} · {a['nom']} · échéance n°{e['num']} · {rules.fmt_aed(reste)} impayé : décision humaine",
                    brouillon=note, objet=objet, montants_regles=[reste, float(e["montant_aed"])],
                    engage_promoteur=True,
                    payload={"echeance_id": e["echeance_id"], "niveau": niveau, "retard": retard},
                    cle=f"RELANCE:{e['echeance_id']}:{niveau}"))
            else:
                objet, texte = ctx.llm.rediger(f"relance_{niveau}", a["langue"], fx)
                out.append(self.p(
                    tache_id="T01", action="MESSAGE", acheteur_id=e["acheteur_id"], unite_id=e["unite_id"],
                    resume=f"Relance {niveau} · {a['nom']} · échéance n°{e['num']} · {rules.fmt_aed(reste)} ({retard} j de retard)",
                    brouillon=texte, objet=objet, canal=a["canal"], langue=a["langue"],
                    montants_regles=[reste, float(e["montant_aed"])],
                    payload={"relance": {"echeance_id": e["echeance_id"], "niveau": niveau, "retard": retard}},
                    cle=f"RELANCE:{e['echeance_id']}:{niveau}"))
        return out
