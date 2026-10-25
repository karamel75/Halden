// Halden impact models: hero numbers, dark charts, waterfall, donut, expansion rings, timeline, quote, before/after, dashboard, team, bilingual cover
const L = require("./lib5");
const { HEX, MX, CW, colX, spanW, T, F } = L;

const SOFT = "C8CFDA", MUTED = "8C96A8", TRACK = "1E2B45";

function darkSticker(s, text, w) {
  w = w || 1.5;
  const x = MX + CW - w, y = 0.38;
  s.addShape("rect", { x, y, w, h: 0.26, fill: { color: HEX.navy, transparency: 100 }, line: { color: HEX.sky, width: 0.75 }, objectName: "Sticker" });
  s.addText(text, T({ x, y, w, h: 0.26, align: "center", valign: "middle", fontSize: 9, bold: true, charSpacing: 1.5, color: HEX.sky }));
}
const hair = (s, x, y, w, color, t) => s.addShape("line", { x, y, w, h: 0, line: { color: color || HEX.sky, width: 0.75, transparency: t || 0 } });
const vhair = (s, x, y, h, color, t) => s.addShape("line", { x, y, w: 0, h, line: { color: color || HEX.sky, width: 0.75, transparency: t || 0 } });
const eyebrow = (s, text, x, y, w, color) => s.addText(text.toUpperCase(), T({ x, y, w, h: 0.28, valign: "bottom", fontSize: 9, bold: true, charSpacing: 2.5, color: color || HEX.sky }));

// 1. Hero number: one figure fills the slide
function hero(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  if (o.sticker) darkSticker(s, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  s.addText(o.value, T({ x: MX - 0.05, y: 2.0, w: CW, h: 2.2, valign: "bottom", fontSize: o.size || 120, bold: true, color: HEX.white, charSpacing: -2, objectName: "!!hero" }));
  if (o.unit) s.addText(o.unit.toUpperCase(), T({ x: MX, y: 4.25, w: 6, h: 0.4, fontSize: 14, bold: true, charSpacing: 4, color: HEX.sky }));
  hair(s, MX, 4.85, 1.2);
  s.addText(o.label, T({ x: MX, y: 5.05, w: 7.2, h: 1.2, fontSize: 16, color: SOFT, lineSpacingMultiple: 1.1 }));
  return s;
}

// 2. Three figures separated by champagne hairlines
function heroRow(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  const w = CW / 3;
  o.items.forEach(([v, u, l], i) => {
    const x = MX + i * w;
    if (i) vhair(s, x, 2.3, 3.6, HEX.sky, 40);
    const px = x + (i ? 0.45 : 0);
    s.addText(v, T({ x: px, y: 2.2, w: w - 0.5, h: 1.5, valign: "bottom", fontSize: 66, bold: true, color: i === o.accent ? HEX.sky : HEX.white, charSpacing: -1 }));
    s.addText(u.toUpperCase(), T({ x: px, y: 3.85, w: w - 0.5, h: 0.3, fontSize: 9, bold: true, charSpacing: 3, color: HEX.sky }));
    s.addText(l, T({ x: px, y: 4.35, w: w - 0.8, h: 1.4, fontSize: 13, color: SOFT, lineSpacingMultiple: 1.1 }));
  });
  return s;
}

// 3. Statement: one sentence, very large
function statement(pres, sec, o) {
  const s = pres.addSlide({ masterName: "H_DIVIDER", sectionTitle: sec });
  s.addText(" ", { placeholder: "num" }); s.addText(" ", { placeholder: "body" });
  s.addText(o.line1, { placeholder: "title" });
  s.addText(o.line2, T({ x: MX, y: 4.15, w: 10.5, h: 1.4, fontSize: 32, bold: true, color: HEX.sky, lineSpacingMultiple: 0.95 }));
  return s;
}

// 4. Line chart on midnight, one hero series in champagne
function darkLine(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  if (o.sticker) darkSticker(s, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  const cw = 8.3;
  eyebrow(s, o.chartTitle, MX, 1.65, cw);
  hair(s, MX, 2.03, cw, HEX.sky, 50);
  s.addChart(pres.charts.LINE, o.series, L.chartBase({
    x: MX - 0.1, y: 2.2, w: cw + 0.2, h: 4.5, chartColors: [MUTED, HEX.sky], lineSize: 3, lineDataSymbol: "none",
    catAxisLabelColor: SOFT, valAxisLabelColor: MUTED, catAxisLineColor: TRACK, valAxisHidden: false, valAxisLineShow: false,
    valGridLine: { color: TRACK, size: 0.5 }, valAxisMaxVal: 100, valAxisMinVal: 0, valAxisMajorUnit: 25, valAxisLabelFormatCode: '0" %"',
    showLegend: false }));
  const rx = MX + cw + 0.6, rw = CW - cw - 0.6;
  o.legend.forEach(([name, color, value, note], i) => {
    const y = 2.2 + i * 2.1;
    s.addShape("line", { x: rx, y: y + 0.12, w: 0.5, h: 0, line: { color, width: 3 } });
    s.addText(name.toUpperCase(), T({ x: rx + 0.65, y, w: rw - 0.65, h: 0.26, fontSize: 9, bold: true, charSpacing: 2, color }));
    s.addText(value, T({ x: rx, y: y + 0.4, w: rw, h: 0.8, valign: "bottom", fontSize: 40, bold: true, color: i ? HEX.white : SOFT }));
    s.addText(note, T({ x: rx, y: y + 1.25, w: rw, h: 0.6, fontSize: 10, color: SOFT }));
  });
  return s;
}

// 5. Waterfall built from shapes
function waterfall(pres, sec, o) {
  const s = L.content(pres, sec, o);
  if (o.sticker) L.sticker(s, { white: HEX.white }, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  const x0 = MX, y0 = 1.75, chH = 4.2, base = y0 + chH, n = o.steps.length;
  const max = o.steps[0][1], k = (chH - 0.8) / max, slot = 8.4 / n, bw = slot * 0.62;
  L.colHead(s, null, o.chartTitle, x0, 1.55, 8.4);
  let level = 0;
  o.steps.forEach(([lab, v, kind], i) => {
    const x = x0 + i * slot + (slot - bw) / 2;
    let top, h, fill;
    if (kind === "total") { top = base - v * k; h = v * k; fill = HEX.navy; level = v; }
    else if (kind === "end") { top = base - v * k; h = v * k; fill = HEX.teal; }
    else { top = base - level * k; h = v * k; fill = HEX.mid; level -= v; }
    s.addShape("rect", { x, y: top, w: bw, h: Math.max(h, 0.04), fill: { color: fill }, line: { type: "none" } });
    s.addText((kind === "step" ? "−" : "") + v, T({ x: x - 0.2, y: top - 0.42, w: bw + 0.4, h: 0.36, align: "center", valign: "bottom", fontSize: 16, bold: true, color: kind === "end" ? HEX.teal : HEX.navy }));
    s.addText(lab, T({ x: x - 0.25, y: base + 0.12, w: bw + 0.5, h: 0.6, align: "center", fontSize: 9.5, color: HEX.text2 }));
    if (i < n - 1) s.addShape("line", { x: x + bw, y: base - level * k, w: slot - bw, h: 0, line: { color: HEX.steel, width: 0.75, dashType: "dash" } });
  });
  s.addShape("line", { x: x0, y: base, w: 8.4, h: 0, line: { color: HEX.line, width: 0.75 } });
  const rx = MX + 8.9, rw = CW - 8.9;
  s.addShape("rect", { x: rx, y: 1.75, w: rw, h: 4.95, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText(o.side.value, T({ x: rx + 0.3, y: 2.05, w: rw - 0.6, h: 1.1, valign: "bottom", fontSize: 54, bold: true, color: HEX.sky }));
  hair(s, rx + 0.3, 3.35, 0.8);
  s.addText(o.side.text, T({ x: rx + 0.3, y: 3.55, w: rw - 0.6, h: 2.9, fontSize: 12, color: HEX.white, lineSpacingMultiple: 1.15 }));
  return s;
}

// 6. Donut with the figure in the hole
function donut(pres, sec, o) {
  const s = L.content(pres, sec, o);
  if (o.sticker) L.sticker(s, { white: HEX.white }, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  const d = 4.4, x = MX + 0.3, y = 1.85;
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Part", labels: ["Oui", "Non"], values: [o.pct, 100 - o.pct] }], L.chartBase({
    x, y, w: d, h: d, holeSize: 78, chartColors: [HEX.navy, HEX.grey], showValue: false, showPercent: false, showLabel: false, dataBorder: { pt: 0, color: "FFFFFF" }, firstSliceAng: 0 }));
  s.addText(o.pct + " %", T({ x, y: y + d / 2 - 0.55, w: d, h: 0.8, align: "center", valign: "middle", fontSize: 44, bold: true, color: HEX.navy }));
  s.addText(o.centerLabel.toUpperCase(), T({ x: x + 0.9, y: y + d / 2 + 0.25, w: d - 1.8, h: 0.5, align: "center", fontSize: 9, bold: true, charSpacing: 2, color: HEX.blue }));
  const rx = MX + 5.6, rw = CW - 5.6;
  o.rows.forEach(([v, l], i) => {
    const yy = 1.9 + i * 1.5;
    s.addText(v, T({ x: rx, y: yy, w: 2.4, h: 0.9, valign: "middle", fontSize: 32, bold: true, color: i === 0 ? HEX.teal : HEX.navy }));
    s.addText(l, T({ x: rx + 2.6, y: yy, w: rw - 2.6, h: 0.9, valign: "middle", fontSize: 12, color: HEX.black }));
    if (i < o.rows.length - 1) s.addShape("line", { x: rx, y: yy + 1.2, w: rw, h: 0, line: { color: HEX.line, width: 0.75 } });
  });
  return s;
}

// 7. Expansion rings around Dubai (schematic, not to scale)
function rings(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  const cx = 4.4, cy = 4.35;
  [0.95, 1.8, 2.6].forEach((r, i) => s.addShape("ellipse", { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { color: HEX.navy, transparency: 100 }, line: { color: HEX.sky, width: 0.75, transparency: 35 + i * 20 } }));
  s.addShape("ellipse", { x: cx - 0.45, y: cy - 0.45, w: 0.9, h: 0.9, fill: { color: HEX.sky, transparency: 82 }, line: { type: "none" } });
  s.addShape("ellipse", { x: cx - 0.12, y: cy - 0.12, w: 0.24, h: 0.24, fill: { color: HEX.sky }, line: { type: "none" } });
  const style = { live: [HEX.sky, HEX.sky], next: [HEX.white, HEX.white], test: [HEX.navy, HEX.sky], later: ["5B6472", "5B6472"] };
  o.points.forEach(([name, ang, r, st, align]) => {
    const a = (ang * Math.PI) / 180, px = cx + r * Math.cos(a), py = cy - r * Math.sin(a), d = 0.16;
    const [fill, line] = style[st];
    s.addShape("ellipse", { x: px - d / 2, y: py - d / 2, w: d, h: d, fill: { color: fill }, line: { color: line, width: 1.25 } });
    const left = align === "l";
    s.addText(name, T({ x: left ? px - 1.95 : px + 0.15, y: py - 0.15, w: 1.8, h: 0.3, valign: "middle", align: left ? "right" : "left", fontSize: 10, bold: st !== "later", color: st === "later" ? MUTED : HEX.white }));
  });
  s.addText("Dubaï", T({ x: cx - 1, y: cy + 0.2, w: 2, h: 0.3, align: "center", fontSize: 11, bold: true, color: HEX.sky }));
  const rx = MX + 8.2, rw = CW - 8.2;
  eyebrow(s, o.legendTitle || "Statut par marché", rx, 1.75, rw);
  hair(s, rx, 2.13, rw, HEX.sky, 50);
  o.legend.forEach(([st, label, text], i) => {
    const y = 2.4 + i * 1.05, [fill, line] = style[st];
    s.addShape("ellipse", { x: rx, y: y + 0.06, w: 0.16, h: 0.16, fill: { color: fill }, line: { color: line, width: 1.25 } });
    s.addText(label.toUpperCase(), T({ x: rx + 0.35, y, w: rw - 0.35, h: 0.28, fontSize: 9, bold: true, charSpacing: 2, color: st === "later" ? MUTED : HEX.white }));
    s.addText(text, T({ x: rx + 0.35, y: y + 0.32, w: rw - 0.35, h: 0.6, fontSize: 10.5, color: SOFT }));
  });
  return s;
}

// 8. Horizontal timeline on midnight with one glowing stage
function timeline(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  const y = 4.3, n = o.stages.length, step = CW / n;
  s.addShape("line", { x: MX, y, w: CW, h: 0, line: { color: HEX.sky, width: 1, transparency: 50 } });
  o.stages.forEach(([name, period, sub], i) => {
    const cx = MX + step * i + step / 2, hot = i === o.hot;
    if (hot) {
      s.addShape("ellipse", { x: cx - 0.4, y: y - 0.4, w: 0.8, h: 0.8, fill: { color: HEX.sky, transparency: 80 }, line: { type: "none" } });
      s.addShape("rect", { x: cx - step / 2 + 0.1, y: 2.0, w: step - 0.2, h: 1.55, fill: { color: HEX.sky, transparency: 88 }, line: { color: HEX.sky, width: 0.75 } });
      s.addText(o.hotLabel.toUpperCase(), T({ x: cx - step / 2 + 0.2, y: 2.12, w: step - 0.4, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
      s.addText(o.hotText, T({ x: cx - step / 2 + 0.2, y: 2.45, w: step - 0.4, h: 1.0, fontSize: 10.5, color: HEX.white }));
      vhair(s, cx, 3.55, 0.55, HEX.sky);
    }
    const d = hot ? 0.26 : 0.16;
    s.addShape("ellipse", { x: cx - d / 2, y: y - d / 2, w: d, h: d, fill: { color: hot ? HEX.sky : HEX.navy }, line: { color: HEX.sky, width: 1.25 } });
    s.addText(String(i + 1).padStart(2, "0"), T({ x: cx - step / 2, y: y + 0.35, w: step, h: 0.45, align: "center", fontSize: 20, color: hot ? HEX.sky : MUTED }));
    s.addText(name, T({ x: cx - step / 2 + 0.1, y: y + 0.85, w: step - 0.2, h: 0.55, align: "center", fontSize: 11.5, bold: true, color: HEX.white }));
    s.addText(period.toUpperCase(), T({ x: cx - step / 2 + 0.1, y: y + 1.42, w: step - 0.2, h: 0.28, align: "center", fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
    s.addText(sub, T({ x: cx - step / 2 + 0.15, y: y + 1.75, w: step - 0.3, h: 0.6, align: "center", fontSize: 9.5, color: SOFT }));
  });
  return s;
}

// 9. Quote
function quote(pres, sec, o) {
  const s = pres.addSlide({ masterName: "H_DIVIDER", sectionTitle: sec });
  s.addText(" ", { placeholder: "num" }); s.addText(" ", { placeholder: "title" }); s.addText(" ", { placeholder: "body" });
  s.addText("“", T({ x: MX - 0.08, y: 0.9, w: 2, h: 1.8, fontSize: 160, bold: true, color: HEX.sky }));
  s.addText(o.text, T({ x: MX, y: 2.3, w: 10.6, h: 1.5, valign: "bottom", fontSize: 30, color: HEX.white, lineSpacingMultiple: 1.05 }));
  s.addText(o.who.toUpperCase(), T({ x: MX, y: 4.15, w: 9, h: 0.3, fontSize: 9, bold: true, charSpacing: 3, color: HEX.sky }));
  return s;
}

// 10. Before / after split
async function beforeAfter(pres, sec, o) {
  const s = L.content(pres, sec, o);
  if (o.sticker) L.sticker(s, { white: HEX.white }, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  const y = 1.75, h = 4.95, w = (CW - 0.3) / 2, x2 = MX + w + 0.3;
  s.addShape("rect", { x: MX, y, w, h, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addShape("rect", { x: x2, y, w, h, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText(o.leftTitle.toUpperCase(), T({ x: MX + 0.4, y: y + 0.35, w: w - 0.8, h: 0.3, fontSize: 9, bold: true, charSpacing: 3, color: HEX.text2 }));
  s.addText(o.rightTitle.toUpperCase(), T({ x: x2 + 0.4, y: y + 0.35, w: w - 0.8, h: 0.3, fontSize: 9, bold: true, charSpacing: 3, color: HEX.sky }));
  o.rows.forEach(([a, b], i) => {
    const yy = y + 0.95 + i * 0.98;
    s.addShape("line", { x: MX + 0.4, y: yy - 0.12, w: w - 0.8, h: 0, line: { color: HEX.line, width: 0.75 } });
    s.addShape("line", { x: x2 + 0.4, y: yy - 0.12, w: w - 0.8, h: 0, line: { color: HEX.sky, width: 0.75, transparency: 60 } });
    s.addText("—", T({ x: MX + 0.4, y: yy, w: 0.4, h: 0.75, valign: "middle", fontSize: 12, color: HEX.text2 }));
    s.addText(a, T({ x: MX + 0.85, y: yy, w: w - 1.25, h: 0.75, valign: "middle", fontSize: 12, color: HEX.text2 }));
    s.addText("✓", T({ x: x2 + 0.4, y: yy, w: 0.4, h: 0.75, valign: "middle", fontSize: 13, bold: true, color: HEX.sky }));
    s.addText(b, T({ x: x2 + 0.85, y: yy, w: w - 1.25, h: 0.75, valign: "middle", fontSize: 12, bold: true, color: HEX.white }));
  });
  const d = 0.62, cx = MX + w + 0.15;
  s.addShape("ellipse", { x: cx - d / 2, y: y + h / 2 - d / 2, w: d, h: d, fill: { color: HEX.teal }, line: { color: HEX.white, width: 2 } });
  s.addImage({ data: await L.icon("FiArrowRight", "FFFFFF"), x: cx - 0.17, y: y + h / 2 - 0.17, w: 0.34, h: 0.34, altText: "Flèche" });
  return s;
}

// 11. Live dashboard on midnight
function dashboard(pres, sec, o) {
  const s = L.dark(pres, sec, o);
  if (o.sticker) darkSticker(s, o.sticker, o.stickerW || Math.max(1.5, 0.12 * o.sticker.length + 0.3));
  const w = (CW - 0.6) / 4;
  o.tiles.forEach(([lab, v, sub, pct], i) => {
    const x = MX + i * (w + 0.2), y = 1.75;
    s.addShape("rect", { x, y, w, h: 2.0, fill: { color: "FFFFFF", transparency: 95 }, line: { color: HEX.sky, width: 0.5, transparency: 70 } });
    s.addText(lab.toUpperCase(), T({ x: x + 0.25, y: y + 0.2, w: w - 0.5, h: 0.28, fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
    s.addText(v, T({ x: x + 0.25, y: y + 0.5, w: w - 0.5, h: 0.75, valign: "middle", fontSize: 32, bold: true, color: i === o.alert ? "F0A39A" : HEX.white }));
    s.addText(sub, T({ x: x + 0.25, y: y + 1.25, w: w - 0.5, h: 0.3, fontSize: 9, color: SOFT }));
    s.addShape("rect", { x: x + 0.25, y: y + 1.68, w: w - 0.5, h: 0.06, fill: { color: TRACK }, line: { type: "none" } });
    s.addShape("rect", { x: x + 0.25, y: y + 1.68, w: (w - 0.5) * pct, h: 0.06, fill: { color: i === o.alert ? "F0A39A" : HEX.sky }, line: { type: "none" } });
  });
  eyebrow(s, o.chartTitle, MX, 4.0, CW);
  hair(s, MX, 4.38, CW, HEX.sky, 50);
  s.addChart(pres.charts.BAR, [{ name: "Série", labels: o.bars.map((b) => b[0]), values: o.bars.map((b) => b[1]) }], L.chartBase({
    x: MX - 0.1, y: 4.5, w: CW + 0.2, h: 2.3, barDir: "col", barGapWidthPct: 45, chartColors: o.bars.map((b, i) => (i === o.bars.length - 1 ? HEX.sky : "33415C")),
    catAxisLabelColor: SOFT, catAxisLineColor: TRACK, showValue: true, dataLabelColor: SOFT, dataLabelFontSize: 9, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0" }));
  return s;
}

// 12. Team with photo frames
async function team(pres, sec, o) {
  const s = L.content(pres, sec, o);
  const n = o.people.length, w = (CW - (n - 1) * 0.25) / n, d = Math.min(1.9, w - 0.4);
  for (let i = 0; i < n; i++) {
    const [name, role, line, hot] = o.people[i], x = MX + i * (w + 0.25), cx = x + w / 2;
    s.addShape("ellipse", { x: cx - d / 2, y: 1.85, w: d, h: d, fill: { color: HEX.grey }, line: { color: hot ? HEX.teal : HEX.line, width: hot ? 1.5 : 0.75 } });
    s.addImage({ data: await L.icon("FiUser", HEX.mid), x: cx - 0.35, y: 1.85 + d / 2 - 0.35, w: 0.7, h: 0.7, altText: "Photo à insérer" });
    s.addText(name, T({ x, y: 2.0 + d, w, h: 0.4, align: "center", valign: "middle", fontSize: 13, bold: true, color: HEX.navy }));
    s.addText(role.toUpperCase(), T({ x, y: 2.42 + d, w, h: 0.3, align: "center", fontSize: 9, bold: true, charSpacing: 2, color: HEX.blue }));
    s.addShape("line", { x: cx - 0.3, y: 2.85 + d, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(line, T({ x: x + 0.1, y: 3.0 + d, w: w - 0.2, h: 1.0, align: "center", fontSize: 10, color: HEX.text2 }));
  }
  return s;
}

// 13. Bilingual cover (French or English + Arabic)
function bilingualCover(pres, sec, o) {
  const s = L.cover(pres, sec, o);
  vhair(s, 8.7, 2.0, 3.3, HEX.sky, 50);
  s.addText("هالدن", T({ x: 8.9, y: 1.9, w: 3.83, h: 1.6, align: "right", valign: "bottom", fontFace: L.FA, fontSize: 72, bold: true, color: HEX.sky, rtlMode: true, lang: "ar-AE" }));
  s.addText("كل وعد، حتى يتحقق", T({ x: 8.9, y: 3.65, w: 3.83, h: 0.5, align: "right", fontFace: L.FA, fontSize: 18, color: HEX.white, rtlMode: true, lang: "ar-AE" }));
  return s;
}

// 14. Morph pair: a figure zooms out and the detail appears
async function morphPair(pres, sec, o) {
  let s = L.dark(pres, sec, { subtitle: o.subtitle, title: " ", source: o.source });
  s.addText(o.value, T({ x: 0, y: 1.9, w: 13.333, h: 3.0, align: "center", valign: "middle", fontSize: 180, bold: true, color: HEX.white, objectName: "!!chiffre" }));
  s.addText(o.label, T({ x: 2, y: 5.0, w: 9.333, h: 0.6, align: "center", fontSize: 16, color: SOFT, objectName: "!!legende" }));
  s = L.dark(pres, sec, o);
  s.addText(o.value, T({ x: MX, y: 1.7, w: 3.2, h: 1.4, valign: "middle", fontSize: 72, bold: true, color: HEX.sky, objectName: "!!chiffre" }));
  s.addText(o.label, T({ x: MX, y: 3.1, w: 3.0, h: 1.0, fontSize: 12, color: SOFT, objectName: "!!legende" }));
  const x0 = MX + 3.8, w = (CW - 3.8 - 0.6) / 4;
  for (let i = 0; i < o.items.length; i++) {
    const [ic, h, b] = o.items[i], x = x0 + i * (w + 0.2);
    s.addShape("rect", { x, y: 1.75, w, h: 4.9, fill: { color: "FFFFFF", transparency: 95 }, line: { color: HEX.sky, width: 0.5, transparency: 70 } });
    await L.iconTile(s, null, ic, x + 0.3, 2.05, 0.6, true);
    s.addText(h, T({ x: x + 0.3, y: 2.95, w: w - 0.6, h: 0.6, fontSize: 13, bold: true, color: HEX.white }));
    hair(s, x + 0.3, 3.65, 0.5);
    s.addText(b, T({ x: x + 0.3, y: 3.85, w: w - 0.6, h: 2.5, fontSize: 10.5, color: SOFT, lineSpacingMultiple: 1.1 }));
  }
  return s;
}

module.exports = { hero, heroRow, statement, darkLine, waterfall, donut, rings, timeline, quote, beforeAfter, dashboard, team, bilingualCover, morphPair, darkSticker };
