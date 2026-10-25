// Halden startup dossier v5: 12 slides, every point of Jennifer's review (24 Oct 2026) applied.
const L = require("./lib5");
const W = require("./wow5");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const { HEX, MX, CW, T } = L;

const SOFT = "C8CFDA";
const th = (t, fill) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: fill || HEX.navy }, fontSize: 10, valign: "middle" } });
const td = (t, o) => ({ text: t, options: Object.assign({ fontSize: 10, color: HEX.black, fill: { color: HEX.grey }, valign: "middle" }, o || {}) });
const fitW = (o) => (o.colW ? Object.assign({}, o, { colW: o.colW.map((c) => c * (o.w || CW) / o.colW.reduce((a, b) => a + b, 0)) }) : o);
const tableOpts = (o) => Object.assign({ x: MX, y: 1.75, w: CW, border: { type: "solid", pt: 3, color: HEX.white }, fontFace: L.F, margin: [0.04, 0.1, 0.04, 0.1] }, fitW(o));
const status = (t, fill) => td(t, { bold: true, color: HEX.white, fill: { color: fill }, align: "center" });

async function build(out) {
  const { pres, K } = await L.newPres("Halden : dossier startup");
  const S = "Synthèse", P = "Problème et marché", H = "Halden", M = "Modèle et pilote", E = "Équipe";

  // 1 · Cover
  pres.addSection({ title: S });
  L.cover(pres, S, { title: "Halden : le back-office IA des promoteurs off-plan à Dubaï",
    subtitle: "Dossier startup · un agent, un pays, un jalon", meta: "Document de travail · octobre 2026 · confidentiel" });

  // 2 · Synthesis
  let s = L.content(pres, S, { subtitle: "Synthèse",
    title: "Halden prend en charge les encaissements des promoteurs off-plan de Dubaï ; nous cherchons un premier shadow run",
    source: "Sources : DXB Interact (données DLD), 2025 ; pages produit d'Akarati et RealSoft, consultées le 24 octobre 2026. Complication = notre hypothèse" });
  L.colHead(s, K, "Étape", MX, 1.6, 2.6);
  L.colHead(s, K, "Constat", MX + 2.8, 1.6, CW - 2.8);
  [["Situation", "À Dubaï, environ deux tiers des AED 686,8 Md de ventes immobilières de 2025 sont off-plan. Chaque acheteur paie par tranches, à chaque jalon de chantier certifié, pendant environ 30 mois."],
    ["Complication", "Les ERP émiratis (Akarati, RealSoft) gèrent déjà échéanciers et relances. Notre hypothèse, à confirmer en entretiens : le travail qui reste à l'équipe est le rapprochement des virements mal référencés, les messages en arabe et en anglais et le dossier escrow."],
    ["Résolution", "Halden fait ce travail au-dessus de l'outil du promoteur. Pendant le pilote, chaque message vers un acheteur est validé par son équipe. L'IA ne signe rien et ne touche jamais à l'argent."]].forEach(([a, b], i) => {
    const y = 2.15 + i * 1.12;
    s.addText(a, T({ x: MX, y, w: 2.6, h: 0.95, valign: "middle", fontSize: 14, bold: true, color: i === 2 ? HEX.teal : HEX.navy }));
    s.addText(b, T({ x: MX + 2.8, y, w: CW - 2.8, h: 0.95, valign: "middle", fontSize: 11, color: HEX.black, lineSpacingMultiple: 1.05 }));
    s.addShape("line", { x: MX, y: y + 1.04, w: CW, h: 0, line: { color: HEX.line, width: 0.5 } });
  });
  s.addShape("rect", { x: MX, y: 5.7, w: CW, h: 0.95, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Notre demande : ", options: { bold: true, color: HEX.sky } },
    { text: "un promoteur de Dubaï qui accepte un shadow run gratuit de quatre semaines sur son prochain jalon. Rien n'est envoyé à ses acheteurs.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.7, w: CW - 0.6, h: 0.95, valign: "middle", fontSize: 13 }));

  // 3 · Problem, labelled as our hypothesis
  pres.addSection({ title: P });
  s = L.content(pres, P, { subtitle: "Le travail après chaque jalon certifié",
    title: "Notre hypothèse : après chaque jalon, quatre tâches liées au cash restent manuelles chez un promoteur de taille moyenne",
    source: "Hypothèse Halden, à confirmer en entretiens avec des équipes finance (aucun promoteur interrogé à ce jour). Escrow : loi de Dubaï n° 8 de 2007" });
  L.sticker(s, K, "HYPOTHÈSE");
  const tasks = [["FiFileText", "Appeler", "Chaque échéance, selon le plan de paiement de l'acheteur, dès le jalon certifié."],
    ["FiRepeat", "Rapprocher", "Chaque virement avec le bon acheteur, souvent sans référence ou avec celle d'un autre."],
    ["FiBell", "Relancer", "Les retards, en arabe ou en anglais, sans abîmer la relation."],
    ["FiArchive", "Documenter", "Un dossier propre pour le compte escrow, l'auditeur et les litiges."]];
  const tw = (8.2 - 0.6) / 4;
  for (let i = 0; i < 4; i++) {
    const [ic, h, b] = tasks[i], x = MX + i * (tw + 0.2);
    await L.iconTile(s, K, ic, x, 1.8, 0.6);
    s.addText(h, T({ x, y: 2.6, w: tw, h: 0.4, fontSize: 14, bold: true, color: HEX.navy }));
    s.addShape("line", { x, y: 3.1, w: 0.5, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x, y: 3.25, w: tw - 0.1, h: 1.3, fontSize: 10, color: HEX.black, lineSpacingMultiple: 1.05 }));
  }
  L.box(s, K, MX, 4.75, 8.2, 1.9);
  s.addText("QUI NOUS DÉCRIVONS", T({ x: MX + 0.25, y: 4.9, w: 7.7, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: HEX.blue }));
  s.addText("Un promoteur avec un à trois projets en cours. Les grands promoteurs ont un ERP ; nous ne savons pas encore comment travaillent les autres. Après chaque entretien, chaque tâche passe de « supposé » à « entendu ».",
    T({ x: MX + 0.25, y: 5.25, w: 7.7, h: 1.3, fontSize: 10.5, color: HEX.black, lineSpacingMultiple: 1.05 }));
  const rx = MX + 8.6, rw = CW - 8.6;
  s.addShape("rect", { x: rx, y: 1.8, w: rw, h: 4.85, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText("CE QUE GAGNE LE DIRECTEUR FINANCIER", T({ x: rx + 0.3, y: 2.05, w: rw - 0.6, h: 0.5, fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
  s.addText("Pas du cash plus tôt : l'escrow ne libère les fonds qu'au rythme de l'avancement certifié.", T({ x: rx + 0.3, y: 2.6, w: rw - 0.6, h: 1.0, fontSize: 12, bold: true, color: HEX.white }));
  s.addShape("line", { x: rx + 0.3, y: 3.75, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
  s.addText([{ text: "Moins de retards de paiement", options: { breakLine: true, bullet: { code: "2014", indent: 12 } } },
    { text: "Moins de temps d'équipe par jalon", options: { breakLine: true, bullet: { code: "2014", indent: 12 } } },
    { text: "Un dossier escrow prêt pour l'audit à chaque demande de libération", options: { bullet: { code: "2014", indent: 12 } } }],
    T({ x: rx + 0.3, y: 3.95, w: rw - 0.6, h: 2.4, fontSize: 11, color: SOFT, paraSpaceAfter: 8 }));

  // 4 · Market: one reading
  s = L.content(pres, P, { subtitle: "Marché off-plan de Dubaï",
    title: "Le marché off-plan reste massif mais ralentit en 2026 : chaque retard de paiement pèse davantage",
    source: "Sources : DXB Interact (DLD), 2025 ; Cavendish Maxwell via The National, T3 2026 ; TradeArabia, 2025 ; Gulf News, 2026. Lecture : la nôtre" });
  const kpi = [["686,8 Md", "AED de ventes immobilières à Dubaï en 2025, dont environ deux tiers off-plan"],
    ["72 %", "part de l'off-plan dans les achats à Dubaï au T3 2026"],
    ["−38 %", "volume résidentiel vendu au T3 2026, sur un an"],
    ["937", "projets en construction à Dubaï en 2025 (+25 %)"],
    ["186", "nouveaux promoteurs sur les sept premiers mois de 2026"]];
  const kw = (CW - 0.8) / 5;
  kpi.forEach(([v, l], i) => {
    const x = MX + i * (kw + 0.2), hot = i === 2;
    s.addShape("rect", { x, y: 1.8, w: kw, h: 2.45, fill: { color: hot ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(v, T({ x: x + 0.2, y: 1.95, w: kw - 0.4, h: 0.9, valign: "bottom", fontSize: 28, bold: true, color: hot ? HEX.sky : HEX.navy }));
    s.addShape("line", { x: x + 0.2, y: 3.0, w: 0.5, h: 0, line: { color: hot ? HEX.sky : HEX.teal, width: 0.75 } });
    s.addText(l, T({ x: x + 0.2, y: 3.15, w: kw - 0.4, h: 1.0, fontSize: 10, color: hot ? SOFT : HEX.black }));
  });
  L.colHead(s, K, "Notre lecture", MX, 4.45, CW);
  [["Le volume baisse", "Après le pic de 2025, moins d'unités se vendent. Les acheteurs déjà engagés continuent de payer leurs tranches jusqu'à la livraison."],
    ["Les retards montent", "Un acheteur qui a acheté au plus haut paie dans un marché plus mou : nous attendons plus de retards et plus de demandes d'étalement."],
    ["Ce que cela change pour nous", "Le suivi des encaissements devient plus important, pas moins. Nous ciblons les promoteurs qui ont déjà un deuxième projet licencié."]].forEach(([h, b], i) => {
    const w = (CW - 0.6) / 3, x = MX + i * (w + 0.3);
    s.addText(h, T({ x, y: 5.0, w, h: 0.35, fontSize: 12, bold: true, color: i === 2 ? HEX.teal : HEX.navy }));
    s.addText(b, T({ x, y: 5.4, w: w - 0.1, h: 1.2, fontSize: 10, color: HEX.black, lineSpacingMultiple: 1.05 }));
  });

  // 5 · Competition
  s = L.content(pres, P, { subtitle: "Positionnement concurrentiel aux Émirats",
    title: "Des ERP émiratis gèrent déjà échéanciers et relances ; Halden fait le travail que l'ERP laisse à l'équipe",
    source: "Sources : pages produit d'Akarati, RealSoft (Coral), In4Suite et RealCube, consultées le 24 octobre 2026 (citations de leurs propres pages). Réponses Halden : à tester" });
  L.sticker(s, K, "À TESTER");
  s.addTable([
    [th("Acteur"), th("Ce qu'il dit faire, sur sa propre page"), th("Ce qui reste à faire, selon nous", HEX.teal)],
    [td("Akarati", { bold: true, color: HEX.navy }), td("« Installments, reminders, dunning, and escrow posting » ; comptes escrow rapprochés ; revendique plus de AED 20 Md de stock géré"), td("Rapprocher un virement sans référence ou avec celle d'un autre acheteur ; décider quoi dire à un acheteur qui répond")],
    [td("RealSoft (Coral)", { bold: true, color: HEX.navy }), td("« Automated invoicing and reminders happen automatically » ; encaissements suivis en temps réel"), td("Relances qui s'arrêtent quand l'acheteur dit « j'ai payé » ou parle d'avocat")],
    [td("In4Suite", { bold: true, color: HEX.navy }), td("ERP immobilier : « RERA, Ejari & VAT compliance with AI + BI dashboards »"), td("L'IA est déjà dans leur discours : notre différence doit se voir sur un vrai relevé")],
    [td("RealCube", { bold: true, color: HEX.navy }), td("ERP avec plans de paiement"), td("Le travail entre l'ERP, la banque et l'acheteur")],
  ], tableOpts({ y: 1.75, colW: [1.9, 5.3, 4.9], rowH: [0.38, 0.72, 0.6, 0.6, 0.45] }));
  L.colHead(s, K, "Pourquoi un promoteur équipé ajouterait Halden : trois réponses à tester", MX, 4.75, CW);
  [["Nous faisons le travail", "Rapprocher, rédiger en arabe et en anglais, préparer l'escalade. L'ERP stocke et envoie."],
    ["Au-dessus de tout ERP", "Halden lit les exports de l'ERP et les relevés de la banque ; il ne remplace rien."],
    ["Pour les plus petits", "Les nouveaux promoteurs, trop petits pour un projet ERP, démarrent sur Halden et leur tableur."]].forEach(([h, b], i) => {
    const w = (CW - 0.6) / 3, x = MX + i * (w + 0.3);
    s.addText(h, T({ x, y: 5.3, w, h: 0.35, fontSize: 12, bold: true, color: HEX.navy }));
    s.addText(b, T({ x, y: 5.7, w: w - 0.1, h: 0.95, fontSize: 10, color: HEX.black }));
  });

  // 6 · How it works and the approval rule
  pres.addSection({ title: H });
  s = L.dark(pres, H, { subtitle: "La règle Halden pendant le pilote",
    title: "L'IA prépare ; l'équipe du promoteur valide chaque message vers un acheteur et décide de chaque exception",
    source: "Source : règle appliquée dans le code du POC Halden v0.2 et vérifiée par ses tests. Enregistrement Oqood : Dubai Land Department" });
  const cw3 = (CW - 0.6) / 3;
  [["01", "Préparer", "L'IA calcule les appels, rapproche les virements, rédige chaque message dans la langue de l'acheteur."],
    ["02", "Valider", "Chaque message vers un acheteur et chaque rapprochement incertain attendent l'accord d'une personne nommée."],
    ["03", "Décider", "Défaut de paiement, plan en difficulté, montant contesté : toujours un humain, avec le dossier préparé."]].forEach(([n, h, b], i) => {
    const x = MX + i * (cw3 + 0.3);
    s.addText(n, T({ x, y: 1.8, w: 1, h: 0.45, fontSize: 18, color: HEX.sky }));
    s.addText(h, T({ x, y: 2.25, w: cw3, h: 0.7, valign: "middle", fontSize: 30, bold: true, color: HEX.white }));
    s.addShape("line", { x, y: 3.05, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x, y: 3.2, w: cw3 - 0.2, h: 1.0, fontSize: 11, color: SOFT, lineSpacingMultiple: 1.05 }));
  });
  s.addShape("line", { x: MX, y: 4.45, w: CW, h: 0, line: { color: HEX.sky, width: 0.5, transparency: 60 } });
  s.addText("CE QUI ARRÊTE TOUT CONTACT AUTOMATIQUE AVEC UN ACHETEUR", T({ x: MX, y: 4.6, w: CW, h: 0.3, fontSize: 9, bold: true, charSpacing: 2.5, color: HEX.sky }));
  const stops = [["FiCheckCircle", "« J'ai payé »", "en anglais, arabe ou français"], ["FiBriefcase", "Avocat, réclamation", "ou difficulté de paiement"],
    ["FiClock", "Un paiement en attente", "ou un virement non identifié"], ["FiLock", "Jamais par l'IA", "signature, Oqood, argent"]];
  const sw4 = (CW - 0.6) / 4;
  for (let i = 0; i < 4; i++) {
    const x = MX + i * (sw4 + 0.2);
    await L.iconTile(s, K, stops[i][0], x, 5.1, 0.5, true);
    s.addText(stops[i][1], T({ x: x + 0.65, y: 5.05, w: sw4 - 0.65, h: 0.35, fontSize: 12, bold: true, color: HEX.white }));
    s.addText(stops[i][2], T({ x: x + 0.65, y: 5.42, w: sw4 - 0.7, h: 0.6, fontSize: 10, color: SOFT }));
  }

  // 7 · Demo, one set of figures
  W.waterfall(pres, H, { subtitle: "Démo du POC · un jalon sur une tour fictive",
    title: "Dans notre démo, 14 virements sur 19 sont rapprochés sans humain ; les 5 autres vont au directeur financier",
    sticker: "DÉMO · FICTIF", chartTitle: "Virements reçus pour le jalon, nombre (démo, données inventées)",
    steps: [["Virements reçus", 19, "total"], ["Rapprochés sans humain", 14, "step"], ["Validés par la CFO", 4, "step"], ["Refusé à raison", 1, "end"]],
    side: { value: "0", text: "message parti vers un acheteur sans validation. Le virement refusé portait la référence d'un autre acheteur : il n'est pas affecté automatiquement. 35 brouillons préparés, aucun envoyé (mode shadow)." },
    source: "Source : POC Halden v0.2, « python -m halden demo » (tour fictive de 32 acheteurs). Banc d'essai interne : 0 faux rapprochement automatique sur 200 lignes écrites par l'équipe" });

  // 8 · Dubai pack in preparation, DLD default procedure
  s = L.content(pres, H, { subtitle: "Pack de règles Dubaï",
    title: "Le pack Dubaï est en préparation : des règles en tables, à faire valider par un juriste émirati avant tout usage réel",
    source: "Sources : loi de Dubaï n° 8 de 2007 (escrow) ; loi n° 13 de 2008, art. 11, modifiée par la loi n° 19 de 2017 ; Al Tamimi & Co. Résumés, pas un avis juridique" });
  L.sticker(s, K, "EN PRÉPARATION", 1.8);
  s.addTable([
    [th("Règle"), th("Ce que fait Halden"), th("Statut")],
    [td("Un compte escrow par projet", { bold: true, color: HEX.navy }), td("Prépare les appels et rapproche ; les fonds sont libérés selon l'avancement certifié, Halden ne les touche jamais"), status("À VÉRIFIER", HEX.slate)],
    [td("Vente enregistrée à la DLD (Oqood)", { bold: true, color: HEX.navy }), td("Garde les plans de paiement cohérents avec la vente enregistrée ; l'enregistrement reste fait par l'équipe"), status("À VÉRIFIER", HEX.slate)],
    [td("Défaut de paiement", { bold: true, color: HEX.navy }), td("Prépare le dossier de notification DLD et les options ci-contre ; la décision reste humaine"), status("À VÉRIFIER", HEX.slate)],
  ], tableOpts({ x: MX, w: 7.6, y: 1.75, colW: [2.3, 4.0, 1.3], rowH: [0.38, 0.85, 0.85, 0.85] }));
  const dx = MX + 7.9, dw = CW - 7.9;
  s.addShape("rect", { x: dx, y: 1.75, w: dw, h: 4.9, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText("PROCÉDURE DE DÉFAUT, ÉTAPE PAR ÉTAPE", T({ x: dx + 0.3, y: 1.95, w: dw - 0.6, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
  [["1", "Le promoteur notifie le défaut à la DLD, qui notifie l'acheteur."], ["2", "L'acheteur dispose de 30 jours pour régulariser."],
    ["3", "Selon l'avancement certifié : ≥ 80 % maintien du contrat ou vente aux enchères ; 60–80 % résiliation, 40 % du prix au plus retenus ; < 60 % : 25 % au plus."]].forEach(([n, t], i) => {
    const y = 2.45 + i * 1.05;
    s.addText(n, T({ x: dx + 0.3, y, w: 0.4, h: 0.4, fontSize: 18, bold: true, color: HEX.sky }));
    s.addText(t, T({ x: dx + 0.8, y, w: dw - 1.1, h: 0.95, fontSize: 10, color: HEX.white }));
  });
  s.addShape("line", { x: dx + 0.3, y: 5.75, w: dw - 0.6, h: 0, line: { color: HEX.sky, width: 0.5, transparency: 50 } });
  s.addText("Dans le POC : étape J+30, décision humaine, contact automatique suspendu.", T({ x: dx + 0.3, y: 5.85, w: dw - 0.6, h: 0.6, fontSize: 10, italic: true, color: SOFT }));
  s.addShape("rect", { x: MX, y: 5.0, w: 7.6, h: 1.65, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "Vision, après un pilote réussi. ", options: { bold: true, color: HEX.teal } },
    { text: "L'Arabie saoudite (projets licenciés via Wafi, escrow projet) puis les autres étapes du parcours acheteur : livraison, information, garantie. Rien n'est commencé hors des encaissements à Dubaï." }],
    T({ x: MX + 0.25, y: 5.0, w: 7.1, h: 1.65, valign: "middle", fontSize: 10.5, color: HEX.black }));

  // 9 · Model, prices and sized market
  pres.addSection({ title: M });
  s = L.content(pres, M, { subtitle: "Modèle de revenus et marché adressable",
    title: "Avec nos prix indicatifs, Dubaï seul pèse environ AED 28 M de revenu annuel : une niche à prouver avant d'élargir",
    source: "Prix : site Halden et partner brief (indicatifs). Sources des volumes : TradeArabia (937 projets, 2025) ; REGA/Wafi (101 942 unités, 2023). Unités par projet et projets neufs : nos hypothèses" });
  L.sticker(s, K, "HYPOTHÈSE");
  const price = [["AED 15 000", "mise en place par projet", "pack pays, import des plans, prix et acheteurs"], ["AED 6–12", "par appartement et par mois", "de l'appel au solde de la livraison"], ["À définir", "en garantie", "qui paie pendant 10 ans : question ouverte"]];
  price.forEach(([v, u, b], i) => {
    const y = 1.8 + i * 1.12;
    s.addShape("rect", { x: MX, y, w: 4.4, h: 1.0, fill: { color: i === 1 ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(v, T({ x: MX + 0.2, y, w: 2.0, h: 1.0, valign: "middle", fontSize: 18, bold: true, color: i === 1 ? HEX.sky : HEX.navy }));
    s.addText([{ text: u, options: { bold: true, breakLine: true } }, { text: b }], T({ x: MX + 2.25, y: y + 0.1, w: 2.05, h: 0.8, valign: "middle", fontSize: 9, color: i === 1 ? HEX.white : HEX.black }));
  });
  const cx0 = MX + 4.8, cwid = CW - 4.8;
  L.colHead(s, K, "Calcul, Dubaï seul (hypothèses étiquetées)", cx0, 1.55, cwid);
  const calc = [["937", "projets en construction (TradeArabia, 2025)"], ["× 250", "unités par projet : hypothèse, à vérifier sur les données DLD"], ["× AED 9 × 12", "prix mensuel moyen entre 6 et 12, sur un an"],
    ["= AED 25,3 M", "abonnements"], ["+ AED 2,8 M", "mise en place : environ 190 projets neufs par an (hypothèse : +25 %) × AED 15 000"]];
  calc.forEach(([v, l], i) => {
    const y = 2.1 + i * 0.5, tot = i === 3;
    s.addText(v, T({ x: cx0, y, w: 2.3, h: 0.45, valign: "middle", fontSize: 13, bold: true, color: tot ? HEX.teal : HEX.navy }));
    s.addText(l, T({ x: cx0 + 2.4, y, w: cwid - 2.4, h: 0.45, valign: "middle", fontSize: 10, color: HEX.black }));
  });
  s.addShape("line", { x: cx0, y: 4.65, w: cwid, h: 0, line: { color: HEX.black, width: 0.75 } });
  s.addText([{ text: "≈ AED 28 M par an", options: { bold: true, color: HEX.teal } }, { text: " à Dubaï, si chaque projet était client. L'Arabie saoudite se calcule à part : 101 942 unités licenciées en 2023, soit environ AED 11 M au même prix." }],
    T({ x: cx0, y: 4.75, w: cwid, h: 0.7, fontSize: 10.5, color: HEX.black }));
  L.box(s, K, MX, 5.6, CW, 1.05);
  s.addText([{ text: "Questions ouvertes pour le juriste : ", options: { bold: true, color: HEX.teal } },
    { text: "une commission sur les retards recouvrés relève-t-elle du recouvrement de créances, activité soumise à licence aux EAU ? Qui paie des frais de garantie pendant 10 ans après la livraison ? Coût IA : AED 0,30 par appartement et par mois retenu par prudence ; le POC mesure la consommation réelle." }],
    T({ x: MX + 0.25, y: 5.6, w: CW - 0.5, h: 1.05, valign: "middle", fontSize: 10, color: HEX.black }));

  // 10 · Prospecting and pilot
  s = L.content(pres, M, { subtitle: "Prospection et shadow pilot",
    title: "Notre objectif à 90 jours : un promoteur qui accepte un shadow run, jugé sur quatre chiffres fixés d'avance",
    source: "Objectifs internes, non encore atteints. Base de temps : relevée chez le promoteur en semaine 1. Le taux de la démo (14 sur 19) ne préjuge pas du taux réel" });
  L.colHead(s, K, "Entonnoir de prospection", MX, 1.55, 4.6);
  const fun = [["30", "promoteurs de Dubaï avec un 2e projet licencié", 4.6], ["10", "introductions chaudes : alumni, LinkedIn, courtiers", 3.8], ["5", "entretiens avec la finance, pas les CEO", 3.0], ["1", "shadow run accepté", 2.2]];
  fun.forEach(([v, l, w], i) => {
    const y = 2.1 + i * 1.12;
    s.addShape("rect", { x: MX, y, w, h: 0.95, fill: { color: i === 3 ? HEX.teal : i === 0 ? HEX.navy : HEX.slate }, line: { type: "none" } });
    s.addText(v, T({ x: MX + 0.2, y, w: 0.9, h: 0.95, valign: "middle", fontSize: 24, bold: true, color: HEX.white }));
    s.addText(l, T({ x: MX + 1.1, y, w: w - 1.2, h: 0.95, valign: "middle", fontSize: 9.5, color: HEX.white }));
  });
  const px = MX + 5.1, pw = CW - 5.1;
  L.colHead(s, K, "Comment le shadow run est jugé", px, 1.55, pw);
  [["Temps passé", "Heures de l'équipe pour préparer le jalon, contre la base mesurée chez lui en semaine 1."],
    ["Rapprochement", "Part des virements rapprochés sans humain sur ses vrais relevés, et zéro rapprochement automatique faux."],
    ["Exactitude", "Zéro écart de montant entre les appels Halden et ceux de l'équipe."],
    ["Prudence", "Chaque « j'ai payé », avocat ou réclamation remonté à un humain, sans exception."]].forEach(([h, b], i) => {
    const y = 2.1 + i * 0.95;
    s.addShape("rect", { x: px, y, w: 0.06, h: 0.8, fill: { color: i === 1 ? HEX.teal : HEX.navy }, line: { type: "none" } });
    s.addText(h, T({ x: px + 0.25, y, w: 2.0, h: 0.8, valign: "middle", fontSize: 12, bold: true, color: HEX.navy }));
    s.addText(b, T({ x: px + 2.3, y, w: pw - 2.3, h: 0.8, valign: "middle", fontSize: 10, color: HEX.black }));
  });
  s.addShape("rect", { x: px, y: 6.0, w: pw, h: 0.65, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "Ensuite : ", options: { bold: true, color: HEX.teal } }, { text: "prix convenu avant le pilote, appliqué seulement si les chiffres sont atteints." }],
    T({ x: px + 0.25, y: 6.0, w: pw - 0.5, h: 0.65, valign: "middle", fontSize: 10.5, color: HEX.black }));

  // 11 · Risks, including the AI itself
  s = L.content(pres, M, { subtitle: "Risques principaux",
    title: "Nos risques tiennent à la confiance, aux règles, aux acteurs en place et à notre propre IA",
    source: "Source : revue interne de l'équipe, 24 octobre 2026 ; tests du POC Halden v0.2. PDPL : décret-loi fédéral n° 45 de 2021" });
  s.addTable([
    [th("Risque"), th("Pourquoi c'est critique"), th("Notre réponse", HEX.teal)],
    ...[["Confiance", "Un promoteur confie son cash et sa réputation à une équipe sans client.", "Shadow run : rien n'est envoyé ; comparaison sur ses données."],
      ["Contrôle de la rédaction IA", "Un montant faux ou un message déplacé vers un acheteur met fin au pilote.", "Montants contrôlés dans toutes les écritures ; chaque message validé."],
      ["Acteurs en place", "Akarati, RealSoft et In4Suite peuvent ajouter ce que nous faisons.", "Se poser au-dessus de leur ERP ; prouver sur un vrai relevé."],
      ["Réaction des acheteurs", "Des messages IA au nom du promoteur peuvent heurter un acheteur.", "Modèles relus par un arabophone natif ; arrêt au premier signal."],
      ["Exactitude des règles", "Une mauvaise étape de défaut a des conséquences juridiques.", "Règles en tables, signées par un juriste émirati avant usage réel."],
      ["Données personnelles", "Identités, IBAN et adresses d'acheteurs ; PDPL aux EAU.", "Région AWS des EAU ; noms remplacés par des marqueurs avant l'IA."],
      ["Capacité et dépendance", "Quatre étudiants à temps partiel ; un seul pilote possible à la fois.", "Un agent, un pays ; trois prospects actifs en parallèle."]]
      .map(([a, b, c]) => [td(a, { bold: true, color: HEX.navy }), td(b), td(c)]),
  ], tableOpts({ y: 1.7, colW: [2.5, 4.9, 4.7], rowH: [0.36, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66] }));

  // 12 · Team and contact
  pres.addSection({ title: E });
  s = await W.team(pres, E, { subtitle: "Équipe",
    title: "Quatre étudiants de SKEMA Business School, concentrés sur un seul problème : les encaissements off-plan",
    source: "Programme de six mois encadré par la faculté (track AI-native, SKEMA). Contact : haldennn.netlify.app",
    people: [["Jennifer El Karaki", "Stratégie et processus", "MSc Strategic Management and Consulting, SKEMA. Carte des processus, revue qualité."],
      ["Karam", "Produit et prototype", "Moteur agentique, POC et prototypes ; dossiers et présentations.", true],
      ["Dhruv", "Membre fondateur", "SKEMA Business School."],
      ["Thomas", "Membre fondateur", "SKEMA Business School."]] });
  s.addShape("rect", { x: MX, y: 6.0, w: CW, h: 0.65, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Déjà en place : ", options: { bold: true, color: HEX.sky } },
    { text: "un site avec une démo interactive, et un prototype qui rapproche, prépare et soumet chaque message à une personne (25 tests).", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 6.0, w: CW - 0.6, h: 0.65, valign: "middle", fontSize: 11 }));

  await pres.writeFile({ fileName: out });
  await applyTheme(out, L.THEME);
  await L.morph(out);
}

build(process.argv[2] || "dossier.pptx").catch((e) => { console.error(e); process.exit(1); });
