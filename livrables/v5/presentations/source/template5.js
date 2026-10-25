const L = require("./lib5");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const { HEX, MX, CW, colX, spanW, T } = L;

const th = (t, fill) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: fill || HEX.navy }, fontSize: 11, valign: "middle" } });
const td = (t, o) => ({ text: t, options: Object.assign({ fontSize: 11, color: HEX.black, fill: { color: HEX.grey }, valign: "middle" }, o || {}) });
const fitW = (o) => (o.colW ? Object.assign({}, o, { colW: o.colW.map((c) => c * CW / o.colW.reduce((a, b) => a + b, 0)) }) : o);
const tableOpts = (o) => Object.assign({ x: MX, y: 1.7, w: CW, border: { type: "solid", pt: 3, color: HEX.white }, fontFace: "Montserrat", margin: [0.05, 0.1, 0.05, 0.1] }, fitW(o));

async function build(out) {
  const { pres, K } = await L.newPres("Halden : template");
  const SEC = "Modèles";
  pres.addSection({ title: SEC });

  L.cover(pres, SEC, { title: "Titre de la présentation en deux lignes maximum", subtitle: "Sous-titre : pour qui, pour quelle décision", meta: "Type de document · mois année · confidentiel" });

  // Sommaire
  let s = L.content(pres, SEC, { title: "Le document répond à une question en cinq temps, de la conclusion aux prochaines étapes", subtitle: "Sommaire" });
  ["Synthèse", "Problème", "Marché", "Solution", "Prochaines étapes"].forEach((t, i) => {
    const y = 1.75 + i * 0.95;
    L.numBlock(s, K, "." + String(i + 1).padStart(2, "0"), MX, y, 1.0, 0.8, i === 0 ? K.teal : K.navy);
    L.cell(s, K, "", MX + 1.05, y, CW - 1.05, 0.8);
    s.addText([{ text: t, options: { bold: true, color: K.navy } }, { text: "     Ce que la section démontre, en une phrase", options: { color: HEX.text2, fontSize: 11 } }],
      T({ x: MX + 1.25, y, w: CW - 1.4, h: 0.8, valign: "middle", fontSize: 14 }));
  });

  L.divider(pres, SEC, { num: ".01", title: "Titre de section", body: "Ce que la section démontre, en une ou deux lignes" });

  // SCR
  s = L.content(pres, SEC, { title: "Titre d'action : la recommandation complète, en une phrase de deux lignes au plus", subtitle: "Modèle · Synthèse SCR", source: "Source : organisme, document, date" });
  L.colHead(s, K, "Étape", MX, 1.6, 2.6); L.colHead(s, K, "Constat", MX + 2.8, 1.6, CW - 2.8);
  [["Situation", "Les faits établis, que le lecteur accepte sans débat."], ["Complication", "Ce qui a changé ou va changer, et pourquoi c'est un problème maintenant."], ["Résolution", "Ce que nous recommandons, et le bénéfice attendu."]].forEach(([k, v], i) => {
    const y = 2.15 + i * 1.12;
    L.square(s, K, MX, y + 0.27, 0.42, i === 2 ? K.teal : K.navy);
    L.cell(s, K, k, MX + 0.5, y, 2.1, 0.96, { text: { valign: "middle", bold: true, color: K.navy } });
    L.box(s, K, MX + 2.8, y, CW - 2.8, 0.96);
    L.para(s, K, v, MX + 2.95, y, CW - 3.1, 0.96, { valign: "middle", fontSize: 11 });
  });
  L.bar(s, K, "DÉCISION ATTENDUE", MX, 5.65, 2.6, 0.9);
  L.cell(s, K, "Ce que le lecteur doit valider à la fin du document.", MX + 2.8, 5.65, CW - 2.8, 0.9, { text: { valign: "middle", fontSize: 12 } });

  // Highlights
  s = L.content(pres, SEC, { title: "Titre d'action : les quatre messages clés que le lecteur doit retenir", subtitle: "Modèle · Points clés", source: "Source : organisme, document, date" });
  for (let i = 0; i < 4; i++) {
    const x = colX(i * 3), w = spanW(3);
    s.addShape("rect", { x, y: 1.7, w, h: 0.95, fill: { color: i === 0 ? K.teal : K.navy }, line: { type: "none" } });
    s.addText([{ text: "MESSAGE " + (i + 1), options: { bold: true, breakLine: true } }, { text: "chiffre ou mot clé", options: { fontSize: 10 } }],
      T({ x, y: 1.7, w, h: 0.95, align: "center", valign: "middle", color: K.white }));
    L.cell(s, K, "", x, 2.75, w, 3.8);
    L.bullets(s, K, ["Preuve chiffrée et sourcée", "Deuxième élément de preuve", "Conséquence pour le lecteur"], x + 0.15, 2.95, w - 0.3, 3.4, { fontSize: 11 });
  }

  // Description rows
  s = L.content(pres, SEC, { title: "Titre d'action : les cinq éléments qui composent la réponse", subtitle: "Modèle · Description", source: "Source : organisme, document, date" });
  L.colHead(s, K, "Élément", MX, 1.6, 2.6); L.colHead(s, K, "Description", MX + 2.8, 1.6, CW - 2.8);
  for (let i = 0; i < 5; i++) {
    const y = 2.15 + i * 0.9;
    L.square(s, K, MX, y + 0.2, 0.36);
    L.cell(s, K, "Élément " + (i + 1), MX + 0.45, y, 2.15, 0.76, { text: { valign: "middle", bold: true, color: K.navy } });
    L.box(s, K, MX + 2.8, y, CW - 2.8, 0.76);
    L.para(s, K, "Une ou deux lignes qui décrivent l'élément et sa contribution à la conclusion du titre.", MX + 2.95, y, CW - 3.1, 0.76, { valign: "middle", fontSize: 11 });
  }

  // Chart + commentary
  s = L.content(pres, SEC, { title: "Titre d'action : la tendance que montre le graphique, avec le chiffre clé", subtitle: "Modèle · Graphique et commentaire", source: "Source : organisme, document, date" });
  L.sticker(s, K, "ILLUSTRATIF");
  L.colHead(s, K, "Ce qui est mesuré, unité", MX, 1.6, 8.1);
  s.addChart(pres.charts.BAR, [{ name: "Série", labels: ["2021", "2022", "2023", "2024", "2025"], values: [40, 48, 55, 61, 78] }], L.chartBase({
    x: MX, y: 2.1, w: 8.1, h: 4.5, barDir: "col", barGapWidthPct: 55, chartColors: [HEX.mid, HEX.mid, HEX.mid, HEX.mid, HEX.navy],
    showValue: true, dataLabelPosition: "outEnd", valAxisMaxVal: 90 }));
  const rx = MX + 8.5, rw = CW - 8.5;
  L.box(s, K, rx, 1.7, rw, 4.9);
  L.colHead(s, K, "Commentaire", rx + 0.2, 1.8, rw - 0.4);
  L.bullets(s, K, ["Le point principal que montre la barre nuit", "Le facteur qui l'explique", "Ce que cela implique pour la décision"], rx + 0.2, 2.4, rw - 0.4, 4.0, { fontSize: 11 });

  // Table
  s = L.content(pres, SEC, { title: "Titre d'action : l'option retenue et le critère qui fait la différence", subtitle: "Modèle · Tableau comparatif", source: "Source : organisme, document, date" });
  s.addTable([[th("Critère"), th("Option A"), th("Option B"), th("Option retenue", HEX.teal)],
    ...["Critère 1", "Critère 2", "Critère 3", "Critère 4"].map((k) => [td(k, { bold: true, color: HEX.navy }), td("Fait ou chiffre"), td("Fait ou chiffre"), td("Fait ou chiffre")]),
    [td("Verdict", { bold: true, color: HEX.navy }), td("Écartée"), td("Écartée"), td("Retenue", { bold: true, color: HEX.teal })]],
    tableOpts({ colW: [2.8, 3.23, 3.23, 3.23], rowH: [0.42, 0.8, 0.8, 0.8, 0.8, 0.6] }));

  // Process blocks
  s = L.content(pres, SEC, { title: "Titre d'action : comment le processus fonctionne et où l'équipe intervient", subtitle: "Modèle · Processus en étapes", source: "Source : organisme, document, date" });
  const fw = (CW - 3 * 0.35) / 4;
  for (let i = 0; i < 8; i++) {
    const r = Math.floor(i / 4), c = r === 0 ? i % 4 : 3 - (i % 4), human = i === 3 || i === 7;
    const x = MX + c * (fw + 0.35), y = 1.75 + r * 2.2;
    s.addShape("rect", { x, y, w: fw, h: 1.65, fill: { color: human ? K.teal : K.navy }, line: { type: "none" } });
    s.addText(String(i + 1).padStart(2, "0"), T({ x: x + 0.15, y: y + 0.12, w: 0.9, h: 0.6, fontSize: 26, color: K.white }));
    s.addText("ÉTAPE", T({ x: x + 1.05, y: y + 0.2, w: fw - 1.15, h: 0.45, valign: "middle", fontSize: 11, bold: true, color: K.white }));
    L.para(s, K, "Ce qui se passe, qui agit, ce qui en sort.", x + 0.15, y + 0.85, fw - 0.3, 0.75, { fontSize: 10, color: K.white });
    if (r === 0 && c < 3) s.addShape("line", { x: x + fw + 0.05, y: y + 0.82, w: 0.25, h: 0, line: { color: HEX.steel, width: 1.5, endArrowType: "triangle" } });
    if (r === 1 && c > 0) s.addShape("line", { x: x - 0.3, y: y + 0.82, w: 0.25, h: 0, line: { color: HEX.steel, width: 1.5, beginArrowType: "triangle" } });
  }
  s.addShape("line", { x: MX + 3 * (fw + 0.35) + fw / 2, y: 3.42, w: 0, h: 0.5, line: { color: HEX.steel, width: 1.5, endArrowType: "triangle" } });
  [["Automatique", K.navy], ["Décision humaine", K.teal]].forEach(([t, c], i) => {
    s.addShape("rect", { x: MX + i * 3.0, y: 6.35, w: 0.22, h: 0.22, fill: { color: c }, line: { type: "none" } });
    s.addText(t, T({ x: MX + 0.32 + i * 3.0, y: 6.33, w: 2.6, h: 0.26, valign: "middle", fontSize: 10 }));
  });

  // Matrix
  s = L.content(pres, SEC, { title: "Titre d'action : notre position sur les deux axes qui comptent pour le client", subtitle: "Modèle · Matrice 2 × 2", source: "Source : organisme, document, date. Positionnement qualitatif" });
  const mx0 = MX + 0.5, my0 = 1.75, mw = 6.9, mh = 4.5;
  [[0, 0, "Quadrant A"], [1, 0, "Quadrant cible"], [0, 1, "Quadrant C"], [1, 1, "Quadrant D"]].forEach(([c, r, t]) => {
    const hot = c === 1 && r === 0;
    s.addShape("rect", { x: mx0 + c * (mw / 2 + 0.05), y: my0 + r * (mh / 2 + 0.05), w: mw / 2 - 0.05, h: mh / 2 - 0.05, fill: { color: hot ? HEX.tint : HEX.grey }, line: { type: "none" } });
    s.addText(t, T({ x: mx0 + c * (mw / 2 + 0.05) + 0.12, y: my0 + r * (mh / 2 + 0.05) + 0.1, w: 3, h: 0.25, fontSize: 9, bold: true, color: hot ? K.teal : HEX.steel }));
  });
  s.addText("Axe horizontal : faible  →  fort", T({ x: mx0, y: my0 + mh + 0.1, w: mw, h: 0.28, fontSize: 9, color: HEX.text2, align: "center" }));
  s.addText("Axe vertical : faible  →  fort", T({ x: MX - 0.38, y: my0, w: 0.3, h: mh, fontSize: 9, color: HEX.text2, vert: "vert270", align: "center", valign: "middle" }));
  [[1.0, 3.3, "Acteur A"], [1.6, 1.0, "Acteur B"], [4.4, 3.5, "Acteur C"], [4.6, 1.1, "Nous"]].forEach(([x, y, l], i) => {
    const hot = i === 3;
    s.addShape("rect", { x: mx0 + x - 0.09, y: my0 + y - 0.09, w: 0.18, h: 0.18, fill: { color: hot ? K.teal : K.navy }, line: { type: "none" } });
    s.addText(l, T({ x: mx0 + x + 0.18, y: my0 + y - 0.2, w: 2, h: 0.4, valign: "middle", fontSize: hot ? 13 : 10, bold: hot, color: hot ? K.teal : K.black }));
  });
  const r2 = MX + 7.9, w2 = CW - 7.9;
  L.colHead(s, K, "Lecture", r2, 1.6, w2);
  L.bullets(s, K, ["Ce que signifie le quadrant cible", "Pourquoi les autres acteurs n'y sont pas", "Ce qui nous y maintient dans la durée"], r2, 2.2, w2, 3.5, { fontSize: 11 });

  // Gantt
  s = L.content(pres, SEC, { title: "Titre d'action : ce qui sera livré, dans quel ordre et à quelle condition", subtitle: "Modèle · Feuille de route", source: "Calendrier indicatif" });
  const gx0 = MX + 2.6, gw = CW - 2.6, mwid = gw / 6;
  for (let m = 0; m < 6; m++) L.bar(s, K, "Mois " + (m + 1), gx0 + m * mwid + 0.03, 1.65, mwid - 0.06, 0.34, { align: "center", fontSize: 10 });
  [["Chantier 1", 0, 2, K.navy], ["Chantier 2", 1, 3, K.navy], ["Jalon clé", 3, 1, K.teal], ["Chantier 3", 4, 2, HEX.slate]].forEach(([n, st, len, c], i) => {
    const y = 2.15 + i * 0.7;
    L.cell(s, K, n, MX, y, 2.5, 0.55, { text: { valign: "middle", bold: true, fontSize: 10, color: K.navy } });
    s.addShape("rect", { x: gx0 + 0.03, y, w: gw - 0.03, h: 0.55, fill: { color: HEX.grey }, line: { type: "none" } });
    s.addShape("rect", { x: gx0 + st * mwid + 0.03, y: y + 0.08, w: len * mwid - 0.06, h: 0.39, fill: { color: c }, line: { type: "none" } });
    s.addText("Livrable", T({ x: gx0 + st * mwid + 0.12, y: y + 0.08, w: len * mwid - 0.2, h: 0.39, valign: "middle", fontSize: 9, color: K.white }));
  });
  L.box(s, K, MX, 5.2, CW, 0.9);
  s.addText([{ text: "Condition de passage : ", options: { bold: true, color: HEX.blue } }, { text: "ce qui doit être prouvé avant de lancer l'étape suivante." }],
    T({ x: MX + 0.2, y: 5.2, w: CW - 0.4, h: 0.9, valign: "middle", fontSize: 11 }));

  // Driver tree
  s = L.content(pres, SEC, { title: "Titre d'action : les trois leviers qui déterminent le résultat, et celui qui pèse le plus", subtitle: "Modèle · Arbre de valeur", source: "Source ou hypothèse pour chaque valeur" });
  L.sticker(s, K, "HYPOTHÈSE");
  const ln = (x, y, w, h) => s.addShape("line", { x, y, w: w || 0.001, h: h || 0.001, line: { color: HEX.steel, width: 1 } });
  L.bar(s, K, "Résultat (unité)", MX, 3.65, 2.8, 0.9, { fontSize: 12 });
  const x2 = MX + 3.4, wd2 = 3.6, x3 = MX + 7.6, w3 = CW - 7.6;
  ln(MX + 2.8, 4.1, 0.3); ln(MX + 3.1, 2.3, 0, 3.6);
  for (let i = 0; i < 3; i++) {
    const y = 1.85 + i * 1.8;
    ln(MX + 3.1, y + 0.45, 0.3);
    L.bar(s, K, "Levier " + (i + 1), x2, y, wd2, 0.38, { fill: i === 0 ? K.teal : HEX.slate });
    L.cell(s, K, "formule ou définition", x2, y + 0.42, wd2, 0.55, { text: { fontSize: 11, valign: "middle" } });
    ln(x2 + wd2, y + 0.45, x3 - x2 - wd2);
    L.box(s, K, x3, y, w3, 0.97);
    s.addText([{ text: "Valeur", options: { bold: true, color: K.navy, breakLine: true } }, { text: "source ou hypothèse", options: { color: HEX.blue } }],
      T({ x: x3 + 0.15, y, w: w3 - 0.3, h: 0.97, valign: "middle", fontSize: 11 }));
  }

  // KPI tiles
  s = L.content(pres, SEC, { title: "Titre d'action : ce que disent les quatre indicateurs clés", subtitle: "Modèle · Chiffres clés", source: "Source : un organisme par chiffre, avec la date" });
  const ic = ["FiClock", "FiRepeat", "FiAlertTriangle", "FiTrendingUp"];
  for (let i = 0; i < 4; i++) {
    const x = colX(i * 3), w = spanW(3);
    s.addShape("rect", { x, y: 1.7, w, h: 2.3, fill: { color: K.navy }, line: { type: "none" } });
    await L.iconTile(s, K, ic[i], x + 0.2, 1.9, 0.6, true);
    s.addText(["00 %", "000", "0,0 M", "×0"][i], T({ x: x + 0.2, y: 2.6, w: w - 0.4, h: 0.65, valign: "bottom", fontSize: 28, bold: true, color: K.white }));
    s.addText("Ce que mesure le chiffre", T({ x: x + 0.2, y: 3.3, w: w - 0.4, h: 0.6, fontSize: 10, color: K.white }));
    L.cell(s, K, "Périmètre, année, statut", x, 4.1, w, 0.55, { text: { valign: "middle", fontSize: 10, italic: true } });
  }
  L.box(s, K, MX, 5.0, CW, 1.1);
  s.addText([{ text: "À retenir : ", options: { bold: true, color: HEX.blue } }, { text: "une ou deux phrases qui relient les chiffres à la conclusion du titre." }],
    T({ x: MX + 0.2, y: 5.0, w: CW - 0.4, h: 1.1, valign: "middle", fontSize: 11 }));

  // Next steps
  s = L.content(pres, SEC, { title: "Titre d'action : les décisions attendues aujourd'hui et ce qui se passe ensuite", subtitle: "Modèle · Prochaines étapes" });
  const half = spanW(6);
  [["Décisions attendues", K.teal, "Décision, et qui la prend"], ["Prochaines étapes", K.navy, "Action · responsable · date"]].forEach(([h, c, t], j) => {
    const x = colX(j * 6);
    L.colHead(s, K, h, x, 1.6, half);
    for (let i = 0; i < 4; i++) {
      const y = 2.15 + i * 1.05;
      s.addShape("rect", { x, y, w: 0.5, h: 0.9, fill: { color: c }, line: { type: "none" } });
      s.addText(String(i + 1), T({ x, y, w: 0.5, h: 0.9, align: "center", valign: "middle", fontSize: 14, bold: true, color: K.white }));
      L.cell(s, K, t, x + 0.55, y, half - 0.55, 0.9, { text: { valign: "middle" } });
    }
  });

  // Impact models
  const IMP = "Modèles impact", I = require("./impact5");
  pres.addSection({ title: IMP });
  L.divider(pres, IMP, { num: ".02", title: "Modèles impact", body: "Pour les moments forts : ouverture, chiffre clé, démonstration, conclusion. Un ou deux par présentation." });
  for (const k of ["bilingual", "statement", "hero", "heroRow", "morph", "timeline", "darkLine", "waterfall", "donut", "dashboard", "beforeAfter", "rings", "quote", "team"]) await I[k](pres, IMP);

  L.ending(pres, IMP, { title: "Message de clôture en une phrase", body: "Nom · rôle · e-mail\nhaldennn.netlify.app" });

  await pres.writeFile({ fileName: out });
  await applyTheme(out, L.THEME);
  await L.morph(out);
}

build(process.argv[2] || "template3.pptx").catch((e) => { console.error(e); process.exit(1); });
