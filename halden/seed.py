"""Génère la base Excel de démonstration : données 100 % fictives mais réalistes (Dubaï, off-plan).

Deux projets d'un même promoteur fictif :
- Azure Crest Residences (JVC) : en construction, jalon 40 % certifié le 1er novembre 2026 ;
- Palm Lumen Residences (Dubai Hills) : livré, en phase réserves et garantie.
"""
from __future__ import annotations

import csv
import datetime as dt
import random
from pathlib import Path

from . import rules
from .db import Database

D = dt.date
PROMOTEUR = "Meridian Crest Developments"
RNG = random.Random(2026)

NOMS = [
    ("Omar Al Hashimi", "Émirats arabes unis", "AR", "whatsapp"), ("Priya Raman", "Inde", "EN", "email"),
    ("James Whitfield", "Royaume-Uni", "EN", "email"), ("Elena Sokolova", "Russie", "EN", "whatsapp"),
    ("Ahmed Khalil", "Égypte", "AR", "whatsapp"), ("Sophie Marchand", "France", "FR", "email"),
    ("Rashid Al Mansoori", "Émirats arabes unis", "AR", "whatsapp"), ("Chen Wei", "Chine", "EN", "email"),
    ("Fatima Zahra Benali", "Maroc", "FR", "whatsapp"), ("Lukas Becker", "Allemagne", "EN", "email"),
    ("Aisha Al Suwaidi", "Émirats arabes unis", "AR", "email"), ("Daniel O'Connor", "Irlande", "EN", "email"),
    ("Hassan Qureshi", "Pakistan", "EN", "whatsapp"), ("Nadia Haddad", "Liban", "FR", "whatsapp"),
    ("Marco Bellini", "Italie", "EN", "email"), ("Yuki Tanaka", "Japon", "EN", "email"),
    ("Karim El Amrani", "Maroc", "FR", "whatsapp"), ("Olga Ivanova", "Kazakhstan", "EN", "whatsapp"),
    ("Arjun Mehta", "Inde", "EN", "whatsapp"), ("Layla Al Nuaimi", "Émirats arabes unis", "AR", "whatsapp"),
    ("Thomas Lefèvre", "France", "FR", "email"), ("Mariam Saeed", "Arabie saoudite", "AR", "whatsapp"),
    ("Viktor Novak", "Tchéquie", "EN", "email"), ("Grace Adeyemi", "Nigeria", "EN", "whatsapp"),
    ("Samir Toukan", "Jordanie", "AR", "email"), ("Hannah Schmidt", "Allemagne", "EN", "email"),
    ("Raj Kapoor", "Inde", "EN", "whatsapp"), ("Ines Duarte", "Portugal", "EN", "email"),
    ("Khalid Al Otaibi", "Arabie saoudite", "AR", "whatsapp"), ("Emily Carter", "États-Unis", "EN", "email"),
    ("Youssef Benjelloun", "Maroc", "FR", "whatsapp"), ("Anna Kowalska", "Pologne", "EN", "email"),
]

GRILLE = [  # tache_id, tache, agent, V1 V2 V3 C1 C2 C3 C4, exemple
    ("T01", "Relances d'échéances J+3 / J+10", "Encaissements", 5, 4, 4, 2, 4, 1, 1, "Rappel courtois 3 jours après l'échéance"),
    ("T02", "Vue CFO du matin", "Orchestrateur", 5, 4, 4, 2, 1, 1, 1, "Encaissé, en retard, file d'attente"),
    ("T03", "Tri et affectation des réserves", "Livraison & réserves", 4, 3, 2, 2, 2, 1, 2, "Fuite sous évier → plombier, 48 h"),
    ("T04", "Réponses FAQ acquéreurs", "Relation acquéreurs", 4, 4, 2, 3, 4, 2, 2, "« Quand est ma prochaine échéance ? »"),
    ("T05", "Rédaction des appels de fonds", "Encaissements", 4, 4, 5, 2, 4, 1, 3, "Jalon 40 % certifié → 20 appels"),
    ("T06", "Rapprochement bancaire (cas ambigus)", "Encaissements", 5, 5, 5, 4, 4, 2, 3, "Virement sans référence"),
    ("T07", "Actualités chantier mensuelles", "Relation acquéreurs", 3, 3, 2, 2, 3, 2, 3, "Lettre d'avancement avec photos"),
    ("T08", "Demandes de modification", "Relation acquéreurs", 3, 3, 3, 3, 4, 2, 4, "Changer la finition de la cuisine"),
    ("T09", "Suivi des leads", "Ventes", 4, 3, 4, 3, 3, 3, 3, "Proposer le lot adapté au budget"),
    ("T10", "Calcul des échéances", "Moteur de règles", 5, 4, 5, 1, 5, 1, 1, "10 % du prix au jalon 40 %"),
    ("T11", "Garantie applicable", "Garantie", 3, 3, 3, 1, 4, 1, 2, "Finitions 12 mois, structure 10 ans"),
    ("T12", "Plan pour acquéreur en difficulté", "Encaissements", 3, 3, 5, 4, 5, 1, 5, "Report demandé après perte d'emploi"),
    ("T13", "Contrat, SPA, réservation, annulation", "Contrat", 4, 3, 5, 3, 5, 2, 5, "Signature, résiliation, remboursement"),
    ("T14", "Responsabilité et litige", "Garantie", 3, 2, 5, 4, 5, 1, 5, "Fissure + menace d'avocat"),
    ("T15", "Lettrage exact (référence + payeur + montant)", "Encaissements", 5, 5, 4, 1, 3, 1, 1, "HLD-ACR-0304-04 = montant dû"),
    ("T16", "Collecte des pièces KYC", "Contrat", 4, 3, 2, 2, 3, 2, 1, "Demander la copie du passeport"),
    ("T17", "Suivi SPA et Oqood", "Contrat", 4, 3, 4, 2, 4, 2, 3, "SPA non signé après 30 jours"),
    ("T18", "Réponse garantie à l'acquéreur", "Garantie", 3, 2, 2, 2, 3, 1, 1, "Accusé + intervention planifiée"),
]

PACK = [
    ("pays", "AE-DU", "", "Émirat de Dubaï", "FAIT"),
    ("devise", "AED", "", "", "FAIT"),
    ("delai_paiement_appel_jours", 30, "jours", "Pratique de marché, selon SPA", "À VÉRIFIER"),
    ("relance_niveau_1_jours", 3, "jours", "Choix Halden (pilote)", "HYPOTHÈSE"),
    ("relance_niveau_2_jours", 10, "jours", "Choix Halden (pilote)", "HYPOTHÈSE"),
    ("escalade_jours", 30, "jours", "Choix Halden ; procédure légale selon loi 13/2008 et SPA", "À VÉRIFIER"),
    ("tolerance_frais_bancaires_aed", 100, "AED", "Choix Halden : écart toléré pour frais bancaires (toujours validé)", "HYPOTHÈSE"),
    ("defaut_notification_dld", "Le promoteur notifie le défaut à la DLD, qui notifie l'acheteur (loi de Dubaï n° 13/2008, art. 11, modifiée par la loi n° 19/2017)", "", "Loi 13/2008 art. 11 ; Al Tamimi", "À VÉRIFIER"),
    ("defaut_delai_dld_jours", 30, "jours", "Loi 13/2008 art. 11 modifiée", "À VÉRIFIER"),
    ("defaut_option_80_plus", "maintenir le contrat et réclamer le solde, ou demander la vente du lot aux enchères via la DLD, ou résilier en conservant au plus 40 % du prix", "", "Loi 19/2017", "À VÉRIFIER"),
    ("defaut_option_60_80", "résilier en conservant au plus 40 % du prix", "", "Loi 19/2017", "À VÉRIFIER"),
    ("defaut_option_moins_60", "résilier en conservant au plus 25 % du prix", "", "Loi 19/2017", "À VÉRIFIER"),
    ("delai_signature_spa_jours", 30, "jours", "Pratique de marché", "À VÉRIFIER"),
    ("delai_enregistrement_oqood_jours", 30, "jours", "DLD / Oqood", "À VÉRIFIER"),
    ("frais_oqood_pct", 4, "% du prix", "DLD (frais de transfert)", "À VÉRIFIER"),
    ("garantie_finitions_mois", 12, "mois", "Pratique contractuelle (DLP)", "À VÉRIFIER"),
    ("garantie_structure_ans", 10, "ans", "Code civil EAU (responsabilité décennale)", "À VÉRIFIER"),
    ("penalites_retard", "Selon clause SPA", "", "Jamais calculées par l'IA", "RÈGLE HALDEN"),
    ("compte_escrow", "Obligatoire", "", "Loi Dubaï n°8/2007 (comptes escrow)", "À VÉRIFIER"),
    ("langues", "EN, AR", "", "", "FAIT"),
]

PLAN_ACR = [(1, "Réservation", 10, "DATE"), (2, "Signature du SPA", 10, "DATE"),
            (3, "Jalon 20 % · fondations", 10, "JALON:ACR-J20"), (4, "Jalon 40 % · structure niveau 8", 10, "JALON:ACR-J40"),
            (5, "Jalon 60 % · structure achevée", 10, "JALON:ACR-J60"), (6, "Jalon 80 % · façade et MEP", 10, "JALON:ACR-J80"),
            (7, "Remise des clés", 40, "JALON:ACR-J100")]


def _prix(base: float) -> float:
    return round(base * RNG.uniform(0.96, 1.06) / 1000) * 1000


def generer(path: Path | str, entrees: Path | str, logo: Path | None = None) -> Database:
    db = Database(path)
    db.add_many("Parametres", [
        {"cle": "date_simulation", "valeur": D(2026, 11, 2), "description": "Date du jour simulée (modifiée à chaque cycle)"},
        {"cle": "mode_shadow", "valeur": "OUI", "description": "OUI = rien n'est envoyé, tout est préparé et journalisé"},
        {"cle": "llm_mode", "valeur": "simule", "description": "simule | claude (API Anthropic) | bedrock (AWS me-central-1)"},
        {"cle": "approbateur", "valeur": "Sara K. · CFO", "description": "Personne fictive qui valide dans la démo"},
        {"cle": "promoteur", "valeur": PROMOTEUR, "description": "Promoteur fictif"},
        {"cle": "perimetre", "valeur": "PILOTE", "description": "PILOTE = encaissements seuls (Dubaï) | VISION = les six agents"},
        {"cle": "approbateurs_autorises", "valeur": "Sara K. · CFO", "description": "Seules ces personnes peuvent décider (séparées par ;). Connexion réelle à prévoir avant le pilote"},
        {"cle": "regle_approbation", "valeur": "Chaque message vers un acheteur est validé par un humain",
         "description": "Écrite dans le code (garde-fous), affichée ici pour mémoire : non modifiable dans l'Excel"},
    ])
    db.add_many("Pack_Pays", [dict(zip(["cle", "valeur", "unite", "source", "statut"], r)) for r in PACK])
    for t in GRILLE:
        s = t[3:10]
        db.add("Grille_Decision", {
            "tache_id": t[0], "tache": t[1], "agent": t[2], "V1_volume": s[0], "V2_temps": s[1],
            "V3_cash_risque": s[2], "C1_ambiguite": s[3], "C2_consequence": s[4], "C3_integration": s[5],
            "C4_jugement": s[6], "niveau": rules.niveau_grille(*s), "phase": rules.phase_grille(s[5]),
            "exemple": t[10], "sensibilite": rules.sensibilite(list(s))})

    db.add_many("Projets", [
        {"projet_id": "ACR", "nom": "Azure Crest Residences", "promoteur": PROMOTEUR, "localisation":
         "Jumeirah Village Circle, Dubaï", "statut": "EN CONSTRUCTION", "avancement_pct": 20,
         "date_lancement": D(2025, 9, 15), "date_livraison": D(2027, 12, 15),
         "compte_escrow": "AE07 0990 0000 1234 5678 901", "banque_escrow": "Banque escrow (fictive)"},
        {"projet_id": "PLR", "nom": "Palm Lumen Residences", "promoteur": PROMOTEUR, "localisation":
         "Dubai Hills Estate, Dubaï", "statut": "LIVRÉ · GARANTIE", "avancement_pct": 100,
         "date_lancement": D(2022, 10, 1), "date_livraison": D(2025, 11, 20),
         "compte_escrow": "AE51 0990 0000 9876 5432 109", "banque_escrow": "Banque escrow (fictive)"},
    ])
    db.add_many("Jalons", [
        {"jalon_id": "ACR-J20", "projet_id": "ACR", "libelle": "Jalon 20 % · fondations", "seuil_pct": 20,
         "date_certificat": D(2026, 9, 20), "certificat_ref": "CERT-ACR-020", "statut": "TRAITÉ"},
        {"jalon_id": "ACR-J40", "projet_id": "ACR", "libelle": "Jalon 40 % · structure niveau 8", "seuil_pct": 40,
         "date_certificat": D(2026, 11, 1), "certificat_ref": "CERT-ACR-040", "statut": "CERTIFIÉ"},
        {"jalon_id": "ACR-J60", "projet_id": "ACR", "libelle": "Jalon 60 % · structure achevée", "seuil_pct": 60,
         "statut": "À VENIR"},
        {"jalon_id": "ACR-J80", "projet_id": "ACR", "libelle": "Jalon 80 % · façade et MEP", "seuil_pct": 80,
         "statut": "À VENIR"},
        {"jalon_id": "ACR-J100", "projet_id": "ACR", "libelle": "Achèvement · remise des clés", "seuil_pct": 100,
         "statut": "À VENIR"},
    ])
    db.add_many("Sous_Traitants", [
        {"st_id": "ST-01", "nom": "AquaFix Technical Services", "specialite": "Plomberie", "contact": "ops@aquafix.example"},
        {"st_id": "ST-02", "nom": "Volt Line Electromechanical", "specialite": "Électricité", "contact": "jobs@voltline.example"},
        {"st_id": "ST-03", "nom": "Polar Breeze HVAC", "specialite": "Climatisation", "contact": "service@polarbreeze.example"},
        {"st_id": "ST-04", "nom": "Cedar & Oak Joinery", "specialite": "Menuiserie", "contact": "site@cedaroak.example"},
        {"st_id": "ST-05", "nom": "Fine Finish Contracting", "specialite": "Finitions", "contact": "snag@finefinish.example"},
        {"st_id": "ST-06", "nom": "Atlas Structural Consultants", "specialite": "Structure", "contact": "expertise@atlas.example"},
    ])

    # --- Acheteurs -------------------------------------------------------------------
    for i, (nom, nat, langue, canal) in enumerate(NOMS, start=1):
        slug = nom.lower().replace(" ", ".").replace("'", "")
        db.add("Acheteurs", {"acheteur_id": f"ACH-{i:03d}", "nom": nom, "nationalite": nat, "langue": langue,
                             "canal": canal, "email": f"{slug}@mail.example", "telephone": f"+971 50 {RNG.randint(100, 999)} {RNG.randint(1000, 9999)}",
                             "kyc_passeport": "OK", "kyc_emirates_id": "OK", "kyc_justif_adresse": "OK",
                             "contact_auto": "ACTIF"})
    for aid, champ in (("ACH-018", "kyc_justif_adresse"), ("ACH-019", "kyc_emirates_id"), ("ACH-019", "kyc_justif_adresse")):
        db.get("Acheteurs", acheteur_id=aid)[champ] = "MANQUANT"

    # --- Azure Crest : 24 lots, 20 vendus ------------------------------------------------
    dispo = {"ACR-0302", "ACR-0702", "ACR-1001", "ACR-1202"}
    acheteurs = iter(f"ACH-{i:03d}" for i in range(1, 21))
    resa_dates = [D(2025, 9, 20) + dt.timedelta(days=14 * k) for k in range(16)] + \
                 [D(2026, 9, 25), D(2026, 9, 28), D(2026, 10, 1), D(2026, 9, 26)]
    k = 0
    ventes = []
    for etage in range(1, 13):
        for pos in (1, 2):
            uid = f"ACR-{etage:02d}{pos:02d}"
            if etage <= 4:
                typ, surf, base = ("Studio", 455, 780_000) if pos == 2 else ("1 chambre", 780, 1_250_000)
            elif etage <= 8:
                typ, surf, base = ("1 chambre", 790, 1_300_000) if pos == 1 else ("2 chambres", 1_160, 1_900_000)
            else:
                typ, surf, base = ("2 chambres", 1_180, 2_050_000) if pos == 1 else ("3 chambres", 1_650, 2_950_000)
            prix = _prix(base * (1 + 0.006 * etage))
            u = {"unite_id": uid, "projet_id": "ACR", "etage": etage, "type": typ, "surface_sqft": surf, "prix_aed": prix}
            if uid in dispo:
                u["statut"] = "DISPONIBLE"
            else:
                aid = next(acheteurs)
                u.update(statut="VENDUE", acheteur_id=aid, date_reservation=resa_dates[k])
                ventes.append(u)
                k += 1
            db.add("Unites", u)
    if db.get("Unites", unite_id="ACR-0302"):
        u = db.get("Unites", unite_id="ACR-0302")
        u.update(type="Studio", surface_sqft=460, prix_aed=812_000)

    retard_j20 = {"ACH-003": "IMPAYÉ_PUIS_PAYE", "ACH-007": "IMPAYÉ", "ACH-011": "PARTIEL"}
    recents = {"ACH-017": "PAYÉ", "ACH-018": "IMPAYÉ_PUIS_CUMUL", "ACH-019": "IMPAYÉ", "ACH-020": "SPA_NON_SIGNÉ"}
    for u in ventes:
        aid, resa = u["acheteur_id"], u["date_reservation"]
        recent = aid in recents
        date_spa = resa + dt.timedelta(days=5 if recent else 12)
        contrat = {"contrat_id": f"CTR-{u['unite_id']}", "unite_id": u["unite_id"], "acheteur_id": aid,
                   "date_reservation": resa, "spa_statut": "SIGNÉ", "date_spa": date_spa,
                   "oqood_statut": "ENREGISTRÉ", "date_oqood": date_spa + dt.timedelta(days=21)}
        if aid in ("ACH-009", "ACH-014"):
            contrat.update(date_spa=D(2026, 8, 14), oqood_statut="EN ATTENTE", date_oqood=None)
        if recent:
            contrat.update(oqood_statut="EN ATTENTE", date_oqood=None)
        if recents.get(aid) == "SPA_NON_SIGNÉ":
            contrat.update(spa_statut="ENVOYÉ", date_spa=None)
        db.add("Contrats", contrat)

        for num, lib, pct, decl in PLAN_ACR:
            montant = rules.montant_echeance(u["prix_aed"], pct)
            e = {"echeance_id": f"ECH-{u['unite_id']}-{num:02d}", "projet_id": "ACR", "unite_id": u["unite_id"],
                 "acheteur_id": aid, "num": num, "libelle": lib, "declencheur": decl, "pourcentage": pct,
                 "montant_aed": montant, "montant_paye_aed": 0, "statut": "À VENIR",
                 "reference": rules.reference(u["unite_id"], num)}
            if num == 1:
                e.update(date_appel=resa, date_limite=resa, montant_paye_aed=montant, statut="PAYÉ")
            elif num == 2 or (num == 3 and recent):
                lim = resa + dt.timedelta(days=30)
                e.update(date_appel=resa, date_limite=lim, statut="PAYÉ", montant_paye_aed=montant)
                if num == 3:
                    e["declencheur"] = "JALON:ACR-J20 (atteint avant la vente)"
                if recents.get(aid, "").startswith("IMPAYÉ"):
                    e.update(statut="APPELÉ", montant_paye_aed=0)
            elif num == 3:
                e.update(date_appel=D(2026, 9, 22), date_limite=D(2026, 10, 22), statut="PAYÉ", montant_paye_aed=montant)
                cas = retard_j20.get(aid)
                if cas in ("IMPAYÉ", "IMPAYÉ_PUIS_PAYE"):
                    e.update(statut="APPELÉ", montant_paye_aed=0)
                elif cas == "PARTIEL":
                    e.update(statut="PARTIEL", montant_paye_aed=round(montant * 0.4, 2))
            db.add("Echeancier", e)
    for aid in retard_j20:
        e = next(x for x in db.where("Echeancier", acheteur_id=aid) if x["num"] == 3)
        db.add("Relances", {"relance_id": db.next_id("Relances", "REL-"), "date": D(2026, 10, 25),
                            "echeance_id": e["echeance_id"], "acheteur_id": aid, "niveau": "J+3", "jours_retard": 3,
                            "canal": db.get("Acheteurs", acheteur_id=aid)["canal"], "statut": "ENVOYÉ"})

    # --- Palm Lumen : livré, 12 lots --------------------------------------------------------
    for n, aid in enumerate(range(21, 33)):
        etage, pos = n // 2 + 1, n % 2 + 1
        uid = f"PLR-{etage:02d}{pos:02d}"
        typ, surf, base = ("2 chambres", 1_240, 2_300_000) if pos == 1 else ("3 chambres", 1_720, 3_200_000)
        prix = _prix(base)
        livraison = D(2025, 11, 20) if n not in (0, 1) else D(2025, 8, 10)
        statut = "LIVRÉE"
        if uid in ("PLR-0501", "PLR-0602"):
            statut, livraison = "PRÊTE · SOLDE DÛ", None
        db.add("Unites", {"unite_id": uid, "projet_id": "PLR", "etage": etage, "type": typ, "surface_sqft": surf,
                          "prix_aed": prix, "statut": statut, "acheteur_id": f"ACH-{aid:03d}",
                          "date_reservation": D(2022, 11, 1) + dt.timedelta(days=9 * n), "date_livraison": livraison})
        db.add("Contrats", {"contrat_id": f"CTR-{uid}", "unite_id": uid, "acheteur_id": f"ACH-{aid:03d}",
                            "date_reservation": D(2022, 11, 1) + dt.timedelta(days=9 * n), "spa_statut": "SIGNÉ",
                            "date_spa": D(2022, 11, 15) + dt.timedelta(days=9 * n), "oqood_statut": "ENREGISTRÉ",
                            "date_oqood": D(2022, 12, 10) + dt.timedelta(days=9 * n)})
        for num, lib, pct in ((1, "Paiements construction (60 %)", 60), (2, "Remise des clés (40 %)", 40)):
            m = rules.montant_echeance(prix, pct)
            e = {"echeance_id": f"ECH-{uid}-{num:02d}", "projet_id": "PLR", "unite_id": uid,
                 "acheteur_id": f"ACH-{aid:03d}", "num": num, "libelle": lib,
                 "declencheur": "DATE" if num == 1 else "JALON:PLR-J100", "pourcentage": pct, "montant_aed": m,
                 "date_appel": D(2025, 9, 1) if num == 2 else D(2023, 1, 1),
                 "date_limite": D(2025, 10, 1) if num == 2 else D(2025, 6, 30),
                 "montant_paye_aed": m, "statut": "PAYÉ", "reference": rules.reference(uid, num)}
            if statut != "LIVRÉE" and num == 2:
                e.update(statut="APPELÉ", montant_paye_aed=0, date_appel=D(2026, 9, 15), date_limite=D(2026, 10, 15))
            db.add("Echeancier", e)

    # --- Entrées du jour : messages, leads, réserves, garantie ---------------------------------
    msgs = [
        ("ACH-002", "email", "Hello, could you tell me when my next payment is due and how much it is?"),
        ("ACH-005", "whatsapp", "متى موعد التسليم المتوقع للمشروع؟"),
        ("ACH-012", "email", "Hi, I would like to change the kitchen finish to dark oak instead of the white gloss. Is it possible?"),
        ("ACH-019", "whatsapp", "I lost my job last month. Can I postpone my next payment by 3 months? I really want to keep the apartment."),
        ("ACH-016", "email", "I want to cancel my purchase and get a refund of everything I paid. Please process it."),
        ("ACH-006", "email", "Bonjour, pouvez-vous m'envoyer mon relevé de compte (statement) à jour ? Merci."),
        ("ACH-010", "email", "Any construction update? Last photos were from September."),
        # Cas relevés par la revue du 24 octobre : chacun doit arrêter les relances ou bloquer la réponse.
        ("ACH-007", "whatsapp", "دفعت القسط أمس، لماذا التذكير؟"),
        ("ACH-011", "email", "What is my balance?"),
        ("ACH-004", "whatsapp", "Please cancel the reminders, I'm talking to my lawyer."),
        ("ACH-001", "whatsapp", "Hi, I'm Omar's assistant, send me his statement please.", "+971 55 000 1122"),
    ]
    for i, m in enumerate(msgs, start=1):
        aid, canal, txt = m[:3]
        a = db.get("Acheteurs", acheteur_id=aid)
        exp = m[3] if len(m) > 3 else (a["email"] if canal == "email" else a["telephone"])
        db.add("Messages_Entrants", {"msg_id": f"MSG-{i:04d}", "date": D(2026, 11, 1), "acheteur_id": aid,
                                     "canal": canal, "expediteur": exp, "texte": txt, "statut": "NOUVEAU"})
    leads = [
        ("Rania Farouk", "Bayut", "Égypte", 840_000, "Studio", D(2026, 10, 30), 4, "NOUVEAU"),
        ("Tom Hendricks", "Site web", "Pays-Bas", 2_000_000, "2 chambres", D(2026, 10, 28), 3, "NOUVEAU"),
        ("Mei Lin", "Salon Cityscape", "Singapour", 2_500_000, "3 chambres", D(2026, 10, 20), 2, "NOUVEAU"),
        ("Sergio Alvarez", "Agent partenaire", "Espagne", 1_450_000, "1 chambre", D(2026, 9, 1), 0, "NOUVEAU"),
        ("Abdullah Al Fahim", "Recommandation", "Émirats arabes unis", 3_300_000, "3 chambres", D(2026, 10, 31), 6,
         "RÉSERVATION DEMANDÉE"),
        ("Clara Dubois", "Instagram", "France", 900_000, "Studio", D(2026, 10, 12), 1, "NOUVEAU"),
    ]
    for i, (nom, src, nat, budget, rech, contact, inter, st) in enumerate(leads, start=1):
        db.add("Leads", {"lead_id": f"LEAD-{i:03d}", "date": contact, "nom": nom, "source": src, "nationalite": nat,
                         "budget_aed": budget, "recherche": rech, "dernier_contact": contact, "interactions": inter,
                         "statut": st})
    reserves = [
        ("PLR-0201", "Fuite sous l'évier de la cuisine", "Cuisine"),
        ("PLR-0201", "Rayure sur la porte du placard de l'entrée", "Entrée"),
        ("PLR-0302", "Prise électrique ne fonctionne pas dans la chambre 2", "Chambre 2"),
        ("PLR-0401", "Thermostat de la clim bloqué à 26°C", "Séjour"),
        ("PLR-0402", "Joint de carrelage fissuré dans la douche", "Salle de bain"),
        ("PLR-0102", "Porte-fenêtre du balcon ne ferme pas correctement", "Balcon"),
    ]
    for i, (uid, desc, loc) in enumerate(reserves, start=1):
        db.add("Reserves", {"reserve_id": f"RSV-{i:04d}", "date": D(2026, 10, 31), "projet_id": "PLR", "unite_id": uid,
                            "description": desc, "localisation": loc, "statut": "NOUVEAU"})
    garanties = [
        ("PLR-0301", "Water leak from the bathroom ceiling, stains are spreading."),
        ("PLR-0402", "The A/C in the master bedroom is not cooling at all since last week."),
        ("PLR-0101", "Kitchen cabinet door hinge is broken."),
        ("PLR-0202", "There is a long structural crack in the living room wall. My lawyer says this is serious."),
    ]
    for i, (uid, desc) in enumerate(garanties, start=1):
        u = db.get("Unites", unite_id=uid)
        db.add("Garantie", {"reclamation_id": f"GAR-{i:04d}", "date": D(2026, 11, 1), "unite_id": uid,
                            "acheteur_id": u["acheteur_id"], "description": desc, "statut": "NOUVEAU"})

    db.save(logo)
    ecrire_releve(db, Path(entrees))
    return db


def ecrire_releve(db: Database, dossier: Path) -> Path:
    """Relevé escrow du 28 novembre 2026 : virements reçus après les appels de fonds du jalon 40 %."""
    dossier.mkdir(parents=True, exist_ok=True)
    ech = {e["echeance_id"]: e for e in db.rows("Echeancier")}
    ach = {a["acheteur_id"]: a for a in db.rows("Acheteurs")}
    lignes = []
    j40 = [e for e in db.rows("Echeancier") if e["declencheur"] == "JALON:ACR-J40"]
    payeurs_exacts = j40[:13]
    formats = ["TRF/{ref}/INSTALMENT", "{ref} payment", "INWARD TT {ref} {nom}", "IPI {ref}"]
    for n, e in enumerate(payeurs_exacts):
        nom = ach[e["acheteur_id"]]["nom"]
        lignes.append((D(2026, 11, 10) + dt.timedelta(days=n % 12), formats[n % 4].format(ref=e["reference"], nom=nom.upper()),
                       nom.upper(), e["montant_aed"]))
    partiel, sans_ref = j40[13], j40[14]
    lignes.append((D(2026, 11, 24), f"PART PAYMENT {partiel['reference']}", ach[partiel["acheteur_id"]]["nom"].upper(),
                   round(partiel["montant_aed"] / 2, 2)))
    nom = ach[sans_ref["acheteur_id"]]["nom"].split()
    lignes.append((D(2026, 11, 25), "INWARD REMITTANCE", f"{nom[-1].upper()} {nom[0].upper()}", sans_ref["montant_aed"]))
    l1 = ech[next(k for k in ech if k.startswith("ECH-") and ech[k]["acheteur_id"] == "ACH-003" and ech[k]["num"] == 3)]
    lignes.append((D(2026, 11, 6), f"TRF/{l1['reference']}/LATE", "JAMES WHITFIELD", l1["montant_aed"]))
    cumul = [e for e in db.rows("Echeancier") if e["acheteur_id"] == "ACH-018" and e["statut"] == "APPELÉ"]
    n18 = ach["ACH-018"]["nom"].split()
    lignes.append((D(2026, 11, 20), "TT FROM ABROAD", f"{n18[-1].upper()} {n18[0].upper()}", round(sum(e["montant_aed"] for e in cumul), 2)))
    lignes.append((D(2026, 11, 26), "INWARD TT", "ALPHA HORIZON TRADING FZE", 47_250.00))
    # La bonne référence et le bon montant, mais pas le bon payeur : jamais lettré automatiquement.
    autre = j40[15]
    lignes.append((D(2026, 11, 27), f"TRF/{autre['reference']}", "AL HASHIMI OMAR", autre["montant_aed"]))
    lignes.sort(key=lambda x: x[0])
    f = dossier / "releve_escrow_2026-11-28.csv"
    with f.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date_valeur", "libelle", "donneur_ordre", "credit_aed", "debit_aed"])
        for d, lib, don, m in lignes:
            w.writerow([d.isoformat(), lib, don, f"{m:.2f}", ""])
        w.writerow(["2026-11-28", "ACCOUNT MAINTENANCE FEE", "BANK", "", "105.00"])
        # Un virement revient rejeté : l'échéance qu'il avait soldée doit redevenir due.
        rejet = payeurs_exacts[10]
        w.writerow(["2026-11-28", f"RETURNED TRF {rejet['reference']} BENEFICIARY BANK REJECT",
                    ach[rejet["acheteur_id"]]["nom"].upper(), "", f"{rejet['montant_aed']:.2f}"])
    return f
