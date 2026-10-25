"""Agent 3 · Encaissements (le pilote) : appels de fonds, rapprochement bancaire, relances.

Étape du parcours : paiements échelonnés pendant la construction.

Règles de contact (revue du 24 octobre 2026) :
- un seul message par acheteur et par cycle, qui regroupe toutes ses échéances en retard ;
- aucune relance tant qu'un paiement de cet acheteur attend en file ou n'est pas identifié,
  qu'il a écrit « j'ai payé », parlé d'avocat, de réclamation ou de difficulté, ou qu'un
  dossier le concernant est escaladé ;
- dès qu'une échéance atteint J+30, tout ce qui concerne l'acheteur passe à un humain.
"""
from __future__ import annotations

import datetime as dt

from .. import rules, signaux
from ..proposition import Proposition
from .base import Agent, Contexte

LIGNE_DETAIL = {
    "EN": "• Unit {unite} · instalment {num} · {reste} · due {date_limite} · ref {ref}",
    "FR": "• Lot {unite} · échéance n°{num} · {reste} · échue le {date_limite} · réf. {ref}",
    "AR": "• الوحدة {unite} · القسط {num} · {reste} · تاريخ الاستحقاق {date_limite} · المرجع {ref}",
}
REJET = ("RETURN", "REJECT", "REVERSAL", "RECALL", "UNPAID", "R-TRF")


class AgentCollections(Agent):
    nom = "Encaissements"
    etape = "3 · Paiements échelonnés"
    mission = ("Préparer les appels de fonds, rapprocher les virements, préparer une relance par acheteur "
               "(toujours validée), escalader à J+30 avec la procédure de défaut DLD.")

    def executer(self, ctx: Contexte) -> list[Proposition]:
        out: list[Proposition] = []
        for ev in ctx.evenements:
            if ev["type"] == "JALON_CERTIFIE":
                out += self.appels_de_fonds(ctx, ev["jalon"])
            elif ev["type"] == "LIGNE_BANCAIRE":
                ligne = ev["ligne"]
                out += self.debit(ctx, ligne) if ligne.get("sens") == "DÉBIT" else self.rapprocher(ctx, ligne)
        out += self.relances(ctx, out)
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
            objet, texte, meta = ctx.rediger("appel_de_fonds", a["langue"], {
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
                cle=f"APPEL:{e['echeance_id']}", **meta))
        return out

    # 2. Ligne de relevé escrow (crédit) → rapprochement
    def rapprocher(self, ctx: Contexte, ligne: dict) -> list[Proposition]:
        r = rules.rapprocher(ctx.db, ligne)
        ligne["score"], ligne["methode"], ligne["acheteur_candidat"] = r.score, r.methode, r.acheteur_id
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
        if r.automatique:   # référence + payeur + montant exacts : seule voie sans humain
            ligne["statut"] = "EN COURS"
            return [self.p(tache_id="T15", action="LETTRAGE",
                           resume=f"Lettrage exact {ligne['ligne_id']} → {cible} ({rules.fmt_aed(montant)})", **base)]
        if r.methode == "INCONNU":
            ligne["statut"] = "INCONNU"
            return [self.p(tache_id="T06", action="IDENTIFIER_ENCAISSEMENT",
                           resume=f"Encaissement non identifié {rules.fmt_aed(montant)} de « {ligne['donneur_ordre']} »",
                           **base)]
        ligne["statut"] = "EN VALIDATION"
        libelle = {"REF_AUTRE_PAYEUR": "la référence appartient à un autre acheteur",
                   "REF_FRAIS_BANCAIRES": "écart de frais bancaires", "REF_DEJA_PAYEE": "référence déjà soldée",
                   "REF_MONTANT_DIFFERENT": "montant différent du dû"}.get(r.methode, r.methode)
        return [self.p(tache_id="T06", action="LETTRAGE",
                       resume=f"À confirmer · {ligne['ligne_id']} → {cible} · {libelle} (indice de tri {r.score:.2f})",
                       **base)]

    # 2 bis. Ligne de relevé (débit) → frais, ou virement rejeté à défaire
    def debit(self, ctx: Contexte, ligne: dict) -> list[Proposition]:
        db = ctx.db
        montant = round(float(ligne["montant_aed"]), 2)
        texte = f"{ligne.get('libelle') or ''}".upper()
        if not any(m in texte for m in REJET):
            ligne.update(statut="FRAIS / AUTRE DÉBIT", methode="DÉBIT")
            ctx.log(self.nom, "DÉBIT_NON_LIÉ", ligne["ligne_id"], f"{rules.fmt_aed(montant)} · {ligne['libelle']}", "RÈGLE")
            return []
        ref = rules.trouver_reference(texte, [p["projet_id"] for p in db.rows("Projets")])
        credits = [l for l in db.rows("Releve_Bancaire")
                   if l.get("sens") != "DÉBIT" and l["ligne_id"] != ligne["ligne_id"]
                   and abs(float(l["montant_aed"]) - montant) < 0.01 and l["statut"] not in ("REJETÉ",)]
        if ref:
            credits = [l for l in credits if ref in rules.reference_de(l, db)] or credits
        origine = credits[-1] if credits else None
        ligne.update(statut="EN VALIDATION", methode="VIREMENT_REJETÉ")
        e = db.get("Echeancier", reference=ref) if ref else None
        ligne["acheteur_candidat"] = e["acheteur_id"] if e else None
        return [self.p(
            tache_id="T06", action="ANNULER_LETTRAGE", acheteur_id=ligne["acheteur_candidat"],
            unite_id=e["unite_id"] if e else None, engage_promoteur=True, montants_regles=[montant],
            resume=f"Virement rejeté {ligne['ligne_id']} ({rules.fmt_aed(montant)}) · "
                   f"{'défaire ' + origine['ligne_id'] if origine else 'crédit d’origine introuvable'}"
                   f"{' → ' + e['echeance_id'] + ' redevient due' if e else ''}",
            brouillon=f"Débit du {ligne['date_valeur']} : « {ligne['libelle']} ». Crédit d'origine : "
                      f"{origine['ligne_id'] + ' du ' + str(origine['date_valeur']) if origine else 'à retrouver'}. "
                      f"Proposition : remettre l'échéance en impayé et ne pas relancer avant d'avoir parlé à "
                      f"l'acheteur.",
            payload={"ligne_id": ligne["ligne_id"], "origine": origine["ligne_id"] if origine else None},
            cle=f"REJET:{ligne['ligne_id']}")]

    # 3. Minuteries J+3 / J+10 / J+30 : une seule conversation par acheteur et par cycle
    def relances(self, ctx: Contexte, deja: list[Proposition]) -> list[Proposition]:
        db, out = ctx.db, []
        bloques = dict(signaux.suspensions(db))
        for p in deja:   # ce que ce cycle vient de mettre en file compte aussi
            if p.acheteur_id and p.action in ("LETTRAGE", "IDENTIFIER_ENCAISSEMENT", "ANNULER_LETTRAGE") \
                    and p.tache_id != "T15":
                bloques.setdefault(p.acheteur_id, f"paiement en validation ({p.cle})")
        bloques.update(ctx.suspendus)
        ciblees = {eid for p in deja if p.action == "LETTRAGE" for eid in p.payload.get("echeances", [])}

        par_acheteur: dict[str, list[tuple[dict, int, str]]] = {}
        for e in db.rows("Echeancier"):
            if e["statut"] not in rules.OUVERTS or not e["date_limite"] or e["echeance_id"] in ciblees:
                continue
            retard = rules.jours_retard(e, ctx.today)
            niveau = rules.niveau_relance(db, retard)
            if not niveau:
                continue
            e["statut"] = "EN RETARD" if e["statut"] == "APPELÉ" else e["statut"]
            par_acheteur.setdefault(e["acheteur_id"], []).append((e, retard, niveau))

        for aid, lignes in par_acheteur.items():
            lignes.sort(key=lambda x: -x[1])
            e0, retard0, niveau0 = lignes[0]
            a, projet = ctx.acheteur(aid), ctx.ctx_projet(e0["projet_id"])
            faites = {(r["echeance_id"], r["niveau"]) for r in db.rows("Relances")}
            reste = round(sum(rules.reste_du(e) for e, _, _ in lignes), 2)
            montants = [reste] + [rules.reste_du(e) for e, _, _ in lignes] + [float(e["montant_aed"]) for e, _, _ in lignes]
            ids = [e["echeance_id"] for e, _, _ in lignes]

            if niveau0 == "J+30":
                fx = {"nom": a["nom"], "unite": e0["unite_id"], "num": e0["num"], "reste": rules.fmt_aed(reste),
                      "date_limite": e0["date_limite"].isoformat(), "retard": retard0,
                      "relances": ", ".join(sorted({n for (i, n) in faites if i in ids})) or "aucune",
                      "procedure": rules.procedure_defaut(db, projet["avancement_pct"])}
                objet, note = ctx.llm.rediger("escalade", "FR", fx)
                if aid in bloques:
                    note += f"\n\nContact automatique déjà suspendu : {bloques[aid]}."
                out.append(self.p(
                    tache_id="T12", action="ESCALADE", acheteur_id=aid, unite_id=e0["unite_id"],
                    resume=f"J+{retard0} · {a['nom']} · {len(lignes)} échéance(s) · {rules.fmt_aed(reste)} : "
                           f"décision humaine (procédure de défaut DLD possible)",
                    brouillon=note, objet=objet, montants_regles=montants, engage_promoteur=True,
                    payload={"echeances": ids, "niveau": "J+30", "retard": retard0},
                    cle=f"ESCALADE:{aid}:{e0['echeance_id']}"))
                signaux.suspendre(db, ctx.today, aid, f"escalade J+30 ({e0['echeance_id']})")
                continue

            if aid in bloques:
                ctx.log(self.nom, "RELANCE_SUSPENDUE", aid, f"{a['nom']} · {', '.join(ids)} · {bloques[aid]}", "RÈGLE")
                continue
            if all((e["echeance_id"], niveau0) in faites for e, _, _ in lignes):
                continue
            langue = a["langue"] if a["langue"] in LIGNE_DETAIL else "EN"
            detail = "\n".join(LIGNE_DETAIL[langue].format(
                unite=e["unite_id"], num=e["num"], reste=rules.fmt_aed(rules.reste_du(e)),
                date_limite=e["date_limite"].isoformat(), ref=e["reference"]) for e, _, _ in lignes)
            fx = {"nom": a["nom"], "detail": detail, "reste": rules.fmt_aed(reste), "ref": e0["reference"],
                  "promoteur": projet["promoteur"], "retard": retard0}
            objet, texte, meta = ctx.rediger(f"relance_{niveau0}", langue, fx)
            meta["faits"] = {**fx, "lignes": [(e["num"], e["date_limite"], e["unite_id"], e["reference"])
                                              for e, _, _ in lignes]}
            out.append(self.p(
                tache_id="T01", action="MESSAGE", acheteur_id=aid, unite_id=e0["unite_id"],
                resume=f"Relance {niveau0} · {a['nom']} · {len(lignes)} échéance(s) · {rules.fmt_aed(reste)} "
                       f"({retard0} j de retard)",
                brouillon=texte, objet=objet, canal=a["canal"], langue=langue, montants_regles=montants,
                payload={"relances": [{"echeance_id": e["echeance_id"], "niveau": niveau0, "retard": r}
                                      for e, r, _ in lignes]},
                cle=f"RELANCE:{aid}:{e0['echeance_id']}:{niveau0}", **meta))
        return out
