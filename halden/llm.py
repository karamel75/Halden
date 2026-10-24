"""Couche IA : comprendre (classer un message) et rédiger (brouillons).

Deux modes :
- « simulé » (par défaut) : classement par mots-clés et modèles de texte. Gratuit,
  reproductible, aucune donnée ne sort de la machine.
- « claude » : Claude via l'API Anthropic (ANTHROPIC_API_KEY) ou « bedrock » via
  Amazon Bedrock région UAE (me-central-1), cible d'hébergement du pilote.

Dans les deux cas l'IA reçoit les montants et les dates déjà calculés par le moteur
de règles ; les garde-fous rejettent tout brouillon qui contient un autre montant.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

MODEL = "claude-opus-5-5"
BEDROCK_MODEL = "anthropic.claude-opus-5-5"   # disponibilité en me-central-1 : à vérifier

CATEGORIES = {
    "FAQ_ECHEANCE": "question sur la prochaine échéance ou le montant dû",
    "FAQ_RELEVE": "demande de relevé de compte / statement / reçu",
    "FAQ_LIVRAISON": "question sur la date de livraison / handover",
    "FAQ_CHANTIER": "question sur l'avancement du chantier",
    "MODIFICATION": "demande de modification (finitions, options, plan)",
    "DIFFICULTE_PAIEMENT": "acheteur en difficulté, demande de report ou d'étalement",
    "ANNULATION_REMBOURSEMENT": "veut annuler, résilier ou être remboursé",
    "RECLAMATION": "plainte ou défaut signalé",
    "AUTRE": "autre",
}

MOTS_CLES = [
    ("ANNULATION_REMBOURSEMENT", ["cancel", "refund", "annul", "rembours", "terminate", "استرداد", "إلغاء"]),
    ("DIFFICULTE_PAIEMENT", ["postpone", "lost my job", "difficult", "report", "délai", "étaler",
                             "instal", "can't pay", "cannot pay", "تأجيل"]),
    ("MODIFICATION", ["change the", "modif", "upgrade", "finish", "option", "changer"]),
    ("FAQ_RELEVE", ["statement", "soa", "receipt", "relevé", "reçu", "كشف"]),
    ("FAQ_LIVRAISON", ["handover", "livraison", "completion date", "التسليم"]),
    ("FAQ_CHANTIER", ["progress", "construction", "chantier", "update", "avancement"]),
    ("FAQ_ECHEANCE", ["next payment", "due", "how much", "échéance", "combien", "الدفعة"]),
    ("RECLAMATION", ["complain", "plainte", "unacceptable", "inadmissible"]),
]


def detecter_langue(texte: str) -> str:
    if re.search(r"[؀-ۿ]", texte or ""):
        return "AR"
    t = (texte or "").lower()
    if any(w in t for w in (" je ", "bonjour", " le ", " la ", " mon ", "merci", "est-ce")):
        return "FR"
    return "EN"


@dataclass
class Classement:
    categorie: str
    langue: str
    resume: str


# --- Modèles de texte (mode simulé) -------------------------------------------------
T = {
    ("appel_de_fonds", "EN"): ("Payment request · {unite} · {jalon}",
        "Dear {nom},\n\nConstruction of {projet} has reached {jalon} (certificate {certificat}). "
        "In line with your payment plan, instalment {num} of {montant} is now due by {date_limite}.\n\n"
        "Please transfer to the project escrow account {escrow} quoting reference {ref}.\n\n"
        "Kind regards,\n{promoteur}"),
    ("appel_de_fonds", "FR"): ("Appel de fonds · {unite} · {jalon}",
        "Bonjour {nom},\n\nLe chantier de {projet} a atteint le jalon « {jalon} » (certificat {certificat}). "
        "Conformément à votre échéancier, l'échéance n°{num} de {montant} est exigible au {date_limite}.\n\n"
        "Merci d'effectuer le virement sur le compte escrow du projet {escrow} avec la référence {ref}.\n\n"
        "Bien cordialement,\n{promoteur}"),
    ("appel_de_fonds", "AR"): ("طلب دفعة · {unite}",
        "السيد/السيدة {nom}،\n\nوصل مشروع {projet} إلى مرحلة {jalon}. "
        "وفقاً لخطة الدفع، القسط رقم {num} بقيمة {montant} مستحق بتاريخ {date_limite}.\n"
        "يرجى التحويل إلى حساب الضمان {escrow} مع ذكر المرجع {ref}.\n\nمع التحية،\n{promoteur}"),
    ("relance_J+3", "EN"): ("Friendly reminder · {ref}",
        "Dear {nom},\n\nA quick reminder that instalment {num} for unit {unite} ({montant}) was due on "
        "{date_limite}. If you have already paid, please ignore this message or send us the transfer receipt.\n\n"
        "Kind regards,\n{promoteur}"),
    ("relance_J+3", "FR"): ("Petit rappel · {ref}",
        "Bonjour {nom},\n\nPetit rappel : l'échéance n°{num} de votre lot {unite} ({montant}) était due le "
        "{date_limite}. Si le virement est parti, ignorez ce message ou envoyez-nous l'avis de virement.\n\n"
        "Bien cordialement,\n{promoteur}"),
    ("relance_J+3", "AR"): ("تذكير ودي · {ref}",
        "السيد/السيدة {nom}،\n\nنذكركم بأن القسط رقم {num} للوحدة {unite} بقيمة {montant} كان مستحقاً بتاريخ "
        "{date_limite}. إذا تم الدفع، يرجى تجاهل هذه الرسالة.\n\nمع التحية،\n{promoteur}"),
    ("relance_J+10", "EN"): ("Second reminder · {ref}",
        "Dear {nom},\n\nOur records show that instalment {num} for unit {unite} remains unpaid "
        "({reste} outstanding, due {date_limite}, {retard} days ago). Please settle it within 7 days or "
        "contact your relationship manager so we can help.\n\nKind regards,\n{promoteur}"),
    ("relance_J+10", "FR"): ("Second rappel · {ref}",
        "Bonjour {nom},\n\nL'échéance n°{num} de votre lot {unite} reste impayée ({reste} restant dû, "
        "échue le {date_limite}, il y a {retard} jours). Merci de la régler sous 7 jours ou de contacter "
        "votre conseiller pour trouver une solution.\n\nBien cordialement,\n{promoteur}"),
    ("escalade", "FR"): ("Escalade J+30 · {nom}",
        "Acheteur : {nom} ({unite}). Reste dû : {reste} sur l'échéance n°{num}, échue le {date_limite} "
        "({retard} jours). Relances déjà faites : {relances}.\n\nDécision humaine attendue : appeler "
        "l'acheteur, proposer ou non un plan, ou lancer la procédure prévue au SPA (avocat). "
        "L'agent ne propose ni pénalité ni délai."),
    ("faq_echeance", "EN"): ("Your next instalment",
        "Dear {nom},\n\nYour next instalment for unit {unite} is n°{num} ({libelle}) of {montant}, "
        "{quand}. Payment reference: {ref}.\n\nKind regards,\n{promoteur}"),
    ("faq_echeance", "FR"): ("Votre prochaine échéance",
        "Bonjour {nom},\n\nVotre prochaine échéance pour le lot {unite} est la n°{num} ({libelle}) de "
        "{montant}, {quand}. Référence de paiement : {ref}.\n\nBien cordialement,\n{promoteur}"),
    ("faq_releve", "EN"): ("Your statement of account",
        "Dear {nom},\n\nPlease find your statement of account for unit {unite} attached. To date you have "
        "paid {paye} out of {prix}.\n\nKind regards,\n{promoteur}"),
    ("faq_livraison", "EN"): ("Expected handover",
        "Dear {nom},\n\nConstruction of {projet} is certified at {avancement}% and handover is currently "
        "planned for {livraison}. We will confirm the exact date with the completion notice.\n\n"
        "Kind regards,\n{promoteur}"),
    ("faq_livraison", "AR"): ("موعد التسليم المتوقع",
        "السيد/السيدة {nom}،\n\nنسبة الإنجاز المعتمدة لمشروع {projet} هي {avancement}٪، والتسليم مخطط له في "
        "{livraison}. سنؤكد التاريخ النهائي مع إشعار الإنجاز.\n\nمع التحية،\n{promoteur}"),
    ("faq_chantier", "EN"): ("Construction update",
        "Dear {nom},\n\n{projet} is certified at {avancement}% completion. Our monthly update with photos "
        "will follow shortly.\n\nKind regards,\n{promoteur}"),
    ("attente_humaine", "EN"): ("We have received your message",
        "Dear {nom},\n\nThank you for your message. A member of our team will call you personally within "
        "two working days.\n\nKind regards,\n{promoteur}"),
    ("attente_humaine", "FR"): ("Nous avons bien reçu votre message",
        "Bonjour {nom},\n\nMerci pour votre message. Un membre de notre équipe vous appellera "
        "personnellement sous deux jours ouvrés.\n\nBien cordialement,\n{promoteur}"),
    ("modification", "EN"): ("Your change request",
        "Dear {nom},\n\nThank you, we have logged your request: « {demande} ». Our technical team will check "
        "feasibility for unit {unite} and come back to you with a quote before anything is changed.\n\n"
        "Kind regards,\n{promoteur}"),
    ("actualite", "EN"): ("{projet} · monthly construction update",
        "Dear owners,\n\n{projet} has reached {jalon} (certificate {certificat}, {date}). Works completed this "
        "month: structure up to level {niveau}, MEP rough-in on lower floors, façade mock-up approved.\n\n"
        "Handover remains planned for {livraison}.\n\nKind regards,\n{promoteur}"),
    ("suivi_lead", "EN"): ("{projet} · a home that matches your search",
        "Dear {nom},\n\nThank you for your interest in {projet}. Unit {unite} ({type}, {surface} sq ft) "
        "is available at {prix} with our 60/40 payment plan. Would you like to book a visit of the show "
        "apartment this week?\n\nKind regards,\n{promoteur} sales team"),
    ("relance_spa", "EN"): ("Your Sale and Purchase Agreement",
        "Dear {nom},\n\nYour SPA for unit {unite} was sent on {date}. It still needs your signature so we "
        "can register your unit with Dubai Land Department (Oqood). Could you sign it this week?\n\n"
        "Kind regards,\n{promoteur}"),
    ("demande_kyc", "EN"): ("Missing documents for your file",
        "Dear {nom},\n\nTo complete your purchase file for unit {unite}, we still need: {pieces}. You can "
        "reply to this message with a photo or PDF.\n\nKind regards,\n{promoteur}"),
    ("accuse_garantie", "EN"): ("Warranty request received · {ref}",
        "Dear {nom},\n\nWe have logged your request « {demande} » under the {garantie} warranty. "
        "{sous_traitant} will contact you to schedule a visit within {sla} days.\n\nKind regards,\n{promoteur}"),
    ("refus_garantie", "EN"): ("Your request · {ref}",
        "Dear {nom},\n\nWe have reviewed your request « {demande} ». Your unit was handed over on {livraison} "
        "and the {garantie} warranty period has ended. We can still send a technician as a paid service "
        "if you wish.\n\nKind regards,\n{promoteur}"),
    ("ordre_reserve", "FR"): ("Réserve {ref} · {unite}",
        "À l'attention de {sous_traitant} : réserve « {description} » ({localisation}) sur le lot {unite}. "
        "Gravité {gravite}, levée attendue avant le {sla}."),
    ("note_rapprochement", "FR"): ("Rapprochement à valider",
        "Ligne {ligne} du {date} : {montant} de « {donneur} » (libellé : {libelle}).\n{explication}\n"
        "Proposition : affecter à {cible}."),
}


def _modele(kind: str, langue: str) -> tuple[str, str]:
    return T.get((kind, langue)) or T.get((kind, "EN")) or T[(kind, "FR")]


class LLM:
    def __init__(self, mode: str | None = None):
        self.mode = (mode or os.environ.get("HALDEN_LLM") or "simule").lower()
        self.client = None
        self.model = MODEL
        self.erreurs = 0
        try:
            if self.mode == "claude":
                import anthropic
                self.client = anthropic.Anthropic()
            elif self.mode == "bedrock":
                from anthropic import AnthropicBedrockMantle
                self.client = AnthropicBedrockMantle(aws_region=os.environ.get("AWS_REGION", "me-central-1"))
                self.model = BEDROCK_MODEL
        except Exception as e:  # SDK absent ou pas de clé : on reste en mode simulé
            print(f"[Halden] IA « {self.mode} » indisponible ({type(e).__name__}) : mode simulé.")
            self.mode, self.client = "simule", None

    @property
    def libelle(self) -> str:
        return {"claude": f"Claude ({MODEL})", "bedrock": f"Claude via Bedrock ({BEDROCK_MODEL})"}.get(
            self.mode, "simulé (mots-clés + modèles)")

    # -- comprendre ------------------------------------------------------------------
    def classer(self, texte: str) -> Classement:
        if self.client:
            try:
                return self._classer_claude(texte)
            except Exception:
                self.erreurs += 1
        langue = detecter_langue(texte)
        t = (texte or "").lower()
        for cat, mots in MOTS_CLES:
            if any(m in t for m in mots):
                return Classement(cat, langue, CATEGORIES[cat])
        return Classement("AUTRE", langue, CATEGORIES["AUTRE"])

    # -- rédiger -----------------------------------------------------------------------
    def rediger(self, kind: str, langue: str, ctx: dict) -> tuple[str, str]:
        objet, corps = _modele(kind, langue)
        brouillon = (objet.format(**ctx), corps.format(**ctx))
        if not self.client or kind in ("note_rapprochement", "escalade", "ordre_reserve"):
            return brouillon
        try:
            return self._rediger_claude(kind, langue, ctx, brouillon)
        except Exception:
            self.erreurs += 1
            return brouillon

    # -- Claude --------------------------------------------------------------------------
    SYSTEME = (
        "Tu es un agent du back office Halden, qui travaille pour un promoteur immobilier off-plan à Dubaï. "
        "Tu prépares des brouillons ; un humain ou un garde-fou décide de l'envoi. Règles strictes : "
        "n'invente jamais de montant, de date, de pourcentage ni d'engagement ; reprends à l'identique les "
        "montants fournis (format « AED 1,234.56 ») ; ne promets ni remise, ni délai, ni remboursement ; "
        "ton courtois, sobre et haut de gamme ; signe au nom du promoteur."
    )

    def _classer_claude(self, texte: str) -> Classement:
        from pydantic import BaseModel

        class Sortie(BaseModel):
            categorie: str
            langue: str
            resume: str

        cats = "\n".join(f"- {k} : {v}" for k, v in CATEGORIES.items())
        r = self.client.messages.parse(
            model=self.model, max_tokens=2000, system=self.SYSTEME,
            messages=[{"role": "user", "content":
                       f"Classe ce message d'acheteur dans une catégorie :\n{cats}\n\n"
                       f"langue = EN, AR ou FR. resume = une phrase en français.\n\nMessage :\n{texte}"}],
            output_format=Sortie)
        if r.stop_reason == "refusal" or r.parsed_output is None:
            raise RuntimeError("pas de sortie exploitable")
        s = r.parsed_output
        cat = s.categorie if s.categorie in CATEGORIES else "AUTRE"
        return Classement(cat, s.langue.upper()[:2], s.resume)

    def _rediger_claude(self, kind: str, langue: str, ctx: dict, modele: tuple[str, str]) -> tuple[str, str]:
        from pydantic import BaseModel

        class Brouillon(BaseModel):
            objet: str
            texte: str

        faits = json.dumps(ctx, ensure_ascii=False, default=str, indent=1)
        r = self.client.messages.parse(
            model=self.model, max_tokens=4000, system=self.SYSTEME,
            messages=[{"role": "user", "content":
                       f"Rédige un message de type « {kind} » en langue {langue}. Faits (seule source "
                       f"autorisée) :\n{faits}\n\nModèle de référence à améliorer sans ajouter de fait :\n"
                       f"Objet : {modele[0]}\n{modele[1]}"}],
            output_format=Brouillon)
        if r.stop_reason == "refusal" or r.parsed_output is None:
            raise RuntimeError("pas de sortie exploitable")
        return r.parsed_output.objet, r.parsed_output.texte
