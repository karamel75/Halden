"""Banc d'essai : 200 lignes de relevé et 100 messages piégés, avec le taux d'erreurs.

    python tools/banc_essai.py

Limite connue : ce jeu est généré par l'équipe, comme la démo. Il mesure la prudence du
moteur sur des pièges connus ; seul un vrai relevé anonymisé dira le taux réel.
Mesures :
- faux rapprochements automatiques (le chiffre qui doit rester à 0) ;
- part rapprochée sans humain ;
- signaux acheteurs détectés (payé, avocat, réclamation, difficulté) et faux signaux.
"""
from __future__ import annotations

import datetime as dt
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from halden import rules, seed, signaux  # noqa: E402
from halden.db import Database  # noqa: E402

RNG = random.Random(4242)


def lignes(db: Database, n: int = 200) -> list[tuple[dict, str | None, bool]]:
    """(ligne, échéance attendue, rapprochement automatique acceptable ?)"""
    ech = [e for e in db.rows("Echeancier") if e["statut"] in rules.OUVERTS]
    ach = {a["acheteur_id"]: a for a in db.rows("Acheteurs")}
    out = []
    for i in range(n):
        e = RNG.choice(ech)
        nom = ach[e["acheteur_id"]]["nom"]
        autre = RNG.choice([a for a in ach.values() if a["acheteur_id"] != e["acheteur_id"]])["nom"]
        ref, du = e["reference"], rules.reste_du(e)
        u, num = e["unite_id"], int(e["num"])
        cas = RNG.choice(["exact", "exact_compact", "unit_inst", "frais", "partiel", "autre_payeur",
                          "sans_ref", "sans_ref_inverse", "typo_nom", "inconnu", "deja_paye", "societe"])
        attendu, auto_ok = e["echeance_id"], False
        if cas == "exact":
            lib, don, m, auto_ok = f"TRF/{ref}", nom.upper(), du, True
        elif cas == "exact_compact":
            lib, don, m, auto_ok = ref.replace("-", ""), nom.upper(), du, True
        elif cas == "unit_inst":
            lib, don, m, auto_ok = f"unit {u} instalment {num}", nom.upper(), du, True
        elif cas == "frais":
            lib, don, m = ref, nom.upper(), du - RNG.choice([25, 35, 50, 75])
        elif cas == "partiel":
            lib, don, m = f"PART {ref}", nom.upper(), round(du * RNG.uniform(0.2, 0.8), 2)
        elif cas == "autre_payeur":
            lib, don, m = f"TRF/{ref}", autre.upper(), du
        elif cas == "sans_ref":
            lib, don, m = "INWARD REMITTANCE", nom.upper(), du
        elif cas == "sans_ref_inverse":
            lib, don, m = "TT", " ".join(reversed(nom.upper().split())), du
        elif cas == "typo_nom":
            n2 = list(nom.upper())
            n2[RNG.randrange(len(n2))] = "X"
            lib, don, m, auto_ok = f"IPI {ref}", "".join(n2), du, True
        elif cas == "inconnu":
            lib, don, m, attendu = "INWARD TT", "GLOBAL TRADING LLC", round(RNG.uniform(10_000, 400_000), 2), None
        elif cas == "deja_paye":
            payee = RNG.choice([x for x in db.rows("Echeancier") if x["statut"] == "PAYÉ"])
            lib, don, m, attendu = f"TRF {payee['reference']}", nom.upper(), payee["montant_aed"], payee["echeance_id"]
        else:
            lib, don, m = ref, f"{nom.split()[-1].upper()} HOLDINGS FZE", du
        out.append(({"ligne_id": f"T{i:03d}", "date_valeur": dt.date(2026, 12, 1), "montant_aed": m,
                     "libelle": lib, "donneur_ordre": don}, attendu, auto_ok, cas))
    return out


MESSAGES = [
    ("I already paid yesterday, why the reminder?", {"PAYÉ"}), ("I've paid it this morning, receipt attached", {"PAYÉ"}),
    ("دفعت القسط أمس", {"PAYÉ"}), ("تم التحويل يوم الأحد", {"PAYÉ"}), ("J'ai déjà payé la semaine dernière", {"PAYÉ"}),
    ("I transferred the full amount on Monday", {"PAYÉ"}), ("My lawyer will contact you", {"AVOCAT"}),
    ("Please cancel the reminders, I'm talking to my lawyer", {"AVOCAT", "RÉCLAMATION"}),
    ("سأرفع قضية في المحكمة", {"AVOCAT"}), ("Mon avocat vous écrira", {"AVOCAT"}),
    ("This is unacceptable, third reminder this week", {"RÉCLAMATION"}), ("أريد تقديم شكوى", {"RÉCLAMATION"}),
    ("I lost my job last month", {"DIFFICULTÉ"}), ("I cannot pay this instalment, can we postpone?", {"DIFFICULTÉ"}),
    ("لا أستطيع الدفع هذا الشهر", {"DIFFICULTÉ"}), ("Je ne peux pas payer ce mois-ci", {"DIFFICULTÉ"}),
    ("What is my balance?", set()), ("When is my next payment due?", set()), ("Can I get my statement?", set()),
    ("متى موعد التسليم؟", set()), ("Any construction update?", set()), ("I want a refund of everything I paid", set()),
    ("Can I change the kitchen finish?", set()), ("Bonjour, mon relevé svp", set()), ("Thanks for the update", set()),
]


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    db = seed.generer(tmp / "b.xlsx", tmp / "e")
    faux_auto = auto = 0
    pieges: dict[str, int] = {}
    jeu = lignes(db)
    for ligne, attendu, auto_ok, cas in jeu:
        r = rules.rapprocher(db, ligne)
        if r.automatique:
            auto += 1
            bon = auto_ok and r.echeances and r.echeances[0]["echeance_id"] == attendu
            if not bon:
                faux_auto += 1
                pieges[cas] = pieges.get(cas, 0) + 1
    msgs = (MESSAGES * 4)[:100]
    manques = sum(1 for t, s in msgs if not s <= set(signaux.detecter(t)))
    faux = sum(1 for t, s in msgs if not s and signaux.detecter(t))
    print(f"Relevé : {len(jeu)} lignes · rapprochées sans humain : {auto} ({auto / len(jeu):.0%})")
    print(f"  Faux rapprochements automatiques : {faux_auto}" + (f" · {pieges}" if pieges else ""))
    print(f"Messages : {len(msgs)} · signaux manqués : {manques} · faux signaux : {faux}")


if __name__ == "__main__":
    main()
