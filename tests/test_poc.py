"""Tests du POC : python -m unittest discover -s tests"""
import datetime as dt
import shutil
import tempfile
import unittest
from pathlib import Path

from halden import approvals, audit, guardrails, rules, seed
from halden.db import Database
from halden.llm import LLM
from halden.orchestrator import cycle
from halden.proposition import Proposition


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.base, self.entrees = self.tmp / "base.xlsx", self.tmp / "entrees"
        seed.generer(self.base, self.entrees)
        self.db = Database.load(self.base)

    def tearDown(self):
        shutil.rmtree(self.tmp)


class TestRegles(unittest.TestCase):
    def test_grille(self):
        self.assertEqual(rules.niveau_grille(2, 5, 5, 3, 3, 1, 1), rules.AUCUN)
        self.assertEqual(rules.niveau_grille(5, 4, 5, 1, 5, 1, 1), rules.REGLE)
        self.assertEqual(rules.niveau_grille(3, 3, 5, 4, 5, 1, 5), rules.HUMAIN)
        self.assertEqual(rules.niveau_grille(4, 4, 5, 2, 4, 1, 3), rules.VALIDATION)
        self.assertEqual(rules.niveau_grille(5, 4, 4, 2, 2, 1, 1), rules.AUTONOME)

    def test_relances(self):
        db = Database("x")
        self.assertIsNone(rules.niveau_relance(db, 2))
        self.assertEqual(rules.niveau_relance(db, 3), "J+3")
        self.assertEqual(rules.niveau_relance(db, 12), "J+10")
        self.assertEqual(rules.niveau_relance(db, 30), "J+30")


class TestGardeFous(Base):
    def test_montant_invente_bloque(self):
        p = Proposition(agent="Test", tache_id="T01", action="MESSAGE", resume="x",
                        brouillon="Merci de régler AED 99,999.00", montants_regles=[124000.0], canal="email")
        self.assertEqual(guardrails.evaluer(self.db, p).niveau, rules.BLOQUE)

    def test_remboursement_interdit(self):
        p = Proposition(agent="Test", tache_id="T04", action="REMBOURSEMENT", resume="x")
        self.assertEqual(guardrails.evaluer(self.db, p).niveau, rules.BLOQUE)

    def test_argent_ou_juridique(self):
        p = Proposition(agent="Test", tache_id="T04", action="MESSAGE", resume="x", engage_promoteur=True)
        self.assertEqual(guardrails.evaluer(self.db, p).niveau, rules.VALIDATION)


class TestScenario(Base):
    def test_trois_journees(self):
        llm = LLM("simule")
        b1 = cycle(self.db, dt.date(2026, 11, 2), llm, self.entrees)
        appels = [p for p in b1.propositions if p.action == "APPEL_DE_FONDS"]
        self.assertEqual(len(appels), 20)
        self.assertTrue(all(p.niveau == rules.VALIDATION for p in appels))
        for f in approvals.en_attente(self.db):
            if f["action"] == "APPEL_DE_FONDS":
                approvals.decider(self.db, f["file_id"], True, "Sara K. · CFO", dt.date(2026, 11, 2))
        self.assertEqual(len(self.db.where("Echeancier", declencheur="JALON:ACR-J40", statut="APPELÉ")), 20)

        cycle(self.db, dt.date(2026, 11, 28), llm, self.entrees)
        lignes = self.db.rows("Releve_Bancaire")
        self.assertEqual(len(lignes), 21)                       # 19 crédits + 2 débits
        self.assertEqual(len([l for l in lignes if l["methode"] == "REF_EXACTE"]), 14)
        self.assertEqual(len([l for l in lignes if l["methode"] == "REF_AUTRE_PAYEUR"]), 1)
        self.assertEqual(len([l for l in lignes if l["methode"] == "INCONNU"]), 1)

        b3 = cycle(self.db, dt.date(2026, 12, 5), llm, self.entrees)
        self.assertTrue(all(m["statut"].startswith("SHADOW") for m in self.db.rows("Messages_Sortants")))
        self.assertEqual(len(self.db.where("File_Approbation", statut="BLOQUÉ")), 2)   # deux remboursements
        # Règle du pilote : aucun message vers un acheteur sans validation humaine.
        for b in (b1, b3):
            self.assertFalse([p for p in b.propositions if p.canal and p.niveau in (rules.AUTONOME, rules.REGLE)])

        self.db.save()
        db2 = Database.load(self.base)
        self.assertEqual(audit.verifier(db2), (True, None))
        db2.rows("Journal_Audit")[5]["detail"] = "modifié à la main"
        self.assertFalse(audit.verifier(db2)[0])


if __name__ == "__main__":
    unittest.main()
