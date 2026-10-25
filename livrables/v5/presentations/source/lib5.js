// Halden v5 (charte v5): nothing under 9 pt, Arabic in IBM Plex Sans Arabic.
// Halden v3 base: premium Dubai look. Montserrat, midnight ink, champagne bronze, hairlines and air.
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fi = require("react-icons/fi");
const path = require("path");

const F = "Montserrat";
const FA = "IBM Plex Sans Arabic";
const MIN = 9;
const HEX = {
  black: "0B1426",      // ink: titles and text
  white: "FFFFFF",
  navy: "0B1426",       // midnight: dark fills
  deep: "050A15",
  blue: "8A6A3A",       // bronze text: eyebrows, column heads
  sky: "C9A86A",        // champagne: hairlines, numbers on dark
  teal: "8A6A3A",       // bronze fill: the one accent
  steel: "5B6472",
  grey: "F4F5F7",
  mid: "CBD1DA",
  text2: "5B6472",
  line: "D5D8DE",
  red: "B42318",
  tint: "F3EEE4",
  slate: "3A4A63",
};

const THEME = {
  name: "Halden",
  headFontFace: F,
  bodyFontFace: F,
  colors: {
    dk1: HEX.black, lt1: HEX.white, dk2: HEX.navy, lt2: HEX.grey,
    accent1: HEX.navy, accent2: HEX.sky, accent3: HEX.teal,
    accent4: HEX.steel, accent5: HEX.deep, accent6: HEX.red,
    hlink: HEX.teal, folHlink: HEX.steel,
  },
};

const W = 13.333, H = 7.5, MX = 0.6, CW = 12.133;
const GUT = 0.2, COL = (CW - 11 * GUT) / 12;
const colX = (i) => MX + i * (COL + GUT);
const spanW = (n) => n * COL + (n - 1) * GUT;

// Midnight background with a curved-facade line motif (the tower on the Halden site)
async function artPng(file, strength) {
  const w = 1920, h = 1080;
  let lines = "";
  for (let i = 0; i <= 90; i++) {
    const t = i / 90;
    const x = 820 + 1180 * Math.pow(t, 1.6);
    const bow = 120 * Math.sin(Math.PI * t);
    lines += `<path d="M${x.toFixed(1)} -10 Q ${(x - bow).toFixed(1)} ${h / 2} ${x.toFixed(1)} ${h + 10}" stroke="#C9A86A" stroke-width="1.2" fill="none"/>`;
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0F1B31"/><stop offset="1" stop-color="#${HEX.deep}"/></linearGradient>
      <radialGradient id="r" cx="0.82" cy="0.1" r="0.7"><stop offset="0" stop-color="#C9A86A" stop-opacity="${0.13 * strength}"/><stop offset="1" stop-color="#C9A86A" stop-opacity="0"/></radialGradient>
      <linearGradient id="fx" x1="0" y1="0" x2="1" y2="0"><stop offset="0.42" stop-color="#fff" stop-opacity="0"/><stop offset="0.72" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0.55"/></linearGradient>
      <linearGradient id="fy" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0.25"/></linearGradient>
      <mask id="m"><rect width="${w}" height="${h}" fill="url(#fx)"/></mask>
      <mask id="m2"><rect width="${w}" height="${h}" fill="url(#fy)"/></mask>
    </defs>
    <rect width="${w}" height="${h}" fill="url(#g)"/><rect width="${w}" height="${h}" fill="url(#r)"/>
    <g mask="url(#m2)"><g mask="url(#m)" opacity="${0.42 * strength}">${lines}</g></g></svg>`;
  await sharp(Buffer.from(svg)).png().toFile(file);
  return file;
}

async function newPres(title, opts) {
  opts = opts || {};
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: F, bodyFontFace: F };
  pres.author = "Halden";
  pres.company = "Halden";
  pres.title = title;
  const C = pres.SchemeColor;
  const K = { black: C.text1, white: C.background1, navy: C.text2, grey: C.background2,
    sky: C.accent2, teal: C.accent3, steel: C.accent4, deep: C.accent5, red: C.accent6 };
  const bgStrong = await artPng(path.join(__dirname, "bg-art.png"), 1);
  const bgSoft = await artPng(path.join(__dirname, "bg-art-soft.png"), 0.55);
  const bgFaint = await artPng(path.join(__dirname, "bg-art-faint.png"), 0.25);
  defineLayouts(pres, K, bgStrong, bgSoft, bgFaint, opts.place || "DUBAÏ · 2026");
  return { pres, K };
}

const wordmark = (x, y, color, size) => ({ text: { text: "HALDEN", options: { x, y, w: 2.2, h: 0.3, margin: 0, valign: "middle",
  fontFace: F, fontSize: size || 9, bold: true, charSpacing: 6, color } } });

function defineLayouts(pres, K, bgStrong, bgSoft, bgFaint, place) {
  pres.defineSlideMaster({
    title: "H_CONTENT",
    background: { color: HEX.white },
    margin: [0.4, MX, 0.7, MX],
    objects: [
      wordmark(MX, 7.0, HEX.navy),
      { placeholder: { options: { name: "subtitle", type: "body", x: MX, y: 0.38, w: CW, h: 0.26, margin: 0,
        fontFace: F, fontSize: 9, bold: true, charSpacing: 3, color: HEX.blue, valign: "middle", align: "left" }, text: "SECTION · SUJET" } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.7, w: CW, h: 0.82, margin: 0,
        fontFace: F, fontSize: 20, bold: true, color: K.black, valign: "top", align: "left", lineSpacingMultiple: 0.95 },
        text: "Titre d'action : la conclusion de la slide en une phrase" } },
      { placeholder: { options: { name: "source", type: "body", x: 2.0, y: 7.0, w: 9.8, h: 0.3, margin: 0,
        fontFace: F, fontSize: 9, color: HEX.text2, valign: "middle", align: "left" }, text: "Source : organisme, document, date" } },
    ],
    slideNumber: { x: 12.23, y: 7.0, w: 0.5, h: 0.3, fontFace: F, fontSize: 9, color: HEX.text2, align: "right", valign: "middle", margin: 0 },
  });

  // Content on midnight: for impact slides (hero numbers, dark charts, maps)
  pres.defineSlideMaster({
    title: "H_DARK",
    background: { path: bgFaint },
    margin: [0.4, MX, 0.7, MX],
    objects: [
      wordmark(MX, 7.0, HEX.white),
      { placeholder: { options: { name: "subtitle", type: "body", x: MX, y: 0.38, w: CW, h: 0.26, margin: 0,
        fontFace: F, fontSize: 9, bold: true, charSpacing: 3, color: HEX.sky, valign: "middle", align: "left" }, text: "SECTION · SUJET" } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.7, w: CW, h: 0.82, margin: 0,
        fontFace: F, fontSize: 20, bold: true, color: K.white, valign: "top", align: "left", lineSpacingMultiple: 0.95 },
        text: "Titre d'action : la conclusion de la slide en une phrase" } },
      { placeholder: { options: { name: "source", type: "body", x: 2.0, y: 7.0, w: 9.8, h: 0.3, margin: 0,
        fontFace: F, fontSize: 9, color: "8C96A8", valign: "middle", align: "left" }, text: "Source : organisme, document, date" } },
    ],
    slideNumber: { x: 12.23, y: 7.0, w: 0.5, h: 0.3, fontFace: F, fontSize: 9, color: "8C96A8", align: "right", valign: "middle", margin: 0 },
  });

  pres.defineSlideMaster({
    title: "H_COVER",
    background: { path: bgStrong },
    objects: [
      wordmark(MX, 0.6, HEX.white, 12),
      { line: { x: MX, y: 4.3, w: 1.2, h: 0, line: { color: HEX.sky, width: 1 } } },
      { placeholder: { options: { name: "meta", type: "body", x: MX, y: 2.0, w: 7.5, h: 0.3, margin: 0,
        fontFace: F, fontSize: 9, bold: true, charSpacing: 4, color: HEX.sky, valign: "middle", align: "left" }, text: "DOCUMENT DE TRAVAIL · MOIS ANNÉE" } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.4, w: 7.6, h: 1.75, margin: 0,
        fontFace: F, fontSize: 34, bold: true, color: K.white, valign: "top", align: "left", lineSpacingMultiple: 0.95 }, text: "Titre de la présentation" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: MX, y: 4.5, w: 7.2, h: 0.8, margin: 0,
        fontFace: F, fontSize: 14, color: "C8CFDA", valign: "top", align: "left" }, text: "Sous-titre" } },
      { text: { text: "Every promise, carried through.", options: { x: MX, y: 6.85, w: 5, h: 0.3, margin: 0, valign: "middle",
        fontFace: F, fontSize: 9, italic: true, color: HEX.sky } } },
      { text: { text: place, options: { x: 9.2, y: 6.85, w: 3.53, h: 0.3, margin: 0, align: "right", valign: "middle",
        fontFace: F, fontSize: 9, bold: true, charSpacing: 4, color: "C8CFDA" } } },
    ],
  });

  pres.defineSlideMaster({
    title: "H_DIVIDER",
    background: { path: bgSoft },
    objects: [
      wordmark(MX, 7.0, HEX.white),
      { line: { x: MX, y: 3.95, w: 1.2, h: 0, line: { color: HEX.sky, width: 1 } } },
      { placeholder: { options: { name: "num", type: "body", x: MX, y: 1.9, w: 3, h: 0.9, margin: 0,
        fontFace: F, fontSize: 44, color: HEX.sky, valign: "bottom", align: "left" }, text: "01" } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.95, w: 9, h: 0.9, margin: 0,
        fontFace: F, fontSize: 32, bold: true, color: K.white, valign: "top", align: "left" }, text: "Titre de section" } },
      { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.15, w: 7.5, h: 0.9, margin: 0,
        fontFace: F, fontSize: 14, color: "C8CFDA", valign: "top", align: "left" }, text: "Ce que la section démontre" } },
    ],
    slideNumber: { x: 12.23, y: 7.0, w: 0.5, h: 0.3, fontFace: F, fontSize: 9, color: "C8CFDA", align: "right", valign: "middle", margin: 0 },
  });

  pres.defineSlideMaster({
    title: "H_END",
    background: { path: bgStrong },
    objects: [
      wordmark(MX, 0.6, HEX.white, 12),
      { line: { x: MX, y: 3.95, w: 1.2, h: 0, line: { color: HEX.sky, width: 1 } } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.4, w: 8.5, h: 1.4, margin: 0,
        fontFace: F, fontSize: 30, bold: true, color: K.white, valign: "bottom", align: "left" }, text: "Message de clôture" } },
      { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.15, w: 8, h: 1.0, margin: 0,
        fontFace: F, fontSize: 12, color: "C8CFDA", valign: "top", align: "left" }, text: "Contact" } },
    ],
  });
}

function content(pres, sec, { title, subtitle, source }) {
  const s = pres.addSlide({ masterName: "H_CONTENT", sectionTitle: sec });
  s.addText(title, { placeholder: "title" });
  s.addText((subtitle || " ").toUpperCase(), { placeholder: "subtitle" });
  s.addText(source || " ", { placeholder: "source" });
  return s;
}
function dark(pres, sec, { title, subtitle, source }) {
  const s = pres.addSlide({ masterName: "H_DARK", sectionTitle: sec });
  s.addText(title || " ", { placeholder: "title" });
  s.addText((subtitle || " ").toUpperCase(), { placeholder: "subtitle" });
  s.addText(source || " ", { placeholder: "source" });
  return s;
}
// Morph transition on every slide (fade fallback for older PowerPoint)
async function morph(file) {
  const JSZip = require("jszip");
  const fs = require("fs");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const tr = '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159"><p:transition spd="slow" p14:dur="1200" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"><p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>';
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))) {
    let x = await zip.file(name).async("string");
    if (x.includes("p159:morph")) continue;
    x = x.replace(/<p:transition[\s\S]*?<\/p:transition>|<p:transition[^>]*\/>/, "");
    x = x.includes("</p:clrMapOvr>") ? x.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + tr) : x.replace(/(<\/p:cSld>)/, "$1" + tr);
    zip.file(name, x);
  }
  // Arabic script falls back to the charte's Arabic font, not Office's default
  for (const name of Object.keys(zip.files).filter((n) => /^ppt\/theme\/theme\d+\.xml$/.test(n))) {
    const x = await zip.file(name).async("string");
    zip.file(name, x.replace(/<a:font script="Arab" typeface="[^"]*"\/>/g, `<a:font script="Arab" typeface="${FA}"/>`));
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}
function cover(pres, sec, o) {
  const s = pres.addSlide({ masterName: "H_COVER", sectionTitle: sec });
  s.addText(o.title, { placeholder: "title" }); s.addText(o.subtitle, { placeholder: "subtitle" }); s.addText(o.meta.toUpperCase(), { placeholder: "meta" });
  return s;
}
function divider(pres, sec, o) {
  const s = pres.addSlide({ masterName: "H_DIVIDER", sectionTitle: sec });
  s.addText(o.num.replace(/^\./, ""), { placeholder: "num" }); s.addText(o.title, { placeholder: "title" }); s.addText(o.body, { placeholder: "body" });
  return s;
}
function ending(pres, sec, o) {
  const s = pres.addSlide({ masterName: "H_END", sectionTitle: sec });
  s.addText(o.title, { placeholder: "title" }); s.addText(o.body, { placeholder: "body" });
  return s;
}

// Every text box goes through T: the 9 pt floor is enforced here, not left to each slide.
const T = (o) => {
  const r = Object.assign({ isTextBox: true, margin: 0, fontFace: F, valign: "top", fontSize: 11 }, o);
  if (r.fontSize < MIN) r.fontSize = MIN;
  return r;
};
const floorRuns = (runs) => (Array.isArray(runs) ? runs.map((x) => (x.options && x.options.fontSize < MIN ? Object.assign({}, x, { options: Object.assign({}, x.options, { fontSize: MIN }) }) : x)) : runs);

// Dark header band, small tracked capitals
function bar(s, K, text, x, y, w, h, o) {
  o = o || {};
  s.addShape("rect", { x, y, w, h, fill: { color: o.fill || K.navy }, line: { type: "none" }, objectName: "Bandeau" });
  s.addText(o.keepCase ? text : text.toUpperCase(), T({ x: x + 0.15, y, w: w - 0.3, h, valign: "middle", align: o.align || "left",
    fontSize: o.fontSize ? Math.min(o.fontSize, 11) - 1 : 9, bold: true, charSpacing: 1.5, color: o.color || K.white }));
}
function cell(s, K, text, x, y, w, h, o) {
  o = o || {};
  s.addShape("rect", { x, y, w, h, fill: { color: o.fill || K.grey }, line: { type: "none" }, objectName: "Cellule" });
  if (text) s.addText(text, T(Object.assign({ x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h - 0.16, fontSize: 10, color: K.black }, o.text || {})));
}
function box(s, K, x, y, w, h, color) {
  s.addShape("rect", { x, y, w, h, fill: { color: K.white }, line: { color: color && color !== HEX.black ? color : HEX.line, width: 0.75 }, objectName: "Cadre" });
}
// Eyebrow label + hairline
function colHead(s, K, text, x, y, w, o) {
  o = o || {};
  s.addText(text.toUpperCase(), T({ x, y, w, h: 0.3, valign: "bottom", fontSize: 9, bold: true, charSpacing: 2, color: o.color || HEX.blue }));
  s.addShape("line", { x, y: y + 0.38, w: o.lineW || w, h: 0, line: { color: HEX.black, width: 0.5 }, objectName: "Filet" });
}
function square(s, K, x, y, d, fill) {
  const k = Math.min(d, 0.12);
  s.addShape("rect", { x: x + (d - k) / 2, y: y + (d - k) / 2, w: k, h: k, fill: { color: fill || HEX.sky }, line: { type: "none" }, objectName: "Repère" });
}
function numBlock(s, K, n, x, y, w, h, fill) {
  s.addShape("rect", { x, y, w, h, fill: { color: fill || K.navy }, line: { type: "none" } });
  s.addText(n, T({ x: x + 0.12, y, w: w - 0.2, h, valign: "middle", fontSize: 22, color: K.white }));
}
function para(s, K, text, x, y, w, h, o) {
  s.addText(text, T(Object.assign({ x, y, w, h, fontSize: 11, color: K.black, lineSpacingMultiple: 1.1 }, o || {})));
}
function bullets(s, K, items, x, y, w, h, o) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { code: "2014", indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 6 } }));
  s.addText(runs, T(Object.assign({ x, y, w, h, fontSize: 11, color: K.black, lineSpacingMultiple: 1.05 }, o || {})));
}
function stat(s, K, value, label, x, y, w, color) {
  s.addText(value, T({ x, y, w, h: 0.7, valign: "bottom", fontSize: 30, bold: true, color: color || K.navy }));
  s.addText(label, T({ x, y: y + 0.8, w, h: 0.75, fontSize: 10, color: HEX.text2 }));
}
function tag(s, K, text, x, y, w, fill) {
  s.addShape("rect", { x, y, w, h: 0.26, fill: { color: fill }, line: { type: "none" }, objectName: "Statut" });
  s.addText(text, T({ x, y, w, h: 0.26, align: "center", valign: "middle", fontSize: 9, bold: true, charSpacing: 1, color: K.white }));
}
function sticker(s, K, text, w) {
  w = w || 1.5;
  const x = MX + CW - w, y = 0.38;
  s.addShape("rect", { x, y, w, h: 0.26, fill: { color: K.white }, line: { color: HEX.sky, width: 0.75 }, objectName: "Sticker" });
  s.addText(text, T({ x, y, w, h: 0.26, align: "center", valign: "middle", fontSize: 9, bold: true, charSpacing: 1.5, color: HEX.blue }));
}

const iconCache = {};
async function icon(name, hex) {
  const key = name + hex;
  if (!iconCache[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Fi[name], { color: "#" + hex, size: "256", strokeWidth: 1.25 }));
    iconCache[key] = "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
  }
  return iconCache[key];
}
async function iconTile(s, K, name, x, y, d, onDark) {
  if (!onDark) s.addShape("rect", { x, y, w: d, h: d, fill: { color: K.grey }, line: { type: "none" }, objectName: "Icône" });
  const p = onDark ? 0.05 : d * 0.22;
  s.addImage({ data: await icon(name, onDark ? HEX.sky : HEX.navy), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: name.replace(/^Fi/, "") });
}

function chartBase(extra) {
  return Object.assign({
    catAxisLabelColor: HEX.black, valAxisLabelColor: HEX.text2,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", legendFontFace: "+mn-lt",
    catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, dataLabelFontSize: 10, dataLabelColor: HEX.black,
    catAxisLineShow: true, catAxisLineColor: HEX.line,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, showTitle: false,
  }, extra);
}

module.exports = { pptxgen, HEX, THEME, W, H, MX, CW, COL, GUT, colX, spanW, newPres, F, FA, MIN, floorRuns,
  content, dark, morph, cover, divider, ending, T, bar, cell, box, colHead, square, numBlock, para, bullets, stat, tag, sticker, icon, iconTile, chartBase };
