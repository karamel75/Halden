"""Couche IA : comprendre (classer un message) et rédiger (brouillons).

Deux modes :
- « simulé » (par défaut) : classement par mots-clés et modèles de texte. Gratuit,
  reproductible, aucune donnée ne sort de la machine.
- « claude » : Claude via l'API Anthropic (ANTHROPIC_API_KEY) ou « bedrock » via
  Amazon Bedrock région UAE (me-central-1), cible d'hébergement du pilote.

Dans les deux cas l'IA reçoit les montants et les dates déjà calculés par le moteur
de règles ; les garde-fous rejettent tout brouillon qui contient un autre nombre.

Données : en mode Claude, les faits partent masqués (⟦nom⟧, ⟦montant⟧, ⟦ref⟧…) et sont
remis en place à la réception. Aucun nom, montant, IBAN ni téléphone d'acheteur ne sort.
Coût : chaque appel est compté (tokens d'entrée et de sortie) et chiffré par cycle.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

# Lettres à partir de modèles et classement de messages : le plus petit modèle suffit.
# Variable HALDEN_MODELE pour comparer (ex. claude-sonnet-5-5, claude-opus-5-5).
MODEL = os.environ.get("HALDEN_MODELE", "claude-haiku-5-5")
BEDROCK_MODEL = "anthropic." + MODEL           # disponibilité en me-central-1 : à vérifier
# Prix publics API Anthropic, USD par million de tokens (entrée, sortie), octobre 2026.
# Bedrock a sa propre grille : à vérifier avant de chiffrer le pilote.
PRIX_USD_MTOK = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.00, 10.00),
                 "claude-opus-5-5": (4.00, 20.00)}

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
    ("FAQ_ECHEANCE", ["next payment", "due", "how much", "balance", "outstanding", "échéance", "combien",
                      "solde", "reste à payer", "الدفعة", "رصيد", "المبلغ المتبقي"]),
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
        "Dear {nom},\n\nA quick reminder that the following instalment is now due:\n{detail}\n\n"
        "If you have already paid, please ignore this message or send us the transfer receipt.\n\n"
        "Kind regards,\n{promoteur}"),
    ("relance_J+3", "FR"): ("Petit rappel · {ref}",
        "Bonjour {nom},\n\nPetit rappel : l'échéance suivante est arrivée à terme :\n{detail}\n\n"
        "Si le virement est parti, ignorez ce message ou envoyez-nous l'avis de virement.\n\n"
        "Bien cordialement,\n{promoteur}"),
    ("relance_J+3", "AR"): ("تذكير ودي · {ref}",
        "السيد/السيدة {nom}،\n\nنود تذكيركم بأن القسط التالي أصبح مستحقاً:\n{detail}\n\n"
        "إذا تم الدفع، يرجى تجاهل هذه الرسالة أو إرسال إشعار التحويل.\n\nمع التحية،\n{promoteur}"),
    ("relance_J+10", "EN"): ("Second reminder · {ref}",
        "Dear {nom},\n\nOur records show that the following instalment remains unpaid:\n{detail}\n\n"
        "Total outstanding: {reste}. Please settle it within 7 days, or contact your relationship manager "
        "so we can help. If you have already paid, please send us the transfer receipt.\n\n"
        "Kind regards,\n{promoteur}"),
    ("relance_J+10", "FR"): ("Second rappel · {ref}",
        "Bonjour {nom},\n\nL'échéance suivante reste impayée :\n{detail}\n\nTotal restant dû : {reste}. "
        "Merci de la régler sous 7 jours ou de contacter votre conseiller pour trouver une solution. "
        "Si le virement est parti, envoyez-nous l'avis de virement.\n\nBien cordialement,\n{promoteur}"),
    ("relance_J+10", "AR"): ("تذكير ثانٍ · {ref}",
        "السيد/السيدة {nom}،\n\nتشير سجلاتنا إلى أن القسط التالي لم يُسدَّد بعد:\n{detail}\n\n"
        "إجمالي المبلغ المستحق: {reste}. يرجى السداد خلال 7 أيام أو التواصل مع مدير علاقتكم لمساعدتكم. "
        "إذا تم الدفع، يرجى إرسال إشعار التحويل.\n\nمع التحية،\n{promoteur}"),
    ("escalade", "FR"): ("Escalade J+30 · {nom}",
        "Acheteur : {nom} ({unite}). Reste dû : {reste} sur l'échéance n°{num}, échue le {date_limite} "
        "({retard} jours). Relances déjà faites : {relances}.\n\nDécision humaine attendue : appeler "
        "l'acheteur, proposer ou non un plan, ou engager la procédure de défaut de Dubaï :\n{procedure}\n\n"
        "Toutes les relances automatiques de cet acheteur sont suspendues jusqu'à décision. "
        "L'agent ne propose ni pénalité ni délai."),
    ("faq_echeance", "EN"): ("Your next instalment",
        "Dear {nom},\n\nYour next instalment for unit {unite} is n°{num} ({libelle}) of {montant}, "
        "{quand}. Payment reference: {ref}.\n\nKind regards,\n{promoteur}"),
    ("faq_echeance", "FR"): ("Votre prochaine échéance",
        "Bonjour {nom},\n\nVotre prochaine échéance pour le lot {unite} est la n°{num} ({libelle}) de "
        "{montant}, {quand}. Référence de paiement : {ref}.\n\nBien cordialement,\n{promoteur}"),
    ("faq_echeance", "AR"): ("قسطكم القادم",
        "السيد/السيدة {nom}،\n\nالقسط القادم للوحدة {unite} هو رقم {num} ({libelle}) بقيمة {montant}، "
        "{quand}. مرجع الدفع: {ref}.\n\nمع التحية،\n{promoteur}"),
    ("faq_releve", "FR"): ("Votre relevé de compte",
        "Bonjour {nom},\n\nVous trouverez ci-joint le relevé de compte de votre lot {unite}. À ce jour, vous "
        "avez réglé {paye} sur {prix}.\n\nBien cordialement,\n{promoteur}"),
    ("faq_releve", "AR"): ("كشف حسابكم",
        "السيد/السيدة {nom}،\n\nمرفق كشف حساب الوحدة {unite}. حتى تاريخه، تم سداد {paye} من أصل {prix}.\n\n"
        "مع التحية،\n{promoteur}"),
    ("faq_chantier", "AR"): ("آخر مستجدات البناء",
        "السيد/السيدة {nom}،\n\nنسبة الإنجاز المعتمدة لمشروع {projet} هي {avancement}٪. "
        "سنرسل لكم قريباً التحديث الشهري مع الصور.\n\nمع التحية،\n{promoteur}"),
    ("attente_humaine", "AR"): ("تم استلام رسالتكم",
        "السيد/السيدة {nom}،\n\nشكراً على رسالتكم. سيتصل بكم أحد أعضاء فريقنا شخصياً خلال يومي عمل.\n\n"
        "مع التحية،\n{promoteur}"),
    ("modification", "AR"): ("طلب التعديل",
        "السيد/السيدة {nom}،\n\nشكراً، تم تسجيل طلبكم: « {demande} ». سيدرس فريقنا الفني إمكانية التنفيذ "
        "للوحدة {unite} ويعود إليكم بعرض سعر قبل أي تغيير.\n\nمع التحية،\n{promoteur}"),
    ("demande_kyc", "AR"): ("مستندات ناقصة في ملفكم",
        "السيد/السيدة {nom}،\n\nلاستكمال ملف شراء الوحدة {unite}، ما زلنا بحاجة إلى: {pieces}. "
        "يمكنكم الرد على هذه الرسالة بصورة أو ملف PDF.\n\nمع التحية،\n{promoteur}"),
    ("accuse_garantie", "AR"): ("تم استلام طلب الضمان · {ref}",
        "السيد/السيدة {nom}،\n\nتم تسجيل طلبكم « {demande} » ضمن ضمان {garantie}. "
        "ستتواصل معكم شركة {sous_traitant} لتحديد موعد الزيارة خلال {sla} أيام.\n\nمع التحية،\n{promoteur}"),
    ("refus_garantie", "AR"): ("طلبكم · {ref}",
        "السيد/السيدة {nom}،\n\nراجعنا طلبكم « {demande} ». تم تسليم وحدتكم بتاريخ {livraison} وقد انتهت مدة "
        "ضمان {garantie}. يمكننا إرسال فني كخدمة مدفوعة إذا رغبتم.\n\nمع التحية،\n{promoteur}"),
    ("relance_spa", "AR"): ("عقد البيع والشراء",
        "السيد/السيدة {nom}،\n\nأُرسل إليكم عقد البيع والشراء للوحدة {unite} بتاريخ {date}. ما زال العقد بحاجة "
        "إلى توقيعكم لتسجيل الوحدة لدى دائرة الأراضي والأملاك في دبي (أوقود). هل يمكنكم توقيعه هذا الأسبوع؟\n\n"
        "مع التحية،\n{promoteur}"),
    ("verification_expediteur", "EN"): ("About your message",
        "Hello,\n\nThank you for your message. For the security of our buyers, we can only share account "
        "details with the registered owner, from their registered contact. A member of our team will get "
        "in touch with the owner directly.\n\nKind regards,\n{promoteur}"),
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


CHAMP_RE = re.compile(r"\{[^{}]*\}")
_PERSO_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\+?\d[\d\s-]{6,}\d|AE\d{2}(?:\s?\d{4}){4,5}(?:\s?\d{1,3})?")


def masquer_texte(texte: str, noms: list[str] = ()) -> str:
    """Retire d'un message libre les e-mails, téléphones, IBAN, longs nombres et noms connus."""
    t = _PERSO_RE.sub("⟦donnée⟧", texte or "")
    for n in noms:
        for part in [n] + [p for p in n.split() if len(p) > 3]:
            t = re.sub(re.escape(part), "⟦nom⟧", t, flags=re.I)
    return t


class LLM:
    def __init__(self, mode: str | None = None):
        self.mode = (mode or os.environ.get("HALDEN_LLM") or "simule").lower()
        self.client = None
        self.model = MODEL
        self.erreurs = 0
        self.journal: list[str] = []     # chaque repli vers le mode simulé, avec sa cause
        self.usage = {"appels": 0, "entree": 0, "sortie": 0}
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

    def texte_fixe(self, kind: str, langue: str) -> str:
        """Texte du modèle sans ses champs : les nombres qu'il contient (« 7 jours ») sont autorisés."""
        return CHAMP_RE.sub(" ", " ".join(_modele(kind, langue)))

    def cout_usd(self) -> float:
        pin, pout = PRIX_USD_MTOK.get(MODEL, (0.0, 0.0))
        return round((self.usage["entree"] * pin + self.usage["sortie"] * pout) / 1e6, 4)

    def _compter(self, r) -> None:
        u = getattr(r, "usage", None)
        self.usage["appels"] += 1
        if u is not None:
            self.usage["entree"] += int(getattr(u, "input_tokens", 0) or 0)
            self.usage["sortie"] += int(getattr(u, "output_tokens", 0) or 0)

    def _echec(self, quoi: str, e: Exception) -> None:
        self.erreurs += 1
        self.journal.append(f"{quoi} : {type(e).__name__}")

    # -- comprendre ------------------------------------------------------------------
    def classer(self, texte: str, noms: list[str] = ()) -> Classement:
        if self.client:
            try:
                return self._classer_claude(masquer_texte(texte, noms))
            except Exception as e:
                self._echec("classement", e)
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
            return self._rediger_claude(kind, langue, ctx)
        except Exception as e:
            self._echec(f"rédaction {kind}", e)
            return brouillon

    # -- Claude --------------------------------------------------------------------------
    SYSTEME = (
        "Tu es un agent du back office Halden, qui travaille pour un promoteur immobilier off-plan à Dubaï. "
        "Tu prépares des brouillons ; un humain ou un garde-fou décide de l'envoi. Règles strictes : "
        "n'invente jamais de montant, de date, de pourcentage ni d'engagement ; reprends à l'identique les "
        "montants fournis (format « AED 1,234.56 ») ; ne promets ni remise, ni délai, ni remboursement ; "
        "ton courtois, sobre et haut de gamme ; signe au nom du promoteur. Les faits te sont donnés sous "
        "forme de marqueurs ⟦champ⟧ : recopie chaque marqueur tel quel, sans le traduire ni l'inventer."
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
        self._compter(r)
        if r.stop_reason == "refusal" or r.parsed_output is None:
            raise RuntimeError("pas de sortie exploitable")
        s = r.parsed_output
        cat = s.categorie if s.categorie in CATEGORIES else "AUTRE"
        return Classement(cat, s.langue.upper()[:2], s.resume)

    def _rediger_claude(self, kind: str, langue: str, ctx: dict) -> tuple[str, str]:
        from pydantic import BaseModel

        class Brouillon(BaseModel):
            objet: str
            texte: str

        # Masquage : Claude voit ⟦nom⟧, ⟦montant⟧… jamais les valeurs.
        marqueurs = {k: f"⟦{k}⟧" for k, v in ctx.items() if isinstance(v, (str, int, float)) or v is None}
        objet_m, corps_m = (CHAMP_RE.sub(lambda m: marqueurs.get(m.group(0)[1:-1], m.group(0)), x)
                            for x in _modele(kind, langue))
        r = self.client.messages.parse(
            model=self.model, max_tokens=2000, system=self.SYSTEME,
            messages=[{"role": "user", "content":
                       f"Rédige un message de type « {kind} » en langue {langue}. Champs disponibles : "
                       f"{', '.join(marqueurs.values())}.\n\nModèle de référence à améliorer sans ajouter de "
                       f"fait :\nObjet : {objet_m}\n{corps_m}"}],
            output_format=Brouillon)
        self._compter(r)
        if r.stop_reason == "refusal" or r.parsed_output is None:
            raise RuntimeError("pas de sortie exploitable")

        def remettre(t: str) -> str:
            for k, m in marqueurs.items():
                t = t.replace(m, str(ctx[k]))
            if "⟦" in t:
                raise RuntimeError("marqueur inconnu dans la réponse")
            return t
        return remettre(r.parsed_output.objet), remettre(r.parsed_output.texte)
