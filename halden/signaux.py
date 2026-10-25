"""Signaux acheteurs et suspension des contacts automatiques.

Règle : dès qu'un acheteur dit « j'ai payé », parle d'avocat, se plaint ou signale une
difficulté, plus aucun message automatique ne part vers lui et un humain est alerté.
Même chose tant qu'un paiement de cet acheteur attend en file, n'est pas identifié, ou
qu'un dossier le concernant est escaladé : une seule conversation par acheteur.

Détection par règles (anglais, français, arabe), avant toute IA : reproductible et testable.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata

from . import rules
from .db import Database

SIGNAUX = {
    "PAYÉ": ["already paid", "i have paid", "i've paid", "i paid it", "i paid the", "i paid yesterday",
             "i paid today", "i paid last", "paid yesterday", "paid this morning", "already transferred",
             "i transferred", "sent the payment", "made the payment", "payment was made", "proof of payment",
             "j'ai payé", "j'ai réglé", "deja paye", "déjà payé", "déjà réglé", "virement effectué",
             "j'ai fait le virement", "دفعت", "تم الدفع", "قمت بالدفع", "حولت", "تم التحويل", "سددت"],
    "AVOCAT": ["lawyer", "attorney", "legal action", "solicitor", "court", "sue ", "avocat", "tribunal",
               "mise en demeure", "justice", "محامي", "محام", "المحكمة", "محكمة", "قضية", "إجراء قانوني"],
    "RÉCLAMATION": ["complain", "complaint", "unacceptable", "disgrace", "harass", "stop contacting",
                    "stop the reminders", "cancel the reminders", "plainte", "inadmissible", "harcèlement",
                    "arrêtez", "شكوى", "غير مقبول", "توقفوا"],
    "DIFFICULTÉ": ["lost my job", "can't pay", "cannot pay", "unable to pay", "postpone", "difficult",
                   "hardship", "medical", "hospital", "je ne peux pas payer", "difficulté", "perdu mon emploi",
                   "reporter", "étaler", "لا أستطيع الدفع", "تأجيل", "صعوبة", "فقدت عملي"],
}
TIERS = ["assistant", "on behalf of", "my husband", "my wife", "my son", "my daughter", "my father",
         "my mother", "his statement", "her statement", "send me his", "send me her", "for my client",
         "pour le compte de", "mon mari", "ma femme", "son relevé", "نيابة عن", "زوجي", "زوجتي"]


def _bas(t: str) -> str:
    return unicodedata.normalize("NFC", (t or "").lower()).replace("’", "'")


def detecter(texte: str) -> list[str]:
    t = f" {_bas(texte)} "
    return [s for s, mots in SIGNAUX.items() if any(m in t for m in mots)]


def tiers(texte: str) -> bool:
    t = f" {_bas(texte)} "
    return any(m in t for m in TIERS)


def _contact(v: str | None) -> str:
    v = (v or "").strip().lower()
    return re.sub(r"[^\d+]", "", v) if "@" not in v else v


def expediteur_verifie(acheteur: dict, message: dict) -> bool:
    """Le message vient-il du contact enregistré de l'acheteur ? (sinon : aucune donnée de compte)"""
    exp = _contact(message.get("expediteur"))
    if not exp:
        return False
    return exp in {_contact(acheteur.get("email")), _contact(acheteur.get("telephone"))}


def suspendre(db: Database, today: dt.date, acheteur_id: str, raison: str) -> None:
    a = db.get("Acheteurs", acheteur_id=acheteur_id)
    if a and not str(a.get("contact_auto") or "").startswith("SUSPENDU"):
        a["contact_auto"] = f"SUSPENDU · {raison} · {today.isoformat()}"


def suspensions(db: Database, tolerance: float | None = None) -> dict[str, str]:
    """Acheteurs à qui aucun message automatique ne doit partir, avec la raison."""
    tol = float(db.pack("tolerance_frais_bancaires_aed", 100)) if tolerance is None else tolerance
    out: dict[str, str] = {}
    for a in db.rows("Acheteurs"):
        if str(a.get("contact_auto") or "").startswith("SUSPENDU"):
            out[a["acheteur_id"]] = str(a["contact_auto"])
    for f in db.where("File_Approbation", statut="EN ATTENTE"):
        if not f["acheteur_id"] or f["acheteur_id"] == "TOUS":
            continue
        if f["action"] in ("LETTRAGE", "IDENTIFIER_ENCAISSEMENT", "ANNULER_LETTRAGE"):
            out.setdefault(f["acheteur_id"], f"paiement en validation ({f['file_id']})")
        elif f["niveau"] == rules.HUMAIN:
            out.setdefault(f["acheteur_id"], f"dossier escaladé ({f['file_id']})")
    # Un virement non identifié peut être celui de n'importe quel acheteur qui doit ce montant.
    ouvertes = [e for e in db.rows("Echeancier") if e["statut"] in ("APPELÉ", "PARTIEL", "EN RETARD")]
    for l in db.rows("Releve_Bancaire"):
        if l["statut"] not in ("INCONNU", "EN VALIDATION", "NOUVEAU") or float(l["montant_aed"] or 0) <= 0:
            continue
        if l.get("acheteur_candidat"):
            out.setdefault(l["acheteur_candidat"], f"virement {l['ligne_id']} en validation")
        m = float(l["montant_aed"])
        for e in ouvertes:
            if abs(rules.reste_du(e) - m) <= tol:
                out.setdefault(e["acheteur_id"], f"virement non identifié {l['ligne_id']} du même montant")
    return out
