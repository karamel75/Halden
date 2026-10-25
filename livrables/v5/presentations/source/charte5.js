const L = require("./lib5");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const { HEX, MX, CW, colX, spanW, T } = L;

async function build(out) {
  const { pres, K } = await L.newPres("Halden : charte graphique");
  const SEC = "Charte";
  pres.addSection({ title: SEC });

  L.cover(pres, SEC, { title: "Charte graphique Halden", subtitle: "Règles de présentation PowerPoint", meta: "Charte v5 · octobre 2026" });

  // Principes
  let s = L.content(pres, SEC, { title: "Une slide Halden se lit en dix secondes : le titre donne la conclusion, le corps la prouve", subtitle: "Quatre principes" });
  [["Titre d'action", "Une phrase complète qui énonce la conclusion, deux lignes au plus. Les titres lus à la suite racontent toute l'histoire."],
    ["Un message par slide", "Deux idées font deux slides. Le corps ne contient que ce qui prouve le titre."],
    ["Chaque chiffre a sa source", "Un organisme, un document, une date ; jamais notre propre brief. Ce qui n'est pas prouvé porte un sticker : HYPOTHÈSE, DÉMO · FICTIF, À TESTER."],
    ["Le bronze désigne l'essentiel", "Une seule couleur d'accent, réservée à la donnée ou à l'option que le lecteur doit regarder en premier."]].forEach(([h, b], i) => {
    const x = colX(i * 3), w = spanW(3);
    s.addShape("rect", { x, y: 1.7, w, h: 0.95, fill: { color: i === 3 ? K.teal : K.navy }, line: { type: "none" } });
    s.addText(String(i + 1).padStart(2, "0"), T({ x: x + 0.15, y: 1.7, w: 0.8, h: 0.95, valign: "middle", fontSize: 24, color: K.white }));
    s.addText(h, T({ x: x + 0.95, y: 1.7, w: w - 1.05, h: 0.95, valign: "middle", fontSize: 12, bold: true, color: K.white }));
    L.cell(s, K, b, x, 2.75, w, 2.2, { text: { fontSize: 11, valign: "top" } });
  });
  L.box(s, K, MX, 5.25, CW, 1.0);
  s.addText([{ text: "Positionnement : ", options: { bold: true, color: HEX.blue } },
    { text: "la rigueur d'un cabinet de conseil pour la structure, le registre du luxe à Dubaï pour le style : nuit, champagne, lignes de façade, beaucoup de blanc. Signature « Every promise, carried through. »" }],
    T({ x: MX + 0.2, y: 5.25, w: CW - 0.4, h: 1.0, valign: "middle", fontSize: 11 }));

  // Logo
  s = L.content(pres, SEC, { title: "La signature est un mot-symbole en capitales très espacées, posé sur blanc ou sur nuit", subtitle: "Identité", source: "Le logo est déjà placé sur chaque gabarit du template : ne pas le redessiner" });
  const lg = (x, dark) => {
    s.addShape("rect", { x, y: 1.7, w: spanW(6), h: 2.4, fill: { color: dark ? K.navy : K.grey }, line: { type: "none" } });
    s.addText("HALDEN", T({ x, y: 1.7, w: spanW(6), h: 2.0, align: "center", valign: "middle", fontSize: 36, bold: true, charSpacing: 10, color: dark ? K.white : K.navy }));
    s.addText("Every promise, carried through.", T({ x, y: 3.35, w: spanW(6), h: 0.4, align: "center", fontSize: 11, italic: true, color: dark ? HEX.sky : HEX.teal }));
  };
  lg(MX, false); lg(colX(6), true);
  [["Zone de protection", "Un espace libre égal à la hauteur des lettres autour du mot-symbole."], ["Taille minimale", "9 pt en pied de page ; 12 pt et plus en couverture."],
    ["Version arabe", "« هالدن » en IBM Plex Sans Arabic, à droite sur les documents bilingues. Tout texte arabe relu par un arabophone natif."], ["À éviter", "Changer la police, ajouter un effet, poser le logo sur une photo chargée."]].forEach(([h, b], i) => {
    const x = colX(i * 3), w = spanW(3);
    L.colHead(s, K, h, x, 4.35, w, { color: i === 3 ? HEX.red : HEX.blue });
    L.para(s, K, b, x, 4.85, w, 1.2, { fontSize: 11 });
  });

  // Palette
  s = L.content(pres, SEC, { title: "La palette part de la nuit de Dubaï ; le bronze et le champagne signent l'accent, jamais plus d'un par slide", subtitle: "Couleurs", source: "Couleurs enregistrées dans le thème du template : Création > Variantes > Couleurs > Halden" });
  [["Nuit", HEX.navy, "Fonds sombres, titres, texte, bandeaux, série principale", 1], ["Bronze", HEX.teal, "L'accent : chiffre ou option à retenir ; sur-titres", 1], ["Champagne", HEX.sky, "Filets et chiffres sur fond nuit ; jamais en fond sous un texte blanc", 0], ["Ardoise", HEX.slate, "Bandeaux et barres secondaires", 1],
    ["Gris perle", HEX.grey, "Fond des cellules et panneaux", 0], ["Gris graphique", HEX.mid, "Séries de contexte dans les graphiques", 0], ["Gris texte", HEX.text2, "Légendes, sources, textes secondaires", 1], ["Rouge", HEX.red, "Alerte uniquement", 1]].forEach(([n, hex, use, light], i) => {
    const x = colX((i % 4) * 3), y = 1.7 + Math.floor(i / 4) * 2.4, w = spanW(3);
    s.addShape("rect", { x, y, w, h: 1.1, fill: { color: hex }, line: { color: HEX.line, width: hex === HEX.grey ? 0.75 : 0 } });
    s.addText("#" + hex, T({ x: x + 0.12, y: y + 0.75, w: w - 0.24, h: 0.28, fontSize: 10, bold: true, color: light ? HEX.white : HEX.black }));
    s.addText(n, T({ x, y: y + 1.2, w, h: 0.3, bold: true, color: K.navy }));
    L.para(s, K, use, x, y + 1.5, w, 0.7, { fontSize: 10 });
  });

  // Typo
  s = L.content(pres, SEC, { title: "Montserrat pour le latin, IBM Plex Sans Arabic pour l'arabe : une seule identité, du deck au site", subtitle: "Typographie", source: "Deux polices gratuites (Google Fonts, licence OFL) à installer sur chaque poste. Le site haldennn.netlify.app doit reprendre les mêmes" });
  s.addShape("rect", { x: MX, y: 1.7, w: 4.3, h: 4.9, fill: { color: K.navy }, line: { type: "none" } });
  s.addText("Aa", T({ x: MX + 0.3, y: 1.9, w: 3.5, h: 1.6, fontSize: 80, bold: true, color: HEX.sky }));
  s.addText("Montserrat", T({ x: MX + 0.3, y: 3.6, w: 3.5, h: 0.5, fontSize: 22, color: K.white }));
  L.para(s, K, "Gras pour les titres et les chiffres. Capitales espacées pour les sur-titres et le logo. Regular pour le reste. L'arabe en IBM Plex Sans Arabic, aligné à droite.", MX + 0.3, 4.3, 3.7, 1.8, { fontSize: 11, color: K.white });
  const tx = MX + 4.6, tw = CW - 4.6;
  L.colHead(s, K, "Élément", tx, 1.6, 2.4); L.colHead(s, K, "Règle", tx + 2.6, 1.6, 2.6); L.colHead(s, K, "Exemple", tx + 5.4, 1.6, tw - 5.4);
  [["Sur-titre", "Gras 9 pt, capitales espacées, bronze", "MARCHÉ OFF-PLAN DE DUBAÏ", { fontSize: 9, bold: true, charSpacing: 3, color: HEX.blue }],
    ["Titre d'action", "Gras 20 pt, nuit, 2 lignes max", "Le marché ralentit : chaque retard pèse plus", { fontSize: 15, bold: true, color: K.black }],
    ["En-tête de colonne", "Gras 9 pt, capitales, bronze, filet", "CONSTAT", { fontSize: 9, bold: true, charSpacing: 2, color: HEX.blue }],
    ["Chiffre clé", "Gras 30 pt, nuit ou bronze", "686,8 Md", { fontSize: 24, bold: true, color: K.navy }],
    ["Corps", "10 à 12 pt, nuit", "Rien n'atteint un acheteur sans accord.", { fontSize: 11, color: K.black }],
    ["Source", "9 pt, gris texte : le minimum", "Source : DXB Interact, 2025", { fontSize: 9, color: HEX.text2 }],
    ["Arabe", "IBM Plex Sans Arabic, à droite", "كل وعد، حتى يتحقق", { fontSize: 14, fontFace: L.FA, rtlMode: true, align: "right", lang: "ar-AE", color: K.black }]].forEach(([n, r, ex, o], i) => {
    const y = 2.1 + i * 0.66;
    L.cell(s, K, n, tx, y, 2.4, 0.58, { text: { valign: "middle", bold: true, color: K.navy, fontSize: 11 } });
    L.cell(s, K, r, tx + 2.6, y, 2.6, 0.58, { text: { valign: "middle", fontSize: 10 } });
    s.addText(ex, T(Object.assign({ x: tx + 5.4, y, w: tw - 5.4, h: 0.58, valign: "middle" }, o)));
  });

  // Grille
  s = L.content(pres, SEC, { title: "Toutes les slides partagent la même anatomie ; seul le corps change d'une slide à l'autre", subtitle: "Grille et zones", source: "Format 16:9. Marges de 0,6 pouce, grille de 12 colonnes, gouttière de 0,2 pouce" });
  const sx = MX, sy = 1.7, sW = 7.4, k = sW / 13.333, sH = 7.5 * k;
  L.box(s, K, sx, sy, sW, sH, HEX.steel);
  for (let c = 0; c < 12; c++) s.addShape("rect", { x: sx + colX(c) * k, y: sy + 1.7 * k, w: L.COL * k, h: 5.1 * k, fill: { color: HEX.grey }, line: { type: "none" } });
  const zone = (n, x, y, w, h, fill) => {
    s.addShape("rect", { x: sx + x * k, y: sy + y * k, w: w * k, h: h * k, fill: { color: fill }, line: { type: "none" } });
    s.addText(String(n), T({ x: sx + x * k + 0.04, y: sy + y * k, w: 0.3, h: h * k, valign: "middle", fontSize: 9, bold: true, color: K.white }));
  };
  zone(1, MX, 0.7, CW, 0.82, HEX.navy); zone(2, MX, 0.36, 5, 0.3, HEX.blue); zone(3, MX, 1.7, CW, 5.1, HEX.mid);
  zone(4, MX, 7.0, 1.3, 0.3, HEX.navy); zone(5, 2.0, 7.0, 9.8, 0.3, HEX.steel); zone(6, 12.23, 7.0, 0.5, 0.3, HEX.steel);
  const zx = MX + 7.8, zw = CW - 7.8;
  [["Titre d'action", "La conclusion, en une phrase"], ["Sur-titre", "Le sujet, en capitales espacées"], ["Corps", "Aligné sur les 12 colonnes"], ["Logo", "Fixé sur le gabarit"], ["Source", "Obligatoire dès qu'un chiffre apparaît"], ["Numéro", "Automatique"]].forEach(([n, d], i) => {
    const y = 1.7 + i * 0.68;
    s.addShape("rect", { x: zx, y, w: 0.45, h: 0.55, fill: { color: K.navy }, line: { type: "none" } });
    s.addText(String(i + 1), T({ x: zx, y, w: 0.45, h: 0.55, align: "center", valign: "middle", bold: true, color: K.white }));
    L.cell(s, K, "", zx + 0.5, y, zw - 0.5, 0.55);
    s.addText([{ text: n + "  ", options: { bold: true, color: K.navy } }, { text: d, options: { fontSize: 10 } }], T({ x: zx + 0.62, y, w: zw - 0.7, h: 0.55, valign: "middle", fontSize: 11 }));
  });

  // Titres
  s = L.content(pres, SEC, { title: "Un titre d'action dit ce que le lecteur doit retenir ; un titre-sujet l'oblige à deviner", subtitle: "Titres", source: "Test : en lisant seulement les titres du deck, dans l'ordre, on comprend toute la recommandation" });
  const hw = spanW(6);
  L.colHead(s, K, "À éviter : titre-sujet", colX(0), 1.6, hw, { color: HEX.red });
  L.colHead(s, K, "À faire : titre d'action", colX(6), 1.6, hw);
  [["Marché", "Le marché off-plan reste massif mais ralentit : chaque retard de paiement pèse davantage"],
    ["Concurrence", "Des ERP gèrent déjà les relances ; Halden fait le travail que l'ERP laisse à l'équipe"],
    ["Résultats de la démo", "Dans notre démo, 14 virements sur 19 sont rapprochés sans humain"],
    ["Prochaines étapes", "D'ici 90 jours : un promoteur qui accepte un shadow run sur son prochain jalon"]].forEach(([a, b], i) => {
    const y = 2.15 + i * 0.95;
    L.cell(s, K, a, colX(0), y, hw, 0.82, { text: { valign: "middle", fontSize: 13, color: HEX.text2 } });
    L.box(s, K, colX(6), y, hw, 0.82);
    L.para(s, K, b, colX(6) + 0.15, y, hw - 0.3, 0.82, { valign: "middle", bold: true, fontSize: 11 });
  });
  L.bullets(s, K, ["Une phrase avec un verbe, au présent, sans point final.", "Un chiffre inventé n'apparaît jamais dans un titre sans « dans notre démo ».", "Le sur-titre bronze donne le sujet ; le titre donne la conclusion."], MX, 6.0, CW, 0.85, { fontSize: 11, paraSpaceAfter: 2 });

  // Graphiques
  s = L.content(pres, SEC, { title: "Un graphique Halden met une seule donnée en nuit ou en bronze et retire tout le reste", subtitle: "Graphiques", source: "Exemple : POC Halden v0.2, démo sur données fictives. Graphiques natifs PowerPoint, modifiables" });
  L.sticker(s, K, "EXEMPLE");
  L.colHead(s, K, "Virements par résultat du rapprochement, nombre (démo)", MX, 1.6, 6.6);
  s.addChart(pres.charts.BAR, [{ name: "Virements", labels: ["Sans humain", "Validés par la CFO", "Refusé"], values: [14, 4, 1] }], L.chartBase({
    x: MX, y: 2.1, w: 6.6, h: 4.4, barDir: "col", barGapWidthPct: 60, chartColors: [HEX.navy, HEX.mid, HEX.mid], showValue: true, dataLabelPosition: "outEnd", valAxisMaxVal: 16 }));
  const rx = MX + 7.0, rw = CW - 7.0;
  [["Titre du graphique", "Ce qui est mesuré et l'unité, en sur-titre bronze avec filet."], ["Une donnée mise en avant", "Nuit ou bronze pour la donnée du titre, gris pour le contexte."],
    ["Étiquettes directes", "Valeurs sur les barres ; ni axe vertical ni quadrillage."], ["Commentaire à droite", "Un cadre fin avec le message du graphique en trois puces."], ["Jamais", "3D, ombres, dégradés, légendes inutiles, camemberts à plus de trois parts."]].forEach(([h, b], i) => {
    const y = 1.7 + i * 0.97;
    s.addShape("rect", { x: rx, y, w: 0.45, h: 0.85, fill: { color: i === 4 ? HEX.red : K.navy }, line: { type: "none" } });
    s.addText(String(i + 1), T({ x: rx, y, w: 0.45, h: 0.85, align: "center", valign: "middle", bold: true, color: K.white }));
    L.cell(s, K, "", rx + 0.5, y, rw - 0.5, 0.85);
    s.addText([{ text: h, options: { bold: true, color: K.navy, breakLine: true } }, { text: b, options: { fontSize: 10 } }], T({ x: rx + 0.62, y, w: rw - 0.75, h: 0.85, valign: "middle", fontSize: 11 }));
  });

  // Éléments
  s = L.content(pres, SEC, { title: "Une boîte à outils courte donne au deck sa cohérence, sans aucune décoration superflue", subtitle: "Éléments récurrents", source: "Tous ces éléments sont prêts à copier dans le template" });
  const ew = spanW(4);
  const blk = (i, h, y) => { L.colHead(s, K, h, colX(i * 4), y, ew); return colX(i * 4); };
  let x = blk(0, "Bandeau et cellules", 1.6);
  L.bar(s, K, "BANDEAU NUIT", x, 2.15, ew, 0.4);
  L.cell(s, K, "Cellule grise : contenu d'un tableau ou d'une carte", x, 2.6, ew, 0.7, { text: { valign: "middle" } });
  L.box(s, K, x, 3.4, ew, 0.7); L.para(s, K, "Cadre fin : commentaire ou message clé", x + 0.15, 3.4, ew - 0.3, 0.7, { valign: "middle", fontSize: 11 });
  x = blk(1, "Statuts", 1.6);
  [["STOPPÉ", HEX.red], ["À VÉRIFIER", HEX.blue], ["À DÉCIDER", HEX.navy], ["FAIT", HEX.steel]].forEach(([t, c], i) => L.tag(s, K, t, x, 2.15 + i * 0.48, 1.6, c));
  x = blk(2, "Stickers", 1.6);
  ["HYPOTHÈSE", "DÉMO · FICTIF", "À TESTER"].forEach((t, i) => {
    s.addShape("rect", { x, y: 2.15 + i * 0.48, w: 1.6, h: 0.26, fill: { color: K.white }, line: { color: HEX.sky, width: 0.75 } });
    s.addText(t, T({ x, y: 2.15 + i * 0.48, w: 1.6, h: 0.26, align: "center", valign: "middle", fontSize: 7.5, bold: true, charSpacing: 1.5, color: HEX.blue }));
  });
  x = blk(0, "Chiffre clé", 4.4);
  L.cell(s, K, "", x, 4.95, ew, 1.6); L.stat(s, K, "14 / 19", "virements rapprochés sans humain, dans notre démo", x + 0.2, 5.0, ew - 0.4, K.teal);
  x = blk(1, "Numéros et repères", 4.4);
  ["01", "02", "03"].forEach((n, i) => L.numBlock(s, K, n, x + i * 1.0, 4.95, 0.9, 0.8, i === 0 ? K.teal : K.navy));
  [0, 1, 2].forEach((i) => L.square(s, K, x + i * 0.5, 6.0, 0.3));
  x = blk(2, "Icônes", 4.4);
  const ic = ["FiFileText", "FiRepeat", "FiBell", "FiShield"];
  for (let i = 0; i < 4; i++) await L.iconTile(s, K, ic[i], x + i * 0.85, 4.95, 0.7);
  L.para(s, K, "Trait fin nuit dans un carré gris perle, ou champagne sur fond nuit. Toujours avec un intitulé.", x, 5.8, ew, 0.7, { fontSize: 10 });

  // Gabarits
  s = L.content(pres, SEC, { title: "Le template fournit cinq gabarits et 28 modèles : on part d'un modèle, jamais d'une page blanche", subtitle: "Gabarits et modèles", source: "Fichier Halden_Template_v5.pptx · Accueil > Nouvelle diapositive pour choisir un gabarit" });
  [["Couverture", "H_COVER", 1], ["Intercalaire", "H_DIVIDER", 1], ["Contenu", "H_CONTENT", 0], ["Contenu sombre", "H_DARK", 1], ["Clôture", "H_END", 1]].forEach(([n, id, dark], i) => {
    const w = (CW - 0.8) / 5, x = MX + i * (w + 0.2), h = w * 0.5625;
    if (dark) s.addImage({ path: require("path").join(__dirname, i === 1 ? "bg-art-soft.png" : "bg-art.png"), x, y: 1.7, w, h, altText: "Fond nuit" });
    else s.addShape("rect", { x, y: 1.7, w, h, fill: { color: K.white }, line: { color: HEX.line, width: 0.75 } });
    s.addShape("rect", { x: x + 0.2, y: 1.7 + (dark ? h * 0.42 : 0.3), w: w * 0.55, h: 0.1, fill: { color: dark ? K.white : K.black }, line: { type: "none" } });
    if (dark) s.addShape("line", { x: x + 0.2, y: 1.7 + h * 0.62, w: 0.4, h: 0, line: { color: HEX.sky, width: 0.75 } });
    else { s.addShape("rect", { x: x + 0.2, y: 1.7 + 0.15, w: w * 0.25, h: 0.05, fill: { color: HEX.blue }, line: { type: "none" } });
      s.addShape("rect", { x: x + 0.2, y: 1.7 + 0.6, w: w - 0.4, h: h - 0.85, fill: { color: K.grey }, line: { type: "none" } }); }
    s.addText([{ text: n, options: { bold: true, color: K.navy, breakLine: true } }, { text: id, options: { fontSize: 9, color: HEX.text2 } }], T({ x, y: 1.75 + h, w, h: 0.55 }));
  });
  L.colHead(s, K, "Modèles prêts à remplir : classiques, puis impact (fond nuit, chiffres géants, Morph)", MX, 4.0, CW);
  ["Sommaire", "Synthèse SCR", "Points clés", "Description", "Graphique + commentaire", "Tableau comparatif", "Processus en étapes",
    "Matrice 2 × 2", "Feuille de route", "Arbre de valeur", "Chiffres clés", "Prochaines étapes", "Intercalaire", "Clôture",
    "Couverture bilingue", "Phrase choc", "Chiffre géant", "Trois chiffres", "Zoom Morph", "Frise", "Courbe sur nuit",
    "Cascade", "Anneau", "Tableau de bord", "Avant / après", "Carte d'expansion", "Citation", "Équipe"].forEach((m, i) => {
    const x = MX + (i % 7) * (CW + 0.1) / 7, y = 4.55 + Math.floor(i / 7) * 0.57, imp = i >= 14;
    L.cell(s, K, m, x, y, (CW + 0.1) / 7 - 0.1, 0.5, { fill: imp ? HEX.navy : HEX.grey, text: { valign: "middle", align: "center", fontSize: 9, color: imp ? HEX.white : HEX.black } });
  });

  // Checklist
  s = L.content(pres, SEC, { title: "Avant d'envoyer un deck, dix vérifications garantissent le niveau d'exigence Halden", subtitle: "Contrôle avant envoi", source: "Faire relire par une deuxième personne tout document externe" });
  ["Les titres lus à la suite racontent toute l'histoire", "Chaque titre tient en deux lignes, sans point final", "Une seule idée par slide", "Chaque chiffre a une source externe, jamais notre brief",
    "Chiffre inventé : sticker et « dans notre démo » au titre", "Un seul accent bronze par slide", "Aucun texte sous 9 pt, sources comprises", "Vocabulaire de Dubaï : DLD, Oqood ; jamais « notaire »",
    "Graphiques natifs, sans 3D ni légende inutile", "Pas de texte qui déborde de son cadre"].forEach((t, i) => {
    const x = colX((i % 2) * 6), y = 1.7 + Math.floor(i / 2) * 0.95, w = spanW(6);
    s.addShape("rect", { x, y, w: 0.5, h: 0.8, fill: { color: K.navy }, line: { type: "none" } });
    s.addText("✓", T({ x, y, w: 0.5, h: 0.8, align: "center", valign: "middle", fontSize: 14, bold: true, color: K.white }));
    L.cell(s, K, t, x + 0.55, y, w - 0.55, 0.8, { text: { valign: "middle" } });
  });

  L.ending(pres, SEC, { title: "Sobre, précis, sourcé", body: "Template : Halden_Template_v5.pptx · Polices : Montserrat, IBM Plex Sans Arabic\nUn document maître par sujet ; la version uniquement dans le nom du fichier" });

  await pres.writeFile({ fileName: out });
  await applyTheme(out, L.THEME);
  await L.morph(out);
}

build(process.argv[2] || "charte5.pptx").catch((e) => { console.error(e); process.exit(1); });
