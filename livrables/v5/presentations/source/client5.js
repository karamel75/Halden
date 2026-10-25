// Halden client deck v5 for prospective developers (English), with every point of the 24 Oct 2026 review applied
const L = require("./lib5");
const W = require("./wow5");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const { HEX, MX, CW, T } = L;

const SOFT = "C8CFDA";
const DEMO = "Source: Halden prototype v0.2 demo (fictitious tower of 32 buyers, invented data). Internal test bench: 0 wrong automatic matches on 200 lines written by our team";
const th = (t, fill) => ({ text: t, options: { bold: true, color: HEX.white, fill: { color: fill || HEX.navy }, fontSize: 10, valign: "middle" } });
const td = (t, o) => ({ text: t, options: Object.assign({ fontSize: 10, color: HEX.black, fill: { color: HEX.grey }, valign: "middle" }, o || {}) });
const fitW = (o) => (o.colW ? Object.assign({}, o, { colW: o.colW.map((c) => c * (o.w || CW) / o.colW.reduce((a, b) => a + b, 0)) }) : o);
const tableOpts = (o) => Object.assign({ x: MX, y: 1.75, w: CW, border: { type: "solid", pt: 3, color: HEX.white }, fontFace: L.F, margin: [0.04, 0.1, 0.04, 0.1] }, fitW(o));

async function build(out) {
  const { pres, K } = await L.newPres("Halden: client presentation", { place: "DUBAI · 2026" });
  const A = "Opening", P = "The problem", H = "Halden", C = "Trust", G = "Pilot";

  pres.addSection({ title: A });
  let s = W.bilingualCover(pres, A, { title: "The AI back office for off-plan collections", subtitle: "From certified milestone to reconciled payment", meta: "Prepared for [developer name] · October 2026" });
  s.addNotes("Arabic wordmark and tagline set in IBM Plex Sans Arabic. The tagline must be reviewed by a native Arabic speaker before this deck is shown.");
  W.statement(pres, A, { line1: "Selling the unit is the easy part.", line2: "The 30 months of payments that follow are the real work." });

  pres.addSection({ title: P });
  W.hero(pres, P, { subtitle: "Dubai off-plan market", title: "Around two thirds of Dubai's property sales are off-plan, paid in stages over construction",
    value: "686.8bn", unit: "AED · 2025 sales", label: "of property sales in Dubai in 2025, around two thirds of them off-plan",
    source: "Source: DXB Interact (Dubai Land Department data), 2025" });

  // Four tasks, stated as our hypothesis (the zoom slide was a subset of this one and is gone)
  s = L.dark(pres, P, { subtitle: "The work behind every milestone",
    title: "What we expect to hear: every certified milestone leaves four cash tasks to your finance team",
    source: "Halden hypothesis, to be confirmed in conversations with finance teams. It describes a developer with one to three projects" });
  W.darkSticker(s, "OUR HYPOTHESIS", 1.9);
  const items = [["FiFileText", "Call", "Each buyer's instalment, from their own payment plan, as soon as the milestone is certified."],
    ["FiRepeat", "Reconcile", "Every transfer matched to the right buyer, often with a missing reference or someone else's."],
    ["FiBell", "Chase", "Late buyers, in Arabic or English, without damaging the relationship."],
    ["FiArchive", "Document", "A clean file for the project escrow account, the auditors and any dispute."]];
  const iw = (CW - 0.6) / 4;
  for (let i = 0; i < 4; i++) {
    const [ic, h, b] = items[i], x = MX + i * (iw + 0.2);
    s.addShape("rect", { x, y: 1.8, w: iw, h: 4.85, fill: { color: "FFFFFF", transparency: 95 }, line: { color: HEX.sky, width: 0.5, transparency: 70 } });
    await L.iconTile(s, K, ic, x + 0.3, 2.1, 0.6, true);
    s.addText(h, T({ x: x + 0.3, y: 3.0, w: iw - 0.6, h: 0.6, fontSize: 20, bold: true, color: HEX.white }));
    s.addShape("line", { x: x + 0.3, y: 3.75, w: 0.5, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x: x + 0.3, y: 3.95, w: iw - 0.6, h: 2.4, fontSize: 11.5, color: SOFT, lineSpacingMultiple: 1.1 }));
  }

  W.timeline(pres, P, { subtitle: "The off-plan buyer journey", title: "We start with one step of the journey: the staged payments, for one tower",
    stages: [["Reserve", "Month 0", "Later"], ["Contract and Oqood", "Months 0–2", "Later"], ["Staged payments", "Months 1–30", "The pilot"],
      ["Construction", "Months 1–30", "Later"], ["Handover", "Around month 30", "Later"], ["Warranty", "Years 1–10", "Later"]],
    hot: 2, hotLabel: "Where we start", hotText: "One certified milestone, every buyer's request, every transfer reconciled.",
    source: "Source: Halden design. Only the staged payments step is in the pilot; the other steps are a vision, not a product" });

  pres.addSection({ title: H });
  await W.beforeAfter(pres, H, { subtitle: "Your back office after the sale", title: "With Halden, collections move from scattered tools to one approval queue", sticker: "PRODUCT TARGET",
    leftTitle: "What we expect today", rightTitle: "With Halden",
    rows: [["Payment requests rebuilt for each milestone", "Requests ready when the milestone is certified, approved by your team"],
      ["Transfers matched line by line, references missing", "Exact matches done; uncertain ones at the top of the queue"],
      ["Reminders one language at a time", "Drafts in each buyer's language, approved before sending"],
      ["Files scattered when the auditor calls", "Every action logged, escrow file ready for audit"]],
    source: "Source: Halden design; left column is our hypothesis. Product in development" });

  s = L.dark(pres, H, { subtitle: "How Halden works during the pilot", title: "Halden prepares. Your team approves every buyer message and decides every exception.",
    source: "Source: rule enforced in the Halden prototype code and checked by its tests. Oqood registration: Dubai Land Department" });
  const cw3 = (CW - 0.6) / 3;
  [["01", "Approve", "Every message to a buyer and every uncertain match waits for a named person on your team."],
    ["02", "Sign", "Contracts, Oqood registration at the DLD and legal notices stay with your team. Never the AI."],
    ["03", "Decide", "A buyer in difficulty, a disputed amount, a payment default: always a person, with the file prepared."]].forEach(([n, h, b], i) => {
    const x = MX + i * (cw3 + 0.3);
    s.addText(n, T({ x, y: 1.8, w: 1, h: 0.5, fontSize: 18, color: HEX.sky }));
    s.addText(h, T({ x, y: 2.3, w: cw3, h: 0.8, valign: "middle", fontSize: 34, bold: true, color: HEX.white }));
    s.addShape("line", { x, y: 3.25, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x, y: 3.45, w: cw3 - 0.2, h: 1.0, fontSize: 12, color: SOFT, lineSpacingMultiple: 1.1 }));
  });
  s.addShape("line", { x: MX, y: 4.85, w: CW, h: 0, line: { color: HEX.sky, width: 0.5, transparency: 60 } });
  s.addText("WHAT STOPS ANY AUTOMATIC CONTACT WITH A BUYER", T({ x: MX, y: 5.0, w: CW, h: 0.3, fontSize: 9, bold: true, charSpacing: 2.5, color: HEX.sky }));
  const g = [["FiCheckCircle", "\"I already paid\"", "In English, Arabic or French."],
    ["FiBriefcase", "Lawyer, complaint, hardship", "A person is alerted at once."],
    ["FiClock", "A payment pending", "Or an unidentified transfer of the same amount."]];
  for (let i = 0; i < 3; i++) {
    const x = MX + i * (cw3 + 0.3);
    await L.iconTile(s, K, g[i][0], x, 5.5, 0.5, true);
    s.addText(g[i][1], T({ x: x + 0.7, y: 5.45, w: cw3 - 0.7, h: 0.3, fontSize: 12, bold: true, color: HEX.white }));
    s.addText(g[i][2], T({ x: x + 0.7, y: 5.8, w: cw3 - 0.8, h: 0.7, fontSize: 10, color: SOFT }));
  }

  W.waterfall(pres, H, { subtitle: "Bank reconciliation for one milestone", title: "In our demo, 14 of 19 transfers are matched with no human; the other 5 go to your CFO", sticker: "DEMO · FICTITIOUS", stickerW: 2,
    chartTitle: "Transfers received for one milestone, number (demo, invented data)",
    steps: [["Transfers received", 19, "total"], ["Matched, no human", 14, "step"], ["Approved by the CFO", 4, "step"], ["Rightly refused", 1, "end"]],
    side: { value: "0", text: "messages sent to a buyer without approval. The refused transfer carried another buyer's reference: it is never matched automatically." },
    source: DEMO });

  // What the CFO gains, escrow-aware (replaces the dashboard and its second 78 %)
  s = L.content(pres, H, { subtitle: "What your CFO gains",
    title: "Escrow releases cash at the pace of construction; Halden gives your CFO fewer delays, less team time and an audit-ready file",
    source: "Escrow: Dubai Law No. 8 of 2007. Gains are product targets, to be measured against your own baseline during the pilot" });
  L.sticker(s, K, "PRODUCT TARGET", 1.9);
  s.addShape("rect", { x: MX, y: 1.8, w: CW, h: 0.85, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "What Halden does not do: ", options: { bold: true, color: HEX.teal } },
    { text: "make escrow cash available sooner. Buyer payments stay in the project escrow account and are released as construction is certified." }],
    T({ x: MX + 0.25, y: 1.8, w: CW - 0.5, h: 0.85, valign: "middle", fontSize: 11.5, color: HEX.black }));
  const gains = [["FiTrendingDown", "Fewer delays", "Every late instalment followed up the same week, in the buyer's language, and stopped the moment the buyer replies."],
    ["FiClock", "Less team time", "Your team reviews a queue of exceptions instead of rebuilding requests and matching transfers line by line."],
    ["FiFolder", "An audit-ready file", "Each request, payment, reminder and approval logged in a signed trail, ready for every escrow release request."]];
  for (let i = 0; i < 3; i++) {
    const [ic, h, b] = gains[i], x = MX + i * (cw3 + 0.3);
    await L.iconTile(s, K, ic, x, 3.0, 0.7);
    s.addText(h, T({ x, y: 3.9, w: cw3, h: 0.5, fontSize: 20, bold: true, color: HEX.navy }));
    s.addShape("line", { x, y: 4.5, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x, y: 4.7, w: cw3 - 0.2, h: 1.5, fontSize: 12, color: HEX.black, lineSpacingMultiple: 1.1 }));
  }

  // Why not my ERP?
  s = L.content(pres, H, { subtitle: "Why not my ERP?",
    title: "Your ERP stores the plan and sends the reminder; Halden does the work your team still does around it",
    source: "Sources: product pages of Akarati, RealSoft (Coral) and In4Suite, read on 24 October 2026. Halden answers are ours, to be tested with you" });
  s.addTable([
    [th("The work"), th("A typical UAE real estate ERP"), th("Halden", HEX.teal)],
    [td("Payment plans and invoices", { bold: true, color: HEX.navy }), td("Yes: plans, invoices, scheduled reminders"), td("Reads them from your ERP export; does not replace it")],
    [td("A transfer with no reference, or someone else's", { bold: true, color: HEX.navy }), td("Left to your team"), td("Proposes the match with its reason; never automatic when the payer does not match")],
    [td("A buyer replies \"I already paid\" or mentions a lawyer", { bold: true, color: HEX.navy }), td("Scheduled reminders may keep going"), td("Every automatic contact stops; a person is alerted")],
    [td("Messages in Arabic and English", { bold: true, color: HEX.navy }), td("Templates"), td("Drafts with the buyer's own figures, every amount checked against the plan")],
    [td("Escrow and audit file", { bold: true, color: HEX.navy }), td("Postings and reports"), td("A signed log of every request, match, message and approval")],
  ], tableOpts({ y: 1.75, colW: [3.3, 3.8, 5.0], rowH: [0.38, 0.62, 0.72, 0.72, 0.62, 0.62] }));
  s.addShape("rect", { x: MX, y: 5.75, w: CW, h: 0.9, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "No ERP yet? ", options: { bold: true, color: HEX.sky } }, { text: "Halden works from your spreadsheets and bank statements, without an ERP project.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.75, w: CW - 0.6, h: 0.9, valign: "middle", fontSize: 13 }));

  pres.addSection({ title: C });
  s = L.content(pres, C, { subtitle: "Dubai rule pack", title: "We are preparing a Dubai rule pack, to be validated by a UAE lawyer before any live use",
    source: "Sources: Dubai Law No. 8 of 2007; Law No. 13 of 2008, art. 11, amended by Law No. 19 of 2017; Al Tamimi & Co. Summaries, not legal advice" });
  L.sticker(s, K, "IN PREPARATION", 1.8);
  [["Escrow", "One escrow account per project", "Buyer payments go to the project escrow account; Halden prepares and reconciles, it never holds or moves funds."],
    ["Oqood", "Every off-plan sale registered", "Payment plans stay consistent with the sale registered at the DLD; registration stays with your team."],
    ["Default", "The DLD procedure", "At 30 days late, Halden prepares the DLD default notice file and the options by completion level. Your team decides."]].forEach(([v, h, b], i) => {
    const w = (CW - 0.6) / 3, x = MX + i * (w + 0.3);
    s.addShape("rect", { x, y: 1.75, w, h: 3.6, fill: { color: i === 0 ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(v, T({ x: x + 0.35, y: 2.0, w: w - 0.7, h: 1.0, valign: "bottom", fontSize: 38, bold: true, color: i === 0 ? HEX.sky : HEX.navy }));
    s.addShape("line", { x: x + 0.35, y: 3.2, w: 0.6, h: 0, line: { color: i === 0 ? HEX.sky : HEX.teal, width: 0.75 } });
    s.addText(h.toUpperCase(), T({ x: x + 0.35, y: 3.4, w: w - 0.7, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: i === 0 ? HEX.white : HEX.blue }));
    s.addText(b, T({ x: x + 0.35, y: 3.8, w: w - 0.7, h: 1.4, fontSize: 11, color: i === 0 ? SOFT : HEX.black, lineSpacingMultiple: 1.1 }));
  });
  L.box(s, K, MX, 5.65, CW, 0.95);
  s.addText([{ text: "Every rule is a line in a table your lawyer can read and correct. ", options: { bold: true, color: HEX.teal } },
    { text: "Nothing in the pack is used on a real buyer until a UAE lawyer has signed it off." }],
    T({ x: MX + 0.25, y: 5.65, w: CW - 0.5, h: 0.95, valign: "middle", fontSize: 11.5, color: HEX.black }));

  // Data and security
  s = L.content(pres, C, { subtitle: "Your data", title: "Your buyers' data stays in the UAE, seen only by the people you name",
    source: "PDPL: UAE Federal Decree-Law No. 45 of 2021. AWS Middle East (UAE) Region, me-central-1. Live set-up agreed in writing before any live use" });
  const sec = [["FiMapPin", "Where it lives", "Hosting in the AWS UAE Region. During the shadow pilot: only the anonymised files you send us."],
    ["FiEyeOff", "What the AI sees", "Names, phone numbers and IBANs are replaced by markers before any AI call, then put back on our side."],
    ["FiUsers", "Who sees it", "Your team and the Halden staff you approve. Only the approvers you name can release a message."],
    ["FiShield", "The law", "Processing under the UAE PDPL, with a data processing agreement signed before the pilot."],
    ["FiList", "The trail", "Every action in a signed log: who prepared, who approved, when."],
    ["FiTrash2", "The end", "At the end of the pilot your files are returned or deleted, as you choose."]];
  for (let i = 0; i < 6; i++) {
    const [ic, h, b] = sec[i], col = i % 3, row = Math.floor(i / 3), w = (CW - 0.6) / 3, x = MX + col * (w + 0.3), y = 1.85 + row * 2.4;
    await L.iconTile(s, K, ic, x, y, 0.6);
    s.addText(h, T({ x: x + 0.8, y, w: w - 0.8, h: 0.6, valign: "middle", fontSize: 14, bold: true, color: HEX.navy }));
    s.addText(b, T({ x: x + 0.8, y: y + 0.7, w: w - 0.9, h: 1.3, fontSize: 11, color: HEX.black, lineSpacingMultiple: 1.05 }));
  }

  // Team
  s = await W.team(pres, C, { subtitle: "Who we are", title: "A four-person team from SKEMA Business School, focused on one problem: off-plan collections",
    source: "Six-month faculty-supervised programme (AI-native track, SKEMA Business School)",
    people: [["Jennifer El Karaki", "Strategy and process", "MSc Strategic Management and Consulting, SKEMA."],
      ["Karam", "Product and prototype", "Builds the Halden engine and its prototype.", true],
      ["Dhruv", "Founding member", "SKEMA Business School."],
      ["Thomas", "Founding member", "SKEMA Business School."]] });
  s.addShape("rect", { x: MX, y: 6.0, w: CW, h: 0.65, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "What exists today: ", options: { bold: true, color: HEX.teal } }, { text: "a website with an interactive demo, and a working prototype of the collections engine with 25 automated tests. No client yet: you would be the first." }],
    T({ x: MX + 0.25, y: 6.0, w: CW - 0.5, h: 0.65, valign: "middle", fontSize: 11, color: HEX.black }));

  pres.addSection({ title: G });
  // Price
  s = L.content(pres, G, { subtitle: "Indicative pricing", title: "The pilot is free; after it, an indicative AED 6 to 12 per unit per month, plus AED 15,000 per project",
    source: "Indicative prices, as on the Halden website. The final price is agreed in writing before the pilot and applies only if the success numbers are met" });
  const pr = [["AED 0", "The shadow pilot", "Four weeks, one tower, nothing sent to your buyers."], ["AED 15,000", "Set-up per project", "Rule pack, payment plans, prices and buyers imported."],
    ["AED 6–12", "Per unit, per month", "From the first call to the final instalment at handover."]];
  pr.forEach(([v, h, b], i) => {
    const w = (CW - 0.6) / 3, x = MX + i * (w + 0.3);
    s.addShape("rect", { x, y: 1.8, w, h: 3.5, fill: { color: i === 2 ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(v, T({ x: x + 0.35, y: 2.1, w: w - 0.7, h: 1.1, valign: "bottom", fontSize: 32, bold: true, color: i === 2 ? HEX.sky : HEX.navy }));
    s.addShape("line", { x: x + 0.35, y: 3.4, w: 0.6, h: 0, line: { color: i === 2 ? HEX.sky : HEX.teal, width: 0.75 } });
    s.addText(h.toUpperCase(), T({ x: x + 0.35, y: 3.6, w: w - 0.7, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: i === 2 ? HEX.white : HEX.blue }));
    s.addText(b, T({ x: x + 0.35, y: 4.0, w: w - 0.7, h: 1.1, fontSize: 11.5, color: i === 2 ? SOFT : HEX.black }));
  });
  L.box(s, K, MX, 5.6, CW, 1.0);
  s.addText([{ text: "For scale: ", options: { bold: true, color: HEX.teal } }, { text: "a 300-unit tower at AED 9 per unit comes to AED 2,700 a month. Where you sit in the range depends on the number of units and languages." }],
    T({ x: MX + 0.25, y: 5.6, w: CW - 0.5, h: 1.0, valign: "middle", fontSize: 11.5, color: HEX.black }));

  // Pilot offer
  s = L.content(pres, G, { subtitle: "The shadow pilot", title: "Start with a free four-week shadow pilot: nothing is sent to your buyers",
    source: "Paid terms agreed in writing before the pilot starts" });
  [["4", "weeks"], ["1", "tower"], ["0", "messages to buyers"], ["0", "AED during the pilot"]].forEach(([v, l], i) => {
    const x = MX + (i % 2) * 2.85, y = 1.75 + Math.floor(i / 2) * 2.45;
    s.addShape("rect", { x, y, w: 2.7, h: 2.3, fill: { color: i === 0 ? HEX.navy : HEX.grey }, line: { type: "none" } });
    s.addText(v, T({ x: x + 0.3, y: y + 0.2, w: 2.1, h: 1.2, valign: "bottom", fontSize: 60, bold: true, color: i === 0 ? HEX.sky : HEX.navy }));
    s.addText(l.toUpperCase(), T({ x: x + 0.3, y: y + 1.55, w: 2.2, h: 0.5, fontSize: 9, bold: true, charSpacing: 2, color: i === 0 ? HEX.white : HEX.blue }));
  });
  const rx = MX + 6.0, rw = CW - 6.0;
  L.colHead(s, K, "How it runs", rx, 1.55, rw);
  [["Week 1", "Set-up and baseline", "Payment plans, prices and buyers imported. We measure how long your team takes today."],
    ["Next milestone", "Shadow run", "Your team works as usual; Halden prepares the same cycle in parallel. We compare line by line."],
    ["Week 4", "Written comparison", "Time, accuracy, matching, escalations. You decide whether to go live, with your team approving every message."]].forEach(([when, h, b], i) => {
    const y = 2.1 + i * 1.18;
    s.addShape("rect", { x: rx, y, w: 0.06, h: 1.0, fill: { color: i === 1 ? HEX.teal : HEX.navy }, line: { type: "none" } });
    s.addText(when.toUpperCase(), T({ x: rx + 0.25, y, w: 2.2, h: 0.28, fontSize: 9, bold: true, charSpacing: 2, color: HEX.blue }));
    s.addText(h, T({ x: rx + 0.25, y: y + 0.28, w: rw - 0.25, h: 0.3, fontSize: 13, bold: true, color: HEX.navy }));
    s.addText(b, T({ x: rx + 0.25, y: y + 0.6, w: rw - 0.25, h: 0.45, fontSize: 10, color: HEX.black }));
  });
  s.addShape("rect", { x: rx, y: 5.75, w: rw, h: 0.85, fill: { color: HEX.grey }, line: { type: "none" } });
  s.addText([{ text: "What we need from you: ", options: { bold: true, color: HEX.teal } }, { text: "one finance contact, anonymised samples, 30 minutes a week." }],
    T({ x: rx + 0.25, y: 5.75, w: rw - 0.5, h: 0.85, valign: "middle", fontSize: 11, color: HEX.black }));

  // Pilot KPIs: everything measurable within a shadow run
  s = L.dark(pres, G, { subtitle: "How the pilot is judged", title: "Four numbers, measured on your own data, side by side with your finance team",
    source: "Targets set with you before the pilot. Baselines measured at your office in week 1. The demo rate (14 of 19) says nothing yet about your statements" });
  W.darkSticker(s, "PILOT TARGETS", 1.8);
  const kw = (CW - 0.6) / 4;
  const kp = [["FiClock", "Time", "team hours to prepare the milestone, against your week-1 baseline", "Vs your baseline"],
    ["FiRepeat", "Matching", "share of your transfers matched with no human, on your real statements", "Measured in the pilot"],
    ["FiAlertTriangle", "0", "amount errors and wrong automatic matches", "Non-negotiable"],
    ["FiBell", "100 %", "of buyer replies like \"I paid\" or \"my lawyer\" escalated to a person", "Non-negotiable"]];
  for (let i = 0; i < 4; i++) {
    const [ic, v, l, st] = kp[i], x = MX + i * (kw + 0.2);
    s.addShape("rect", { x, y: 1.85, w: kw, h: 4.6, fill: { color: "FFFFFF", transparency: 95 }, line: { color: HEX.sky, width: 0.5, transparency: 70 } });
    await L.iconTile(s, K, ic, x + 0.3, 2.15, 0.55, true);
    s.addText(v, T({ x: x + 0.3, y: 3.0, w: kw - 0.5, h: 1.1, valign: "bottom", fontSize: 32, bold: true, color: i >= 2 ? HEX.sky : HEX.white }));
    s.addText(l, T({ x: x + 0.3, y: 4.25, w: kw - 0.6, h: 1.2, fontSize: 11.5, color: SOFT }));
    s.addShape("line", { x: x + 0.3, y: 5.55, w: kw - 0.6, h: 0, line: { color: HEX.sky, width: 0.5, transparency: 60 } });
    s.addText(st.toUpperCase(), T({ x: x + 0.3, y: 5.7, w: kw - 0.6, h: 0.3, fontSize: 9, bold: true, charSpacing: 2, color: HEX.sky }));
  }

  // Next steps
  s = L.content(pres, G, { subtitle: "Next steps", title: "Three steps to a shadow run on your next milestone", source: "Halden · haldennn.netlify.app" });
  const sw = (CW - 0.6) / 3;
  s.addShape("line", { x: MX, y: 2.35, w: CW, h: 0, line: { color: HEX.line, width: 0.75 } });
  [["30-minute call", "With your finance or collections lead: how a milestone runs today, which tools, which banks, what went wrong last time."],
    ["Anonymised samples", "One payment request, one payment plan and one bank statement extract. Nothing identifiable."],
    ["Shadow run", "On your next certified milestone. Side-by-side comparison; nothing is sent to your buyers."]].forEach(([h, b], i) => {
    const x = MX + i * (sw + 0.3);
    s.addShape("ellipse", { x, y: 2.05, w: 0.6, h: 0.6, fill: { color: i === 2 ? HEX.teal : HEX.navy }, line: { color: HEX.white, width: 3 } });
    s.addText(String(i + 1), T({ x, y: 2.05, w: 0.6, h: 0.6, align: "center", valign: "middle", fontSize: 16, bold: true, color: HEX.white }));
    s.addText(h, T({ x, y: 3.0, w: sw - 0.2, h: 0.5, fontSize: 20, bold: true, color: HEX.navy }));
    s.addShape("line", { x, y: 3.65, w: 0.6, h: 0, line: { color: HEX.sky, width: 0.75 } });
    s.addText(b, T({ x, y: 3.85, w: sw - 0.3, h: 1.4, fontSize: 12, color: HEX.black, lineSpacingMultiple: 1.1 }));
  });
  s.addShape("rect", { x: MX, y: 5.6, w: CW, h: 0.95, fill: { color: HEX.navy }, line: { type: "none" } });
  s.addText([{ text: "Our ask today: ", options: { bold: true, color: HEX.sky } }, { text: "book the 30-minute call with the person who runs your collections.", options: { color: HEX.white } }],
    T({ x: MX + 0.3, y: 5.6, w: CW - 0.6, h: 0.95, valign: "middle", fontSize: 14 }));

  L.ending(pres, G, { title: "Every promise, carried through.", body: "Halden · haldennn.netlify.app" });

  await pres.writeFile({ fileName: out });
  await applyTheme(out, L.THEME);
  await L.morph(out);
}

build(process.argv[2] || "client.pptx").catch((e) => { console.error(e); process.exit(1); });
