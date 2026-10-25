"""Couche 5 · Moteur de règles : tout ce qui se calcule se calcule ici, jamais par l'IA.

Montants, échéances, niveaux de relance, lettrage bancaire, garantie applicable,
score des leads et niveau d'autonomie de chaque tâche (grille de décision).
"""
from __future__ import annotations

import datetime as dt
import difflib
import re
import unicodedata
from dataclasses import dataclass

from .db import Database

# Niveaux d'autonomie, du plus libre au plus encadré.
AUTONOME, REGLE, VALIDATION, HUMAIN, BLOQUE, AUCUN = (
    "AUTONOME", "RÈGLE", "VALIDATION", "HUMAIN", "BLOQUÉ", "AUCUN AGENT")
ORDRE = {AUTONOME: 0, REGLE: 0, VALIDATION: 1, HUMAIN: 2, BLOQUE: 3, AUCUN: 3}


# --- Grille de décision ---------------------------------------------------------
def niveau_grille(v1: int, v2: int, v3: int, c1: int, c2: int, c3: int, c4: int) -> str:
    """Arbre de décision de l'équipe (HYPOTHÈSE à tester en entretiens).

    V1<3 → pas d'agent ; C1≤1 → règle déterministe ; C2=5 et C4=5 → humain
    (l'agent ne fait que préparer le dossier) ; C2≥4 ou C4≥4 → l'agent prépare,
    un humain valide ; C2≤2 → autonome et journalisé ; sinon validation.
    """
    if v1 < 3:
        return AUCUN
    if c1 <= 1:
        return REGLE
    if c2 >= 5 and c4 >= 5:
        return HUMAIN
    if c2 >= 4 or c4 >= 4:
        return VALIDATION
    if c2 <= 2:
        return AUTONOME
    return VALIDATION


CRITERES = ("V1", "V2", "V3", "C1", "C2", "C3", "C4")


def sensibilite(scores: list[int]) -> str:
    """Quelles décisions basculent si une note bouge d'un point ? (la grille est fragile)"""
    base = niveau_grille(*scores)
    out = []
    for i, nom in enumerate(CRITERES):
        for d in (-1, 1):
            s = list(scores)
            s[i] = min(5, max(1, s[i] + d))
            if s[i] != scores[i] and niveau_grille(*s) != base:
                out.append(f"{nom}{'+' if d > 0 else '−'}1 → {niveau_grille(*s)}")
    return " ; ".join(out) or "stable à ±1"


def phase_grille(c3: int) -> str:
    return "Pilote" if c3 <= 2 else ("Ensuite (connecteur)" if c3 == 3 else "Vision (licence / tiers)")


def niveau_tache(db: Database, tache_id: str) -> str:
    r = db.get("Grille_Decision", tache_id=tache_id)
    if not r:
        return VALIDATION
    s = [int(r[k] or 0) for k in ("V1_volume", "V2_temps", "V3_cash_risque", "C1_ambiguite",
                                    "C2_consequence", "C3_integration", "C4_jugement")]
    return niveau_grille(*s)


def plus_strict(a: str, b: str) -> str:
    return a if ORDRE[a] >= ORDRE[b] else b


# --- Montants et échéances ------------------------------------------------------
def montant_echeance(prix_aed: float, pourcentage: float) -> float:
    return round(prix_aed * pourcentage / 100.0, 2)


def reste_du(e: dict) -> float:
    return round(float(e["montant_aed"] or 0) - float(e["montant_paye_aed"] or 0), 2)


def fmt_aed(x: float) -> str:
    return f"AED {x:,.2f}"


def reference(unite_id: str, num: int) -> str:
    return f"HLD-{unite_id}-{int(num):02d}"


def jours_retard(e: dict, today: dt.date) -> int:
    if not e.get("date_limite"):
        return 0
    return (today - e["date_limite"]).days


def niveau_relance(db: Database, retard: int) -> str | None:
    """J+3 rappel courtois, J+10 rappel ferme, J+30 escalade humaine."""
    n1 = int(db.pack("relance_niveau_1_jours", 3))
    n2 = int(db.pack("relance_niveau_2_jours", 10))
    n3 = int(db.pack("escalade_jours", 30))
    if retard >= n3:
        return "J+30"
    if retard >= n2:
        return "J+10"
    if retard >= n1:
        return "J+3"
    return None


# --- Rapprochement bancaire -----------------------------------------------------
# Seuils (hypothèses de l'équipe, à recalibrer sur un vrai relevé anonymisé) :
# - SEUIL_NOM = 0,72 : similarité minimale entre le donneur d'ordre et le nom de l'acheteur
#   (tolère l'ordre inversé « HADDAD NADIA », un second prénom ou une faute de frappe).
# - L'« indice » d'un rapprochement (0,55 + 0,35 × similarité, etc.) est un classement
#   heuristique pour trier la file : ce n'est PAS une probabilité. Il ne décide jamais seul.
SEUIL_NOM = 0.72
OUVERTS = ("APPELÉ", "PARTIEL", "EN RETARD")


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", " ", s.lower())


def similarite_nom(a: str, b: str) -> float:
    ta, tb = sorted(_plain(a).split()), sorted(_plain(b).split())
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()


def trouver_reference(texte: str, projets: list[str]) -> str | None:
    """Lit une référence d'échéance dans tous les formats vus sur les relevés :
    HLD-ACR-0402-03, HLDACR040203, ACR-0402-03, « HLD ACR 0402 03 », « unit ACR-0402 instalment 3 »."""
    codes = "|".join(map(re.escape, projets)) or "[A-Z]{3}"
    haut = (texte or "").upper()
    m = re.search(rf"(?:HLD)?({codes})(\d{{4}})(\d{{2}})(?!\d)", re.sub(r"[^A-Z0-9]", "", haut))
    if m:
        return reference(f"{m.group(1)}-{m.group(2)}", int(m.group(3)))
    m = re.search(rf"({codes})[-\s]?(\d{{4}})\b.{{0,30}}?(?:INSTAL+MENT|INST\.?|ECHEANCE|ÉCHÉANCE|NO\.?|N°|#)\s*(\d{{1,2}})\b",
                  haut)
    if m:
        return reference(f"{m.group(1)}-{m.group(2)}", int(m.group(3)))
    return None


def reference_de(ligne: dict, db: Database) -> str:
    return trouver_reference(f"{ligne.get('libelle') or ''}", [p["projet_id"] for p in db.rows("Projets")]) or ""


@dataclass
class Rapprochement:
    methode: str            # REF_EXACTE, REF_AUTRE_PAYEUR, REF_FRAIS_BANCAIRES, REF_MONTANT_DIFFERENT,
                            # REF_DEJA_PAYEE, NOM_MONTANT, CUMUL_ACHETEUR, INCONNU
    score: float            # indice de tri de la file (heuristique, pas une probabilité)
    echeances: list[dict]
    acheteur_id: str | None
    explication: str

    @property
    def automatique(self) -> bool:
        return self.methode == "REF_EXACTE"


def rapprocher(db: Database, ligne: dict) -> Rapprochement:
    montant = round(float(ligne["montant_aed"]), 2)
    donneur = ligne.get("donneur_ordre") or ""
    texte = f"{ligne.get('libelle') or ''} {donneur}"
    tol = float(db.pack("tolerance_frais_bancaires_aed", 100))
    ouvertes = [e for e in db.rows("Echeancier") if e["statut"] in OUVERTS]
    acheteurs = {a["acheteur_id"]: a for a in db.rows("Acheteurs")}

    ref = trouver_reference(texte, [p["projet_id"] for p in db.rows("Projets")])
    e = next((x for x in db.rows("Echeancier") if x["reference"] == ref), None) if ref else None
    if e:
        titulaire = acheteurs.get(e["acheteur_id"], {}).get("nom", "?")
        sim = similarite_nom(donneur, titulaire)
        if e["statut"] not in OUVERTS:
            return Rapprochement("REF_DEJA_PAYEE", 0.4, [e], e["acheteur_id"],
                                 f"Référence {ref} déjà soldée ({e['statut']}) : doublon, trop-perçu ou "
                                 f"erreur de référence. À vérifier avant toute affectation.")
        du = reste_du(e)
        if sim < SEUIL_NOM:
            autre = max(((a, similarite_nom(donneur, a["nom"])) for a in acheteurs.values()
                         if a["acheteur_id"] != e["acheteur_id"]), key=lambda x: x[1], default=(None, 0))
            piste = ""
            if autre[0] and autre[1] >= SEUIL_NOM:
                doit = [x for x in ouvertes if x["acheteur_id"] == autre[0]["acheteur_id"]
                        and abs(reste_du(x) - montant) <= tol]
                piste = (f" Le payeur ressemble à « {autre[0]['nom']} »"
                         + (f", qui doit aussi ce montant ({doit[0]['echeance_id']})." if doit else "."))
            return Rapprochement("REF_AUTRE_PAYEUR", 0.5, [e], e["acheteur_id"],
                                 f"La référence {ref} appartient à « {titulaire} », mais le virement vient de "
                                 f"« {donneur} » (similarité {sim:.0%}).{piste} Ne rien affecter sans vérifier "
                                 f"l'avis de virement.")
        if abs(du - montant) < 0.01:
            return Rapprochement("REF_EXACTE", 1.0, [e], e["acheteur_id"],
                                 f"Référence {ref}, payeur conforme (« {donneur} ») et montant identique au "
                                 f"reste dû ({fmt_aed(du)}).")
        if 0 < du - montant <= tol:
            return Rapprochement("REF_FRAIS_BANCAIRES", 0.8, [e], e["acheteur_id"],
                                 f"Référence {ref} et payeur conformes, mais {fmt_aed(du - montant)} de moins que "
                                 f"le reste dû ({fmt_aed(du)}) : frais bancaires probables. Lettrer et décider "
                                 f"si l'écart est réclamé ou abandonné.")
        return Rapprochement("REF_MONTANT_DIFFERENT", 0.7, [e], e["acheteur_id"],
                             f"Référence {ref} et payeur conformes, mais {fmt_aed(montant)} reçu pour "
                             f"{fmt_aed(du)} dû (paiement partiel ou en trop).")

    # Pas de référence exploitable : nom du donneur d'ordre + montant.
    best = None
    for a in acheteurs.values():
        sim = similarite_nom(donneur, a["nom"])
        if sim < SEUIL_NOM:
            continue
        siennes = [x for x in ouvertes if x["acheteur_id"] == a["acheteur_id"]]
        exact = [x for x in siennes if abs(reste_du(x) - montant) < 0.01]
        if exact:
            cand = Rapprochement("NOM_MONTANT", round(0.55 + 0.35 * sim, 2), [exact[0]], a["acheteur_id"],
                                 f"Pas de référence. Donneur d'ordre proche de « {a['nom']} » "
                                 f"(similarité {sim:.0%}) et montant égal à une échéance ouverte.")
        else:
            echues = [x for x in siennes if x["date_limite"] and x["date_limite"] <= ligne["date_valeur"]]
            groupe = next((g for g in (echues, siennes)
                           if len(g) > 1 and abs(sum(reste_du(x) for x in g) - montant) < 0.01), None)
            if not groupe:
                continue
            cand = Rapprochement("CUMUL_ACHETEUR", round(0.5 + 0.3 * sim, 2), groupe, a["acheteur_id"],
                                 f"Pas de référence. Montant égal au total des {len(groupe)} échéances échues de "
                                 f"« {a['nom']} » (similarité du nom {sim:.0%}).")
        if best is None or cand.score > best.score:
            best = cand
    if best:
        return best
    return Rapprochement("INCONNU", 0.0, [], None,
                         "Aucune référence, aucun acheteur ni montant correspondant.")


# --- Procédure de défaut de Dubaï (J+30) -----------------------------------------
def procedure_defaut(db: Database, avancement_pct: float) -> str:
    """Étapes de la procédure de défaut, lues dans le pack pays (à valider par un juriste émirati).

    Le moteur ne déclenche rien : il prépare le dossier pour la décision humaine.
    """
    a = float(avancement_pct or 0)
    if a >= 80:
        option = db.pack("defaut_option_80_plus", "?")
    elif a >= 60:
        option = db.pack("defaut_option_60_80", "?")
    else:
        option = db.pack("defaut_option_moins_60", "?")
    ligne = db.get("Pack_Pays", cle="defaut_notification_dld") or {}
    return (f"1. {db.pack('defaut_notification_dld', '?')}\n"
            f"2. Délai laissé à l'acheteur après notification : {db.pack('defaut_delai_dld_jours', '?')} jours.\n"
            f"3. Avancement certifié {a:.0f} % → {option}\n"
            f"Statut : {ligne.get('statut') or 'À VÉRIFIER'} · à faire valider par un juriste émirati avant tout "
            f"usage réel.")


# --- Garantie ------------------------------------------------------------------
CATEGORIES_GARANTIE = {
    "structure": ["fissure", "crack", "structural", "structure", "affaissement", "fondation"],
    "plomberie": ["fuite", "leak", "water", "eau", "plomb", "drain", "tap"],
    "climatisation": ["clim", "a/c", "ac ", "air condition", "hvac", "cooling"],
    "électricité": ["électri", "electric", "socket", "prise", "light", "lumière", "power"],
    "finitions": ["peinture", "paint", "carrelage", "tile", "porte", "door", "parquet", "cabinet", "placard"],
}


def categoriser(texte: str, table: dict[str, list[str]] = CATEGORIES_GARANTIE) -> str:
    t = (texte or "").lower()
    for cat, mots in table.items():
        if any(m in t for m in mots):
            return cat
    return "autre"


def garantie_applicable(db: Database, categorie: str, date_livraison: dt.date, today: dt.date) -> tuple[str, bool]:
    mois_finitions = int(db.pack("garantie_finitions_mois", 12))
    ans_structure = int(db.pack("garantie_structure_ans", 10))
    age = (today - date_livraison).days
    if categorie == "structure":
        return f"Structure {ans_structure} ans", age <= ans_structure * 365
    return f"Équipements et finitions {mois_finitions} mois", age <= mois_finitions * 30.4


# --- Leads ---------------------------------------------------------------------
def score_lead(lead: dict, unites_dispo: list[dict], today: dt.date) -> tuple[int, dict | None]:
    """Score 0-100 : adéquation budget/produit (50), fraîcheur (25), engagement (25)."""
    budget = float(lead["budget_aed"] or 0)
    compatibles = [u for u in unites_dispo
                   if (lead["recherche"] or "").lower() in (u["type"] or "").lower()
                   and u["prix_aed"] <= budget * 1.05]
    meilleure = max(compatibles, key=lambda u: u["prix_aed"], default=None)
    s_budget = 50 if meilleure else (15 if any(u["prix_aed"] <= budget * 1.05 for u in unites_dispo) else 0)
    jours = (today - lead["dernier_contact"]).days if lead.get("dernier_contact") else 99
    s_frais = 25 if jours <= 7 else (15 if jours <= 21 else 5)
    s_eng = min(25, int(lead["interactions"] or 0) * 5)
    return s_budget + s_frais + s_eng, meilleure


# --- Réserves (snags) ----------------------------------------------------------
CATEGORIES_RESERVES = {
    "plomberie": ["fuite", "leak", "robinet", "tap", "drain", "évacuation", "wc", "douche"],
    "électricité": ["prise", "socket", "interrupteur", "switch", "lumière", "light", "électri"],
    "climatisation": ["clim", "ac", "thermostat", "ventilation", "fcu"],
    "menuiserie": ["porte", "door", "placard", "cabinet", "fenêtre", "window", "poignée"],
    "finitions": ["peinture", "paint", "carrelage", "tile", "joint", "rayure", "scratch", "fissure fine"],
}
SLA_JOURS = {"haute": 2, "moyenne": 7, "basse": 14}


def gravite_reserve(texte: str) -> str:
    t = (texte or "").lower()
    if any(m in t for m in ("fuite", "leak", "électrocution", "étincelle", "spark", "inond", "no power", "pas de courant")):
        return "haute"
    if any(m in t for m in ("ne ferme pas", "ne fonctionne pas", "not working", "cassé", "broken", "bloqué")):
        return "moyenne"
    return "basse"
