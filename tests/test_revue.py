"""Chaque cas relevé par la revue du 24 octobre 2026 (Jennifer El Karaki) devient un test.

    python -m unittest discover -s tests
"""
import datetime as dt
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from halden import approvals, audit, guardrails, ingestion, rules, seed, signaux
from halden.agents.base import Contexte
from halden.agents.collections import AgentCollections
from halden.db import Database
from halden.llm import LLM, masquer_texte
from halden.orchestrator import cycle
from halden.proposition import Proposition

J1, J2 = dt.date(2026, 11, 2), dt.date(2026, 11, 28)
CFO = "Sara K. · CFO"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.base, self.entrees = self.tmp / "base.xlsx", self.tmp / "entrees"
        seed.generer(self.base, self.entrees)
        self.db = Database.load(self.base)
        self.llm = LLM("simule")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def jour1(self):
        """Cycle du 2 novembre, puis le CFO approuve les appels de fonds."""
        b = cycle(self.db, J1, self.llm)
        for f in approvals.en_attente(self.db):
            if f["action"] == "APPEL_DE_FONDS":
                approvals.decider(self.db, f["file_id"], True, CFO, J1)
        return b

    def ligne(self, libelle, donneur, montant, date=J2, sens="CRÉDIT"):
        return self.db.add("Releve_Bancaire", {
            "ligne_id": self.db.next_id("Releve_Bancaire", "BNK-"), "date_valeur": date, "montant_aed": montant,
            "libelle": libelle, "donneur_ordre": donneur, "fichier_source": "test", "statut": "NOUVEAU",
            "sens": sens})

    def ech(self, aid, num):
        return next(e for e in self.db.where("Echeancier", acheteur_id=aid) if e["num"] == num)

    def nom(self, aid):
        return self.db.get("Acheteurs", acheteur_id=aid)["nom"]


class TestArgent(Base):
    def test_reference_d_un_autre_acheteur_jamais_automatique(self):
        """Omar paie avec la référence de Rashid et le montant exact que Rashid doit."""
        self.jour1()
        rashid = self.ech("ACH-007", 4)
        self.ligne(f"TRF/{rashid['reference']}", self.nom("ACH-001").upper(), rashid["montant_aed"])
        r = rules.rapprocher(self.db, self.db.rows("Releve_Bancaire")[-1])
        self.assertEqual(r.methode, "REF_AUTRE_PAYEUR")
        self.assertFalse(r.automatique)
        self.assertIn("appartient", r.explication)
        cycle(self.db, J2, self.llm)
        self.assertEqual(self.ech("ACH-007", 4)["statut"], "APPELÉ")      # Rashid n'est pas marqué payé

    def test_pas_de_relance_quand_un_paiement_attend(self):
        """Nadia paie sans référence ; le rapprochement attend le CFO ; aucune relance ne part."""
        self.jour1()
        nadia = self.ech("ACH-014", 4)
        self.ligne("INWARD REMITTANCE", "HADDAD NADIA", nadia["montant_aed"], dt.date(2026, 12, 6))
        b = cycle(self.db, dt.date(2026, 12, 12), self.llm)
        self.assertTrue(any(p.action == "LETTRAGE" and p.acheteur_id == "ACH-014" for p in b.propositions))
        self.assertFalse([p for p in b.propositions if p.acheteur_id == "ACH-014" and "relances" in p.payload])

    def test_virement_non_identifie_du_meme_montant_suspend(self):
        self.jour1()
        nadia = self.ech("ACH-014", 4)
        self.ligne("CASH DEPOSIT", "UNKNOWN", nadia["montant_aed"], dt.date(2026, 12, 6))
        b = cycle(self.db, dt.date(2026, 12, 12), self.llm)
        self.assertFalse([p for p in b.propositions if p.acheteur_id == "ACH-014" and "relances" in p.payload])

    def test_une_conversation_par_acheteur(self):
        """Arjun (difficulté signalée) ne reçoit aucune relance ; personne n'en reçoit deux dans un cycle."""
        b = cycle(self.db, J1, self.llm)
        relances = [p for p in b.propositions if "relances" in p.payload]
        self.assertFalse([p for p in relances if p.acheteur_id == "ACH-019"])
        ids = [p.acheteur_id for p in relances]
        self.assertEqual(len(ids), len(set(ids)))
        b2 = cycle(self.db, dt.date(2026, 11, 3), self.llm)
        self.assertFalse([p for p in b2.propositions if p.acheteur_id == "ACH-019" and "relances" in p.payload])

    def test_frais_bancaires_et_formats_de_reference(self):
        self.jour1()
        e = self.ech("ACH-002", 4)
        projets = ["ACR", "PLR"]
        for txt in ("HLDACR010204", "ACR-0102-04 PAYMENT", "unit ACR-0102 instalment 4", "HLD ACR 0102 04"):
            self.assertEqual(rules.trouver_reference(txt, projets), e["reference"], txt)
        self.ligne(e["reference"], self.nom("ACH-002").upper(), e["montant_aed"] - 50)
        r = rules.rapprocher(self.db, self.db.rows("Releve_Bancaire")[-1])
        self.assertEqual(r.methode, "REF_FRAIS_BANCAIRES")
        self.assertFalse(r.automatique)

    def test_virement_rejete_redevient_du(self):
        self.jour1()
        e = self.ech("ACH-002", 4)
        self.ligne(f"TRF/{e['reference']}", self.nom("ACH-002").upper(), e["montant_aed"], dt.date(2026, 11, 20))
        cycle(self.db, dt.date(2026, 11, 21), self.llm)
        self.assertEqual(self.ech("ACH-002", 4)["statut"], "PAYÉ")
        self.ligne(f"RETURNED TRF {e['reference']}", "", e["montant_aed"], dt.date(2026, 11, 23), "DÉBIT")
        cycle(self.db, dt.date(2026, 11, 23), self.llm)
        f = next(x for x in approvals.en_attente(self.db) if x["action"] == "ANNULER_LETTRAGE")
        approvals.decider(self.db, f["file_id"], True, CFO, dt.date(2026, 11, 23))
        self.assertNotEqual(self.ech("ACH-002", 4)["statut"], "PAYÉ")


class TestSignaux(Base):
    def test_detection(self):
        self.assertIn("PAYÉ", signaux.detecter("I already paid yesterday, why the reminder?"))
        self.assertIn("PAYÉ", signaux.detecter("دفعت القسط أمس، لماذا التذكير؟"))
        self.assertIn("AVOCAT", signaux.detecter("Please cancel the reminders, I'm talking to my lawyer"))
        self.assertIn("DIFFICULTÉ", signaux.detecter("I lost my job, I can't pay this month"))
        self.assertEqual(signaux.detecter("I want a refund of everything I paid"), [])
        self.assertEqual(self.llm.classer("What is my balance?").categorie, "FAQ_ECHEANCE")

    def test_signal_suspend_tout_contact(self):
        cycle(self.db, J1, self.llm)
        for aid in ("ACH-007", "ACH-004", "ACH-019"):      # payé (arabe), avocat, difficulté
            self.assertTrue(str(self.db.get("Acheteurs", acheteur_id=aid)["contact_auto"]).startswith("SUSPENDU"))
        b = cycle(self.db, dt.date(2026, 11, 15), self.llm)
        self.assertFalse([p for p in b.propositions if p.acheteur_id in ("ACH-007", "ACH-004") and "relances" in p.payload])

    def test_expediteur_non_verifie(self):
        """« Omar's assistant, send me his statement » : aucune donnée de compte ne part."""
        b = cycle(self.db, J1, self.llm)
        omar = [p for p in b.propositions if p.acheteur_id == "ACH-001" and p.agent == "Relation acquéreurs"]
        self.assertTrue(any(p.action == "ESCALADE" for p in omar))
        for p in omar:
            self.assertNotIn("AED", p.brouillon if p.canal else "")


class TestControleNombres(Base):
    def p(self, texte, montants=(321000.0,), faits=None):
        return Proposition(agent="T", tache_id="T01", action="MESSAGE", resume="x", acheteur_id="ACH-001",
                           brouillon=texte, montants_regles=list(montants), canal="email", faits=faits or {})

    def test_toutes_les_ecritures(self):
        bloque = lambda t: guardrails.evaluer(self.db, self.p(t)).niveau == rules.BLOQUE
        self.assertTrue(bloque("Please pay 312,000 AED"))
        self.assertTrue(bloque("يرجى دفع ٣١٢٬٠٠٠ درهم"))
        self.assertTrue(bloque("Please pay USD 87,000"))
        self.assertTrue(bloque("A 15% late fee applies"))
        self.assertTrue(bloque("Please pay before 15/12/2026"))
        self.assertFalse(bloque("Please pay AED 321,000.00"))
        self.assertFalse(bloque("Please pay 321,000 AED"))
        self.assertFalse(bloque("Please pay AED 321k"))
        self.assertFalse(bloque("يرجى دفع ٣٢١٬٠٠٠ درهم"))

    def test_brouillon_modifie_recontrole(self):
        cycle(self.db, J1, self.llm)
        f = next(x for x in approvals.en_attente(self.db) if x["action"] == "APPEL_DE_FONDS")
        with self.assertRaises(ValueError):
            approvals.decider(self.db, f["file_id"], True, CFO, J1, brouillon_modifie=f["brouillon"] + "\nPlease add AED 5,000 fees.")
        approvals.decider(self.db, f["file_id"], True, CFO, J1, brouillon_modifie=f["brouillon"] + "\nThank you.")

    def test_approbateur_non_autorise(self):
        cycle(self.db, J1, self.llm)
        f = approvals.en_attente(self.db)[0]
        with self.assertRaises(PermissionError):
            approvals.decider(self.db, f["file_id"], True, "Quelqu'un", J1)


class TestGrilleEtAudit(Base):
    def test_excel_ne_rend_pas_les_relances_autonomes(self):
        self.db.get("Grille_Decision", tache_id="T01").update(C2_consequence=1, C1_ambiguite=1)
        b = cycle(self.db, J1, self.llm)
        self.assertTrue(all(p.niveau == rules.VALIDATION for p in b.propositions if "relances" in p.payload))

    def test_sensibilite(self):
        self.assertIn("→", self.db.get("Grille_Decision", tache_id="T01")["sensibilite"])

    def test_chaine_signee_et_ancree(self):
        cycle(self.db, J1, self.llm)
        self.db.save()
        db = Database.load(self.base)
        self.assertEqual(audit.verifier(db), (True, None))
        # Recalculer la chaîne avec un simple SHA-256 (sans la clé) ne passe pas.
        import hashlib
        r = db.rows("Journal_Audit")[3]
        r["detail"] = "modifié"
        r["hash"] = hashlib.sha256((r["hash_precedent"] + json.dumps(r, default=str)).encode()).hexdigest()[:32]
        self.assertFalse(audit.verifier(db)[0])
        # Tronquer la fin se voit grâce à l'ancre.
        db2 = Database.load(self.base)
        del db2.tables["Journal_Audit"][-5:]
        self.assertFalse(audit.verifier(db2)[0])

    def test_procedure_defaut(self):
        self.assertIn("25 %", rules.procedure_defaut(self.db, 40))
        self.assertIn("40 %", rules.procedure_defaut(self.db, 70))
        self.assertIn("DLD", rules.procedure_defaut(self.db, 90))


class TestIngestionEtIA(Base):
    def test_csv_autre_banque_et_doublons(self):
        csv = "Value Date;Narrative;Remitter;Amount\n28/11/2026;HLDACR010204;PRIYA RAMAN;78.600,00\n" \
              "28/11/2026;BANK CHARGES;BANK;-105,00\n"
        (self.entrees / "releve_escrow_2026-11-29.csv").write_text(csv, encoding="utf-8")
        (self.entrees / "releve_escrow_2026-11-30.csv").write_text(csv, encoding="utf-8")   # même relevé, autre nom
        ingestion.importer_releves(self.db, self.entrees, dt.date(2026, 11, 30))
        nouvelles = [l for l in self.db.rows("Releve_Bancaire") if l["fichier_source"].startswith("releve_escrow_2026-11-29")]
        self.assertEqual(len(nouvelles), 2)
        self.assertEqual(nouvelles[0]["montant_aed"], 78600.0)
        self.assertEqual(nouvelles[1]["sens"], "DÉBIT")
        self.assertFalse([l for l in self.db.rows("Releve_Bancaire") if l["fichier_source"].endswith("11-30.csv")])

    def test_mt940(self):
        mt = ":20:STMT\n:25:AE070990000012345678901\n:61:2611280128C78600,00NTRFHLDACR010204\n" \
             ":86:/ORDP/PRIYA RAMAN\n:61:2611280128D105,00NCHGNONREF\n:86:BANK CHARGES\n"
        lignes = ingestion.lire_mt940(mt)
        self.assertEqual([round(l["montant"], 2) for l in lignes], [78600.0, -105.0])
        self.assertEqual(lignes[0]["donneur_ordre"], "PRIYA RAMAN")

    def test_aucun_nom_ni_montant_n_est_envoye_a_l_ia(self):
        envoyes = []

        class Faux:
            class messages:
                @staticmethod
                def parse(**kw):
                    envoyes.append(json.dumps(kw["messages"], ensure_ascii=False))
                    out = kw["output_format"](objet="Reminder ⟦ref⟧", texte="Dear ⟦nom⟧, ⟦detail⟧ Kind regards, ⟦promoteur⟧")

                    class R:
                        stop_reason, parsed_output = "end_turn", out
                        usage = type("U", (), {"input_tokens": 120, "output_tokens": 40})()
                    return R()
        llm = LLM("simule")
        llm.client = Faux()
        faits = {"nom": "Rashid Al Mansoori", "detail": "• ACR-0402 · AED 77,700.00", "ref": "HLD-ACR-0402-03",
                 "promoteur": "Meridian", "reste": "AED 77,700.00"}
        objet, texte = llm.rediger("relance_J+3", "EN", faits)
        self.assertIn("Rashid Al Mansoori", texte)
        self.assertNotIn("Rashid", envoyes[0])
        self.assertNotIn("77,700", envoyes[0])
        self.assertEqual(llm.usage["entree"], 120)
        self.assertNotIn("omar@mail.example", masquer_texte("write to omar@mail.example or +971 50 123 4567"))


if __name__ == "__main__":
    unittest.main()
