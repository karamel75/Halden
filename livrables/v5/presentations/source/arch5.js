// Halden architecture note v5: the review of 24 Oct 2026 applied (approval rule, sensitivity, data markers, AI cost, pilot scope)
const L = require("./lib5");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const { HEX, MX, CW, T } = L;
const GRILLE = require("./grille.json");

const SOFT = "C8CFDA";
const th = (t, fill) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: fill || HEX.navy }, fontSize: 9, valign: "middle" } });
const td = (t, o) => ({ text: String(t), options: Object.assign({ fontSize: 9, color: HEX.black, fill: { color: HEX.grey }, valign: "middle" }, o || {}) });
const fitW = (o) => (o.colW ? Object.assign({}, o, { colW: o.colW.map((c) => c * (o.w || CW) / o.colW.reduce((a, b) => a + b, 0)) }) : o);
const tableOpts = (o) => Object.assign({ x: MX, y: 1.75, w: CW, border: { type: "solid", pt: 2, color: HEX.white }, fontFace: L.F, margin: [0.03, 0.08, 0.03, 0.08] }, fitW(o));
const INTERNE = "Proposition de l'équipe Halden ; règles appliquées dans le POC Halden v0.2";
const PILOTE = new Set(["T01", "T02", "T05", "T06", "T10", "T12", "T15"]);
const SHORT = { AUTONOME: "autonome", VALIDATION: "validation", "RÈGLE": "règle", HUMAIN: "humain", AUCUN: "pas d'agent" };
const LIB = { AUTONOME: "Agent autonome", VALIDATION: "Agent + validation", "RÈGLE": "Règle (pas d'IA)", HUMAIN: "Humain décide", AUCUN: "Pas d'agent" };

function cols(s, items, y, h, o) {
  o = o || {};
  const n = items.length, w = (CW - (n - 1) * 0.3) / n;
  items.forEach(([head, body], i) => {
    const x = MX + i * (w + 0.3);
    s.addText(head, T({ x, y, w, h: 0.4, fontSize: o.hs || 13, bold: true, color: i === o.hot ? HEX.teal : HEX.navy }));
    s.addShape("line", { x, y: y + 0.48, w: 0.5, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(body, T({ x, y: y + 0.62, w: w - 0.1, h: h - 0.62, fontSize: o.bs || 10.5, color: HEX.black, lineSpacingMultiple: 1.05 }));
  });
}

async function build(out) {
  const { pres, K } = await L.newPres("Halden : note d'architecture");
  const S = "Synthèse", A = "Comment ça marche", G = "Les agents et la grille", H = "Hébergement, coût, intégrations";

  pres.addSection({ title: S });
  L.cover(pres, S, { title: "Halden : architecture agentique, hébergement et intégrations",
    subtitle: "Comment le moteur fonctionne, où il tourne, ce qu'il coûte et pourquoi chaque tâche est confiée ou non à un agent",
    meta: "Note d'architecture · usage interne · octobre 2026" });

  // Synthesis: the same rule as everywhere else
  let s = L.content(pres, S, { subtitle: "Synthèse",
    title: "Halden est un moteur d'agents encadrés : pendant le pilote, chaque message vers un acheteur passe par une personne",
    source: INTERNE + ". Règle identique dans le site, le dossier, la présentation client, l'atlas BPMN et le code" });
  L.colHead(s, K, "Étape", MX, 1.6, 2.6);
  L.colHead(s, K, "Constat", MX + 2.8, 1.6, CW - 2.8);
  [["Situation", "Après une vente sur plan, le back-office gère environ 30 mois d'appels de fonds, de rapprochements, de relances et de dossiers escrow."],
    ["Complication", "Données sensibles (identités, IBAN), règles par pays (PDPL), et une erreur de montant ou une relance à un acheteur qui a payé peut coûter le client."],
    ["Résolution", "L'IA comprend et rédige, les règles calculent, une personne valide chaque message vers un acheteur et décide de chaque engagement. Pilote : un agent (encaissements), une instance aux EAU."]].forEach(([a, b], i) => {
    const y = 2.15 + i * 1.05;
    s.addText(a, T({ x: MX, y, w: 2.6, h: 0.9, valign: "middle", fontSize: 14, bold: true, color: i === 2 ? HEX.teal : HEX.navy }));
    s.addText(b, T({ x: MX + 2.8, y, w: CW - 2.8, h: 0.9, valign: "middle", fontSize: 11, color: HEX.black }));
    s.addShape("line", { x: MX, y: y + 0.97, w: CW, h: 0, line: { color: HEX.line, width: 0.5 } });
  });
  s.addShape("rect", { x: MX, y: 5.5, w: CW, h: 1.15, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Décision attendue : ", options: { bold: true, color: HEX.sky } },
    { text: "valider l'architecture du pilote (AWS Émirats, fichiers, portail d'approbation, marqueurs à la place des noms avant l'IA) et faire noter la grille de décision par un directeur financier en entretien.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.5, w: CW - 0.6, h: 1.15, valign: "middle", fontSize: 12 }));

  // Key points
  s = L.content(pres, S, { subtitle: "Points clés", title: "Quatre principes structurent l'architecture, du rôle de l'IA aux intégrations", source: INTERNE });
  const kp = [["01", "Trois rôles séparés", "L'IA comprend et rédige. Le moteur de règles calcule. Une personne valide et engage le promoteur."],
    ["02", "Agentifier par critères", "Une grille de sept critères, une ligne de sensibilité à ±1 et des planchers par tâche. Notée par l'équipe : à refaire avec un directeur financier."],
    ["03", "Une seule instance d'abord", "AWS Émirats pour le pilote. Une instance par pays seulement quand un deuxième pays a un client."],
    ["04", "Fichiers d'abord", "CSV et MT940 lus aujourd'hui ; PDF exporté en CSV par la banque. Open Finance, WhatsApp et DLD viennent après la preuve."]];
  const kw = (CW - 0.9) / 4;
  kp.forEach(([n, h, b], i) => {
    const x = MX + i * (kw + 0.3);
    s.addShape("rect", { x, y: 1.75, w: kw, h: 1.0, fill: { color: i === 0 ? HEX.teal : HEX.navy }, line: { type: "none" } });
    s.addText(n, T({ x: x + 0.2, y: 1.75, w: 0.7, h: 1.0, valign: "middle", fontSize: 22, color: HEX.white }));
    s.addText(h, T({ x: x + 0.9, y: 1.75, w: kw - 1.0, h: 1.0, valign: "middle", fontSize: 12, bold: true, color: HEX.white }));
    s.addShape("rect", { x, y: 2.85, w: kw, h: 3.8, fill: { color: HEX.grey }, line: { type: "none" } });
    s.addText(b, T({ x: x + 0.2, y: 3.0, w: kw - 0.4, h: 3.5, fontSize: 11, color: HEX.black, lineSpacingMultiple: 1.1 }));
  });

  // Mapping as layers
  pres.addSection({ title: A });
  s = L.content(pres, A, { subtitle: "Mapping de l'architecture",
    title: "Les données entrent par fichiers, sont traitées aux Émirats, et seuls des marqueurs anonymes partent vers le modèle d'IA",
    source: "Sources : AWS, inférence inter-régions de Claude depuis les régions du Moyen-Orient (24 février 2026) ; POC Halden v0.2 (llm.py : masquage). P pilote, E ensuite, V vision" });
  const colW3 = [3.2, CW - 6.8, 3.0];
  const x2 = MX + colW3[0] + 0.3, x3 = x2 + colW3[1] + 0.3;
  s.addShape("rect", { x: MX, y: 1.75, w: colW3[0], h: 4.9, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addShape("rect", { x: x2, y: 1.75, w: colW3[1], h: 4.9, fill: { color: "FBFAF7" }, line: { color: HEX.teal, width: 1, dashType: "dash" } });
  s.addShape("rect", { x: x3, y: 1.75, w: colW3[2], h: 4.9, fill: { color: HEX.grey }, line: { type: "none" } });
  const head = (t, x, w, c) => s.addText(t, T({ x: x + 0.15, y: 1.85, w: w - 0.3, h: 0.3, fontSize: 9, bold: true, charSpacing: 1.5, color: c || HEX.text2 }));
  head("ENTRÉES · LE PROMOTEUR", MX, colW3[0]); head("HALDEN · RÉGION AWS ÉMIRATS (ME-CENTRAL-1)", x2, colW3[1], HEX.blue); head("SORTIES · HUMAINS ET TIERS", x3, colW3[2]);
  const list = (x, w, y, items) => s.addText(items.map(([t, p], i) => ({ text: `${t}  ·  ${p}`, options: { breakLine: i < items.length - 1, paraSpaceAfter: 5 } })),
    T({ x: x + 0.15, y, w: w - 0.3, h: 4.3, fontSize: 9.5, color: HEX.black }));
  list(MX, colW3[0], 2.25, [["Plans de paiement et acheteurs (Excel)", "P"], ["Relevé escrow CSV ou MT940", "P"], ["Certificat de jalon (PDF)", "P"], ["Messages acheteurs (e-mail)", "P"],
    ["Open Finance EAU via un TPP agréé", "E"], ["WhatsApp Business entrant", "E"], ["DLD API Gateway (Oqood, escrow)", "V"], ["ERP du promoteur (lecture)", "V"]]);
  const layers = [["1 · Ingestion", "Lire, normaliser, dédoublonner sur le contenu ; crédits et débits"], ["2 · Orchestration", "Route chaque événement ; une seule conversation par acheteur et par cycle"],
    ["3 · Agent encaissements", "Appels, rapprochements, brouillons de relance ; les autres agents sont la vision"], ["4 · Garde-fous", "Montants par règles ; signaux qui suspendent ; chaque message acheteur validé"],
    ["5 · Socle", "Dossier acheteur, pack pays en tables, journal d'audit signé, documents"]];
  layers.forEach(([h, b], i) => {
    const y = 2.25 + i * 0.62;
    s.addShape("rect", { x: x2 + 0.15, y, w: colW3[1] - 0.3, h: 0.54, fill: { color: HEX.white }, line: { color: HEX.line, width: 0.5 } });
    s.addText([{ text: h + "   ", options: { bold: true, color: HEX.navy } }, { text: b }], T({ x: x2 + 0.3, y, w: colW3[1] - 0.6, h: 0.54, valign: "middle", fontSize: 9.5, color: HEX.black }));
  });
  s.addShape("rect", { x: x2 + 0.15, y: 5.4, w: colW3[1] - 0.3, h: 1.1, fill: { color: HEX.white }, line: { color: HEX.red, width: 1, dashType: "dash" } });
  s.addText([{ text: "FRONTIÈRE DU MODÈLE D'IA  ", options: { bold: true, color: HEX.red } },
    { text: "Claude via Bedrock : l'inférence peut être traitée hors des EAU. Avant chaque appel, noms, téléphones et IBAN deviennent des marqueurs (⟦nom⟧) ; les vraies valeurs sont remises après, dans la région. À valider par un juriste avant toute donnée réelle." }],
    T({ x: x2 + 0.3, y: 5.4, w: colW3[1] - 0.6, h: 1.1, valign: "middle", fontSize: 9.5, color: HEX.black }));
  list(x3, colW3[2], 2.25, [["File d'approbation (portail)", "P"], ["Vue du matin du directeur financier", "P"], ["Comparaison shadow ligne à ligne", "P"],
    ["E-mail au nom du promoteur, après validation", "E"], ["WhatsApp, modèles approuvés par Meta", "E"], ["Dossier escrow pour chaque libération", "E"]]);
  s.addText("L'argent ne passe jamais par Halden : acheteur → compte escrow du projet.", T({ x: x3 + 0.15, y: 5.9, w: colW3[2] - 0.3, h: 0.6, fontSize: 9.5, italic: true, color: HEX.teal }));

  // Milestone path, readable at slide size; the full BPMN lives in the atlas
  s = L.content(pres, A, { subtitle: "Le trajet d'un jalon",
    title: "Un jalon déclenche un sous-processus par acheteur ; chaque message attend une validation, et tout s'arrête au premier signal",
    source: "Diagramme BPMN complet et validé : Atlas des processus Halden (EN), vue To-Be encaissements. Libération escrow : loi de Dubaï n° 8 de 2007" });
  const steps = [["1 · Jalon certifié", "Par l'ingénieur du site ; rien ne démarre sans lui.", 0], ["2 · Calcul", "Les règles calculent l'échéance de chaque acheteur.", 0],
    ["3 · Brouillons", "L'IA rédige dans la langue de l'acheteur, sur marqueurs.", 0], ["4 · Validation", "La finance valide le lot ; montants recontrôlés.", 1],
    ["5 · Rapprochement", "Exact si référence, payeur et montant concordent ; sinon en file.", 0], ["6 · Relances", "J+3 et J+10 préparées, validées, jamais si un paiement attend.", 1],
    ["7 · J+30", "Le dossier part à un humain ; procédure de défaut DLD préparée.", 1], ["8 · Libération escrow", "Dossier prêt pour la demande de libération au jalon suivant.", 0]];
  const sw = (CW - 0.9) / 4;
  steps.forEach(([h, b, hum], i) => {
    const x = MX + (i % 4) * (sw + 0.3), y = 1.8 + Math.floor(i / 4) * 1.75;
    s.addShape("rect", { x, y, w: sw, h: 1.55, fill: { color: hum ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(h, T({ x: x + 0.2, y: y + 0.15, w: sw - 0.4, h: 0.4, fontSize: 12, bold: true, color: hum ? HEX.sky : HEX.navy }));
    s.addText(b, T({ x: x + 0.2, y: y + 0.6, w: sw - 0.4, h: 0.85, fontSize: 10, color: hum ? HEX.white : HEX.black }));
  });
  s.addShape("rect", { x: MX, y: 5.4, w: CW, h: 1.2, fill: { color: HEX.white }, line: { color: HEX.teal, width: 1 } });
  s.addText([{ text: "Ce qui interrompt tout, à n'importe quelle étape : ", options: { bold: true, color: HEX.teal } },
    { text: "« j'ai payé », avocat, réclamation, difficulté, un virement non identifié du même montant, ou un dossier repris par un humain. Les relances de cet acheteur s'arrêtent ; elles ne reprennent que sur décision humaine (commande « reactiver » du POC)." }],
    T({ x: MX + 0.25, y: 5.4, w: CW - 0.5, h: 1.2, valign: "middle", fontSize: 10.5, color: HEX.black }));

  // Three roles
  s = L.dark(pres, A, { subtitle: "Les trois rôles", title: "Chaque responsabilité a un seul propriétaire : l'IA comprend, la règle calcule, la personne valide et engage", source: INTERNE });
  [["L'IA", "Comprend et rédige", ["Lit les messages, PDF et références floues", "Rédige sur des marqueurs, jamais sur les vrais noms", "Propose un rapprochement avec sa raison", "Ne calcule jamais un montant"]],
    ["La règle", "Calcule et contrôle", ["Échéances depuis le plan de paiement", "Montants recontrôlés dans toute écriture", "Plafonds et délais du pack pays, relus par un juriste", "Résultat reproductible et testé"]],
    ["La personne", "Valide et engage", ["Valide chaque message vers un acheteur", "Signe : l'IA ne signe jamais", "Tranche les exceptions et le défaut", "Réactive un acheteur suspendu"]]].forEach(([n, h, items], i) => {
    const w = (CW - 0.6) / 3, x = MX + i * (w + 0.3);
    s.addText(n.toUpperCase(), T({ x, y: 1.8, w, h: 0.3, fontSize: 9, bold: true, charSpacing: 2.5, color: HEX.sky }));
    s.addText(h, T({ x, y: 2.15, w, h: 0.7, valign: "middle", fontSize: 24, bold: true, color: HEX.white }));
    s.addShape("line", { x, y: 3.0, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(items.map((t, j) => ({ text: t, options: { bullet: { code: "2014", indent: 12 }, breakLine: j < items.length - 1, paraSpaceAfter: 8 } })),
      T({ x, y: 3.2, w: w - 0.2, h: 3.0, fontSize: 11.5, color: SOFT }));
  });

  // Agents
  pres.addSection({ title: G });
  s = L.content(pres, G, { subtitle: "Fiches des agents",
    title: "Le pilote ne construit qu'un agent, les encaissements ; les cinq autres restent une vision tant qu'il n'est pas prouvé",
    source: INTERNE + ". Dans le POC, les agents de la vision ne tournent qu'avec « demo --vision »" });
  s.addTable([
    [th("Agent"), th("Fait seul"), th("Prépare, une personne valide"), th("Mesure"), th("Périmètre")],
    [td("Orchestrateur", { bold: true, color: HEX.navy }), td("Route les événements ; une conversation par acheteur ; retire les relances en conflit"), td("Rien : ne parle jamais à un acheteur"), td("Événements routés sans erreur"), td("Pilote", { bold: true, color: HEX.teal })],
    [td("Encaissements", { bold: true, color: HEX.navy }), td("Rapprochement exact (référence, payeur, montant) ; détection des signaux qui suspendent"), td("Chaque appel et chaque relance ; rapprochements incertains ; virements rejetés ; plan en difficulté ; dossier de défaut DLD"), td("Temps d'équipe par jalon ; part rapprochée sans humain ; 0 faux rapprochement"), td("Pilote", { bold: true, color: HEX.teal })],
    [td("Relation acheteur", { bold: true, color: HEX.navy }), td("Vérifie l'expéditeur ; suspend sur signal"), td("Chaque réponse ; chaque modification et son prix"), td("Messages traités, signaux remontés"), td("Vision")],
    [td("Livraison et réserves", { bold: true, color: HEX.navy }), td("Trie et affecte les réserves"), td("Le procès-verbal ; les réserves contestées"), td("Réserves ouvertes à 30 et 90 jours"), td("Vision")],
    [td("Contrat", { bold: true, color: HEX.navy }), td("Liste les pièces manquantes"), td("Dossier Oqood et SPA ; la signature reste humaine"), td("Jours jusqu'à l'enregistrement"), td("Vision")],
    [td("Garantie, ventes", { bold: true, color: HEX.navy }), td("Identifie la garantie applicable (règle)"), td("Toute réponse ; responsabilité, remises, réservation"), td("Jours par sinistre ; délai de réponse"), td("Vision")],
  ], tableOpts({ y: 1.75, colW: [2.0, 3.4, 3.6, 2.4, 1.1], rowH: [0.36, 0.62, 0.82, 0.55, 0.55, 0.55, 0.55] }));

  // Criteria grid
  s = L.content(pres, G, { subtitle: "Grille de critères",
    title: "Sept critères notés de 1 à 5 proposent agent, règle ou humain ; des planchers et la règle du pilote ne peuvent que durcir",
    source: "Grille proposée par l'équipe Halden, poids égaux. À noter avec un directeur financier en entretien ; les notes actuelles sont les nôtres" });
  s.addTable([
    [th("Axe"), th("Critère"), th("La question"), th("1 ="), th("5 =")],
    ...[["Valeur", "V1 · Volume", "Combien de fois la tâche revient-elle ?", "Quelques fois par an", "Des centaines de fois par jalon"],
      ["Valeur", "V2 · Temps équipe", "Combien d'heures l'équipe y passe-t-elle ?", "Quelques minutes", "Des jours par jalon"],
      ["Valeur", "V3 · Impact", "Que gagne le directeur financier ?", "Confort", "Moins de retards, erreurs évitées"],
      ["Complexité", "C1 · Ambiguïté", "Les données sont-elles floues ?", "Structurées, exactes", "Texte libre, références fausses"],
      ["Complexité", "C2 · Conséquence", "Une erreur touche-t-elle argent, droit ou relation acheteur ?", "Interne, corrigible", "Irréversible ou juridique"],
      ["Complexité", "C3 · Intégration", "Les données sont-elles accessibles ?", "Un fichier suffit", "Connecteur, licence, tiers"],
      ["Complexité", "C4 · Jugement", "Faut-il négocier, arbitrer, rassurer ?", "Aucun jugement", "Arbitrage ou relation sensible"]].map((r) => r.map((c, j) => td(c, j < 2 ? { bold: true, color: HEX.navy } : {}))),
  ], tableOpts({ y: 1.75, colW: [1.4, 2.1, 4.0, 2.2, 2.4], rowH: [0.34, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42] }));
  s.addShape("rect", { x: MX, y: 5.35, w: CW, h: 1.3, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Règle de lecture. ", options: { bold: true, color: HEX.sky } },
    { text: "La grille propose ; un plancher par tâche et la règle du pilote ne peuvent que rendre plus strict. Règle du pilote : tout message vers un acheteur est validé, quelle que soit la note. Une relance à un acheteur qui a payé n'est pas rattrapable : C2 = 4.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.35, w: CW - 0.6, h: 1.3, valign: "middle", fontSize: 11 }));

  // Scored tasks with sensitivity
  const nb = (k) => GRILLE.filter((r) => r[14] === k).length;
  s = L.content(pres, G, { subtitle: "Notation des tâches et sensibilité",
    title: `Sur ${GRILLE.length} tâches, ${nb("HUMAIN")} restent humaines, ${nb("RÈGLE")} sont des règles, ${nb("VALIDATION")} sont validées ; seules ${nb("AUTONOME")} tâches internes sont autonomes`,
    source: "Calculé par le POC Halden v0.2 (rules.niveau_grille, guardrails.PLANCHERS, rules.sensibilite). Notes de l'équipe, à refaire avec un directeur financier" });
  L.sticker(s, K, "HYPOTHÈSE");
  s.addTable([
    [th("Tâche"), th("V"), th("C"), th("Grille"), th("Plancher"), th("Décision"), th("Bascule si une note bouge de ±1"), th("Phase")],
    ...GRILLE.map((r) => [td(r[1]), td(r[10], { align: "center" }), td(r[11], { align: "center" }), td(SHORT[r[12]] || r[12]), td(r[13] ? SHORT[r[13]] : "—"),
      td(LIB[r[14]] || r[14], { bold: true, color: r[14] === "AUTONOME" ? HEX.teal : HEX.navy }), td(r[15].replace(/AUCUN AGENT/g, "AUCUN").replace(/ → (\S+)/g, (m, k) => " → " + (SHORT[k] || k)).replace("stable à ±1", "stable")),
      td(PILOTE.has(r[0]) ? "Pilote" : "Vision", PILOTE.has(r[0]) ? { bold: true, color: HEX.teal } : {})]),
  ], tableOpts({ y: 1.7, colW: [3.3, 0.4, 0.4, 0.95, 0.95, 1.55, 4.3, 0.75], rowH: [0.28, ...GRILLE.map(() => 0.25)] }));

  // Decision tree
  s = L.content(pres, G, { subtitle: "Arbre de décision",
    title: "Cinq questions, dans cet ordre, disent si une tâche devient une règle, un agent autonome, un agent validé ou reste humaine",
    source: INTERNE });
  const qs = [["1", "Revient-elle souvent ?", "Non → pas d'agent : règle simple ou humain"], ["2", "Peut-on l'écrire comme une règle exacte ?", "Oui → règle, pas d'IA (calcul des échéances, lettrage exact)"],
    ["3", "Engage-t-elle argent, droit ou un arbitrage ?", "Oui → humain décide (plan en difficulté, contrat, responsabilité)"], ["4", "Touche-t-elle un acheteur ?", "Oui → agent prépare, une personne valide (pendant tout le pilote)"],
    ["5", "L'erreur reste-t-elle interne et corrigible ?", "Oui → agent autonome, journalisé (vue CFO, tri interne) ; sinon validation"]];
  qs.forEach(([n, q, r], i) => {
    const y = 1.8 + i * 0.95;
    s.addShape("ellipse", { x: MX, y: y + 0.1, w: 0.6, h: 0.6, fill: { color: i === 3 ? HEX.teal : HEX.navy }, line: { type: "none" } });
    s.addText(n, T({ x: MX, y: y + 0.1, w: 0.6, h: 0.6, align: "center", valign: "middle", fontSize: 16, bold: true, color: HEX.white }));
    s.addText(q, T({ x: MX + 0.85, y, w: 4.6, h: 0.8, valign: "middle", fontSize: 13, bold: true, color: HEX.navy }));
    s.addShape("rect", { x: MX + 5.6, y, w: CW - 5.6, h: 0.8, fill: { color: i === 3 ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(r, T({ x: MX + 5.8, y, w: CW - 6.0, h: 0.8, valign: "middle", fontSize: 11, color: i === 3 ? HEX.white : HEX.black }));
  });
  s.addText("Puis le moment : pilote si un fichier suffit (C3 ≤ 2) et si la tâche sert les encaissements ; sinon ensuite ou vision.", T({ x: MX, y: 6.6 - 0.1, w: CW, h: 0.3, fontSize: 9.5, italic: true, color: HEX.text2 }));

  // Hosting
  pres.addSection({ title: H });
  s = L.content(pres, H, { subtitle: "Hébergement",
    title: "Une seule instance aux Émirats pour le pilote ; une instance par pays seulement quand un deuxième pays a un client",
    source: "Sources : AWS (Bedrock inter-régions, 24 février 2026) ; PDPL EAU (décret-loi fédéral n° 45 de 2021) ; PDPL KSA, art. 29. Pas un avis juridique" });
  s.addTable([
    [th("Couche"), th("Pilote Dubaï (shadow, anonymisé)"), th("Live Émirats"), th("Arabie saoudite, plus tard")],
    ...[["Application et données", "AWS, région Émirats (me-central-1)", "Idem ; conditions écrites dans le contrat", "Région saoudienne pour les clients régulés ; ouverture d'une région AWS annoncée pour décembre 2026 (à vérifier)"],
      ["Modèle d'IA", "Claude via Bedrock ; seuls des marqueurs partent (ni nom, ni téléphone, ni IBAN)", "Avis écrit d'un juriste local avant toute donnée réelle", "Transfert hors du royaume très encadré : à trancher"],
      ["Règles", "PDPL EAU : transferts possibles sous conditions", "Hébergement et sous-traitants fixés par écrit", "Transfert seulement par exception ; clients SAMA : données dans le royaume"],
      ["Journal et accès", "Journal d'audit signé (HMAC) et ancré ; approbateurs nommés", "Connexion individuelle de chaque approbateur", "Sauvegardes, journaux et support dans le royaume"]].map((r) => r.map((c, j) => td(c, j === 0 ? { bold: true, color: HEX.navy } : {}))),
  ], tableOpts({ y: 1.75, colW: [2.2, 3.4, 3.0, 3.5], rowH: [0.36, 0.8, 0.8, 0.7, 0.7] }));
  s.addShape("rect", { x: MX, y: 5.6, w: CW, h: 1.0, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "Stack proposée : ", options: { bold: true, color: HEX.teal } }, { text: "base relationnelle (dossiers, règles versionnées) · stockage objet · workflow durable pour J+3 à J+30 · journal en ajout seul · clés de chiffrement dans la région." }],
    T({ x: MX + 0.25, y: 5.6, w: CW - 0.5, h: 1.0, valign: "middle", fontSize: 10.5, color: HEX.black }));

  // AI cost
  s = L.content(pres, H, { subtitle: "Coût de l'IA",
    title: "Avec un petit modèle et des modèles de lettres, l'IA coûte une fraction de l'hypothèse de AED 0,30 par appartement et par mois",
    source: "Prix publics de l'API Anthropic, octobre 2026 (Bedrock a sa propre grille, à vérifier). Volumes par appartement : hypothèse. 1 USD = 3,6725 AED" });
  L.sticker(s, K, "ESTIMATION");
  s.addTable([
    [th("Élément"), th("Hypothèse"), th("Calcul"), th("Résultat")],
    ...[["Modèle par défaut", "Claude Haiku 5.5 (le POC, réglable)", "USD 0,10 / 0,50 par million de tokens (entrée / sortie)", "—"],
      ["Un brouillon", "800 tokens en entrée, 250 en sortie", "0,00008 + 0,000125", "≈ USD 0,0002"],
      ["Par appartement et par mois", "4 appels : appel, relance, réponse, cas ambigu", "4 × USD 0,0002", "≈ AED 0,003"],
      ["Tour de 300 appartements", "Un mois", "300 × AED 0,003", "≈ AED 0,9"],
      ["Avec un grand modèle", "Opus 5.5, mêmes volumes", "× 40 environ", "≈ AED 0,12 par appartement"]].map((r) => r.map((c, j) => td(c, j === 0 ? { bold: true, color: HEX.navy } : j === 3 ? { bold: true, color: HEX.teal } : {}))),
  ], tableOpts({ y: 1.75, colW: [2.6, 3.6, 3.6, 2.3], rowH: [0.36, 0.55, 0.55, 0.55, 0.55, 0.55] }));
  s.addShape("rect", { x: MX, y: 5.3, w: CW, h: 1.3, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Ce qui se mesure déjà : ", options: { bold: true, color: HEX.sky } },
    { text: "le POC compte les tokens de chaque appel et écrit le coût au journal (CONSOMMATION_IA). Pendant le shadow run, on remplace ces hypothèses par la mesure réelle, tour par tour.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.3, w: CW - 0.6, h: 1.3, valign: "middle", fontSize: 11.5 }));

  // Integrations
  s = L.content(pres, H, { subtitle: "Intégrations",
    title: "Le pilote tient avec trois fichiers et un portail ; chaque connexion directe arrive quand un client la paie",
    source: "Sources : Dubai Land Department (API Gateway, tarifs) ; Banque centrale des EAU (Open Finance, via Spare) ; Meta (WhatsApp Business Platform) ; POC Halden v0.2 (ingestion.py)" });
  s.addTable([
    [th("Système"), th("Comment on s'y branche"), th("Phase"), th("Ce qu'il faut savoir")],
    ...[["Plans de paiement et acheteurs", "Import Excel, colonnes validées par le promoteur", "Pilote", "Chaque promoteur a son format"],
      ["Relevés escrow", "CSV (plusieurs mises en page) et MT940, lus par le POC", "Pilote", "PDF : demander un export CSV à la banque ; débits et rejets lus"],
      ["Certification du jalon", "PDF par e-mail, puis formulaire", "Pilote", "Rien ne démarre sans certification humaine"],
      ["File d'approbation", "Portail Halden, approbateurs nommés", "Pilote", "Notifications e-mail ou Teams ensuite"],
      ["Open Finance EAU (AlTareq)", "Lecture des transactions via un TPP agréé", "Ensuite", "Cadre 2024 ; banques connectées à vérifier"],
      ["E-mail et WhatsApp sortants", "Domaine du promoteur ; API WhatsApp via fournisseur", "Ensuite", "Toujours après validation ; modèles approuvés par Meta"],
      ["DLD API Gateway", "Trust Account Bulk Inflow ; Oqood", "Vision", "Au nom du promoteur ; environ AED 30 000 + TVA par an et par API"],
      ["ERP du promoteur", "Lecture seule des exports", "Vision", "On lit, on ne remplace pas"]].map((r) => r.map((c, j) => td(c, j === 0 ? { bold: true, color: HEX.navy } : j === 2 && c === "Pilote" ? { bold: true, color: HEX.teal } : {}))),
  ], tableOpts({ y: 1.75, colW: [2.6, 4.0, 1.0, 4.5], rowH: [0.34, ...Array(8).fill(0.55)] }));

  // Decisions, with the "who presses send" question closed
  s = L.content(pres, H, { subtitle: "Décisions et prochaines étapes",
    title: "Une décision est prise, trois restent à trancher avant le live ; aucune ne bloque le shadow run",
    source: INTERNE });
  [["Décidé · Qui appuie sur « envoyer » ?", "Pendant le pilote, une personne nommée de l'équipe du promoteur valide chaque message ; rien ne part en shadow. En live, Halden envoie seulement ce qui a été validé.", 1],
    ["Où tourne le modèle d'IA en live ?", "Bedrock depuis la région Émirats, marqueurs à la place des données, avis écrit d'un juriste. Plan B : modèle hébergé dans le pays.", 0],
    ["Quel prestataire Open Finance ?", "Un TPP déjà agréé, choisi selon les banques escrow des premiers promoteurs.", 0],
    ["Quelle région pour la KSA ?", "Décider avec le premier client saoudien, pas avant.", 0]].forEach(([q, r, done], i) => {
    const w = (CW - 0.3) / 2, x = MX + (i % 2) * (w + 0.3), y = 1.8 + Math.floor(i / 2) * 1.45;
    s.addShape("rect", { x, y, w, h: 1.3, fill: { color: done ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(q, T({ x: x + 0.25, y: y + 0.12, w: w - 0.5, h: 0.4, fontSize: 12, bold: true, color: done ? HEX.sky : HEX.navy }));
    s.addText(r, T({ x: x + 0.25, y: y + 0.55, w: w - 0.5, h: 0.7, fontSize: 10, color: done ? HEX.white : HEX.black }));
  });
  L.colHead(s, K, "Dans les 30 prochains jours", MX, 4.75, CW);
  ["Passer le moteur sur un vrai relevé anonymisé", "Faire relire le pack Dubaï et la procédure de défaut par un juriste", "Noter la grille avec un directeur financier", "Faire relire les modèles arabes par un natif"].forEach((t, i) => {
    const w = (CW - 0.9) / 4, x = MX + i * (w + 0.3);
    s.addText(String(i + 1).padStart(2, "0"), T({ x, y: 5.3, w: 0.6, h: 0.5, fontSize: 18, color: HEX.teal }));
    s.addText(t, T({ x, y: 5.85, w, h: 0.8, fontSize: 10.5, color: HEX.black }));
  });

  // Sources
  s = L.content(pres, H, { subtitle: "Annexe · sources", title: "Chaque règle et chaque chiffre renvoie à une source ; les points incertains sont signalés", source: "Les points juridiques sont des résumés à confirmer avec un juriste émirati, pas un avis juridique" });
  s.addTable([
    [th("Domaine"), th("Source"), th("Statut")],
    ...[["Modèle IA aux EAU", "AWS Machine Learning Blog, inférence inter-régions de Claude au Moyen-Orient, 24 février 2026", "Vérifié"],
      ["Open Finance EAU", "Spare, cadre Open Finance de la Banque centrale (blog éditeur)", "À vérifier auprès de la Banque centrale"],
      ["DLD", "dubailand.gov.ae, API Gateway : Oqood, Trust Account Bulk Inflow, tarifs", "Vérifié"],
      ["Escrow et défaut", "Loi de Dubaï n° 8 de 2007 ; loi n° 13 de 2008, art. 11, modifiée par la loi n° 19 de 2017 ; Al Tamimi & Co.", "À valider par un juriste"],
      ["Données EAU et KSA", "PDPL EAU, décret-loi fédéral n° 45 de 2021 ; PDPL KSA, art. 29", "À valider par un juriste"],
      ["Cloud KSA", "Annonce d'une région AWS saoudienne pour décembre 2026, consultée en octobre 2026", "À vérifier"],
      ["Coût de l'IA", "Prix publics de l'API Anthropic, octobre 2026", "Estimation, à mesurer"],
      ["Grille et notation", "Équipe Halden ; calcul du POC Halden v0.2", "Hypothèse, à noter avec un DAF"]].map((r) => r.map((c, j) => td(c, j === 0 ? { bold: true, color: HEX.navy } : {}))),
  ], tableOpts({ y: 1.75, colW: [2.2, 7.2, 2.7], rowH: [0.34, ...Array(8).fill(0.52)] }));

  L.ending(pres, H, { title: "Chaque promesse, tenue jusqu'au bout", body: "Note d'architecture Halden · document de travail · octobre 2026" });

  await pres.writeFile({ fileName: out });
  await applyTheme(out, L.THEME);
  await L.morph(out);
}

build(process.argv[2] || "arch.pptx").catch((e) => { console.error(e); process.exit(1); });
