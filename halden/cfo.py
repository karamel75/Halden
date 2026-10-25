"""Couche 7 · Vue CFO du matin : les chiffres que le directeur financier lit en 30 secondes."""
from __future__ import annotations

import datetime as dt

from . import rules
from .db import Database


def vue(db: Database, today: dt.date) -> dict:
    ech = db.rows("Echeancier")
    ouvertes = [e for e in ech if e["statut"] in ("APPELÉ", "PARTIEL", "EN RETARD")]
    retard = [e for e in ouvertes if e["date_limite"] and e["date_limite"] < today]
    buckets = {"1-9 j": 0.0, "10-29 j": 0.0, "30 j et +": 0.0}
    for e in retard:
        j = (today - e["date_limite"]).days
        k = "30 j et +" if j >= 30 else ("10-29 j" if j >= 10 else "1-9 j")
        buckets[k] += rules.reste_du(e)
    lignes = [l for l in db.rows("Releve_Bancaire") if l.get("sens") != "DÉBIT"]   # crédits seulement
    lettrees = [l for l in lignes if l["statut"] == "LETTRÉ"]
    auto = [l for l in lignes if l["methode"] == "REF_EXACTE"]   # rapprochés sans humain, même si rejetés ensuite
    file = db.where("File_Approbation", statut="EN ATTENTE")
    acr = [e for e in ech if e["projet_id"] == "ACR"]
    return {
        "date": today,
        "appele_total": round(sum(float(e["montant_aed"]) for e in ech if e["date_appel"] and e["date_appel"] <= today), 2),
        "encaisse_total": round(sum(float(e["montant_paye_aed"] or 0) for e in ech), 2),
        "encaisse_releve": round(sum(float(l["montant_aed"]) for l in lettrees), 2),
        "a_encaisser": round(sum(rules.reste_du(e) for e in ouvertes), 2),
        "en_retard": round(sum(buckets.values()), 2),
        "nb_retard": len(retard),
        "buckets": buckets,
        "taux_auto": (len(auto) / len(lignes)) if lignes else None,
        "nb_lignes": len(lignes), "nb_auto": len(auto), "nb_lettrees": len(lettrees),
        "nb_rejetes": len([l for l in lignes if l["statut"] == "REJETÉ"]),
        "file": len(file),
        "file_validation": len([f for f in file if f["niveau"] == "VALIDATION"]),
        "file_humain": len([f for f in file if f["niveau"] == "HUMAIN"]),
        "bloques": len(db.where("File_Approbation", statut="BLOQUÉ")),
        "messages_prepares": len(db.rows("Messages_Sortants")),
        "acr_collecte_pct": (sum(float(e["montant_paye_aed"] or 0) for e in acr) /
                             sum(float(e["montant_aed"]) for e in acr) * 100) if acr else 0,
        "top_retards": sorted(({"acheteur": db.get("Acheteurs", acheteur_id=e["acheteur_id"])["nom"],
                                "unite": e["unite_id"], "reste": rules.reste_du(e),
                                "jours": (today - e["date_limite"]).days} for e in retard),
                              key=lambda x: -x["jours"])[:6],
    }


def texte(v: dict) -> str:
    f = rules.fmt_aed
    taux = f"{v['taux_auto']:.0%}" if v["taux_auto"] is not None else "—"
    rejet = f" (dont {v['nb_rejetes']} rejeté ensuite par la banque)" if v.get("nb_rejetes") else ""
    out = [
        f"VUE CFO · {v['date']}",
        f"  Encaissé (cumul)          {f(v['encaisse_total'])}",
        f"  Reste à encaisser appelé  {f(v['a_encaisser'])}",
        f"  En retard                 {f(v['en_retard'])}  ({v['nb_retard']} échéances)",
    ]
    out += [f"     · {k:<10} {f(x)}" for k, x in v["buckets"].items()]
    out += [f"  Rapprochés sans humain    {v['nb_auto']} virements sur {v['nb_lignes']} ({taux}) · référence, "
            f"payeur et montant exacts{rejet} · démo, données fictives",
            f"  File d'approbation        {v['file']} en attente ({v['file_validation']} à valider, "
            f"{v['file_humain']} décisions humaines) · {v['bloques']} bloquée(s)",
            f"  Messages préparés         {v['messages_prepares']} (mode shadow : aucun envoyé)"]
    return "\n".join(out)
