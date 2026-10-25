"""Patch Halden_Atlas_BPMN_EN.html with the corrections from the 24 Oct 2026 review."""
import json, re, sys
from gen_cash import build

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
a = s.index('<script id="views"'); a2 = s.index('>', a) + 1; b = s.index('</script>', a)
V = json.loads(s[a2:b])


def meta(v):
    H = v == 'halden'
    p = 'h' if H else 't'
    I = {
        f'{p}3': {'d': 'Nothing starts before the site engineer certifies the milestone.'},
        f'{p}4': {'d': "Each instalment is calculated from the buyer's payment plan and checked against the contract and the country rules.",
                  'g': 'Rules apply before anything is drafted.'},
        'e1': {'d': 'An amount above the plan or the cap is held before it reaches the buyer (status STOPPED).',
               'g': 'Requirement: zero wrong amounts sent.'},
        f'{p}5': {'d': 'Finance reviews the held request and decides.', 'gate': 'DECIDE'},
        f'{p}6': {'d': 'One personal request per buyer, in their language, with the right amount, due date and escrow account.'},
        f'{p}7': {'d': 'Finance approves the batch, exceptions at the top. Nothing reaches a buyer without this approval.', 'gate': 'APPROVE'},
        f'{p}9': {'d': 'Sent by email or WhatsApp, in the developer’s name, once approved.'},
        f'{p}SP': {'d': 'One follow-up per buyer, run in parallel (multi-instance). It ends when the instalment is paid, when finance takes over, or at day 30 with an escalation.'},
        f'{p}20': {'d': 'The approved request has gone out to this buyer.'},
        f'{p}21': {'d': 'Every loop comes back here: the buyer is waiting again.'},
        f'{p}22': {'d': 'Wait for whichever comes first: a transfer, a reminder date, or day 30.'},
        f'{p}10': {'d': 'A transfer appears on the escrow account statement (import first, bank connection later). Money never passes through Halden.' if H
                   else 'A transfer appears on the escrow account statement.'},
        f'{p}12': {'d': 'Matching on three keys: reference, payer and amount, plus the buyer history.'},
        f'{p}13': {'d': 'Only an exact match (reference, payer and amount) is logged without a person. Partial, overpaid, another buyer’s reference or unknown: finance checks.'},
        f'{p}14': {'d': 'Finance confirms the right buyer, or says it is not this buyer.', 'gate': 'VERIFY'},
        f'{p}14g': {'d': 'Confirmed: the payment is logged. Not this buyer: the transfer goes back to the queue and this buyer keeps waiting.'},
        f'{p}15': {'d': 'Payment logged against the instalment, receipt prepared for approval.'},
        f'{p}16': {'d': 'Instalment paid, follow-up closed for this buyer.'},
        f'{p}30': {'d': 'Day 3 and day 10 without payment. The developer sets the timing per project.'},
        f'{p}31': {'d': 'Never remind a buyer whose payment is pending or whose contact is suspended.'},
        f'{p}32': {'d': 'Reminder drafted in the buyer’s language, or for their bank if the buyer is financed.'},
        f'{p}33': {'d': 'Finance reads and validates every reminder before it goes out.', 'gate': 'APPROVE'},
        f'{p}34': {'d': 'Validated: sent. Redraft: back to the agent. Dropped: no reminder this time.'},
        f'{p}11': {'d': 'The validated reminder is sent in the developer’s name.'},
        f'{p}40': {'d': 'Day 30 and still unpaid.'},
        f'{p}41': {'d': 'The follow-up for this buyer ends with an escalation to finance.'},
        f'{p}ES': {'d': 'Interrupting event subprocess: a buyer signal stops every automatic message for this buyer.'},
        f'{p}50': {'d': 'The buyer says they have paid, mentions a lawyer, complains, or reports hardship.'},
        f'{p}51': {'d': 'All messages suspended, file flagged.'},
        f'{p}52': {'d': 'A person in finance takes the buyer over from here.', 'gate': 'DECIDE'},
        f'{p}60': {'d': 'Non-interrupting: the escalation reaches finance while the other buyers carry on.'},
        f'{p}61': {'d': 'Finance decides between a new payment plan and the DLD default procedure.', 'gate': 'DECIDE'},
        f'{p}62': {'d': 'New plan or default procedure.'},
        f'{p}63': {'d': 'New plan agreed with the buyer.'},
        f'{p}64': {'d': 'Default procedure (Law 13/2008 art. 11, amended by Law 19/2017): the developer notifies the DLD, which notifies the buyer; the buyer has 30 days to pay.', 'gate': 'DECIDE'},
        f'{p}65': {'d': 'If still unpaid: at 80% completion or more, keep the contract, auction or terminate keeping up to 40%; from 60% to 80%, terminate keeping up to 40%; below 60%, terminate keeping up to 25%. To confirm with a lawyer.', 'gate': 'DECIDE'},
        f'{p}66': {'d': 'Default handled under the DLD rules.'},
        f'{p}70': {'d': 'Escrow release file prepared: milestone certificate, amounts collected, evidence (Dubai Law No. 8 of 2007).'},
        f'{p}71': {'d': 'Finance submits the release request to the escrow bank.', 'gate': 'SIGN'},
        f'{p}72': {'d': 'Milestone closed.'},
        's1': {'d': 'Caps, plans and reminder timing in a table a lawyer can read and correct, not in code.'},
        's2': {'d': 'One file per buyer: plan, messages, payments, signals.'},
        's3': {'d': 'Every draft, approval, match and message logged: who, what, when, why.'},
    }
    if H:
        I[f'{p}9']['shadow'] = 'In the shadow pilot nothing is sent. Halden compares its batch, line by line, with the one the team prepared by hand.'
        I[f'{p}11']['shadow'] = 'In the shadow pilot: reminder drafted and validated, not sent.'
        I[f'{p}12']['g'] = 'In our demo (fictional data): 14 of 19 transfers matched with no human, 4 confirmed by finance, 1 rightly refused.'
        I['s1']['d'] = 'Dubai pack, in preparation: one escrow account per project, every off-plan sale registered (Oqood). To confirm with a lawyer.'
        lst = [(f'{p}7', 'Nothing goes out without approval'), (f'{p}33', 'Every reminder validated'),
               (f'{p}10', 'Money never passes through Halden'), (f'{p}12', '14 of 19 matched in our demo (fictional)'),
               (f'{p}50', 'A buyer signal stops all contact'), (f'{p}64', 'Day 30: DLD default procedure')]
        plain = [{'h': 'How it works', 't': 'Halden drafts, finance approves every message in the queue, the buyer pays straight into escrow.'},
                 {'h': 'The guardrail', 't': 'No message without approval, no reminder while a payment is pending, any buyer signal goes to a person.'},
                 {'h': 'Key point', 't': 'In the shadow pilot nothing is sent: we compare with the team’s own work.'}]
        return dict(kicker='HALDEN SOLUTION · ONE COLLECTIONS MILESTONE, IN PRACTICE',
                    source='Source: Halden POC and partner brief, October 2026. 14 of 19 from the Halden demo (fictional tower of 32 buyers). DLD rules to confirm with a lawyer. Product in development.',
                    list_title='Why a developer can say yes', info=I,
                    list=[{'id': i, 'label': l} for i, l in lst], plain=plain)
    lst = [('s1', 'Rules a lawyer can read'), ('e1', 'Error stopped before the buyer'), (f'{p}SP', 'One follow-up per buyer'),
           (f'{p}33', 'Every reminder validated'), (f'{p}13', 'Only exact matches are automatic'), (f'{p}70', 'Escrow release at the end')]
    plain = [{'h': 'The principle', 't': 'Country rules apply before anything is drafted; an error is stopped before it reaches the buyer.'},
             {'h': 'What the team keeps', 't': 'Batch approval, every reminder, doubtful matches, buyer signals, decisions at day 30, the escrow release.'},
             {'h': 'Key point', 't': 'Each buyer is followed on their own, with a clear end: paid, taken over by a person, or escalated.'}]
    return dict(kicker='TARGET PROCESS (TO-BE) · WHAT A COLLECTIONS MILESTONE SHOULD LOOK LIKE, WHATEVER THE TOOL',
                source='Source: Halden partner brief, October 2026; Dubai Law 13/2008 (amended by Law 19/2017) and Law No. 8 of 2007. Target process, tool-independent.',
                list_title='What changes', info=I, list=[{'id': i, 'label': l} for i, l in lst], plain=plain)


for v in ('tobe', 'halden'):
    xml, edges, w, h, p = build(v)
    sim = [f'{p}{k}' for k in ['3', '4', '6', '7', '9', '20', '21', '22', '10', '12', '13', '15', '16',
                               '30', '31', '32', '33', '34', '11', '40', '41', '60', '61', '62', '64', '65', '66', '70', '71', '72']]
    V[f'{v}-cash'] = dict(xml=xml, meta=meta(v), sim=sim, edges=edges, w=w, h=h)

# ---------- asis-cash: close the dangling end ----------
x = V['asis-cash']['xml']
x = x.replace('<bpmn:incoming>F_r2_a13</bpmn:incoming></bpmn:manualTask>',
              '<bpmn:incoming>F_r2_a13</bpmn:incoming><bpmn:outgoing>F_a13_a14</bpmn:outgoing></bpmn:manualTask>', 1)
assert 'F_a13_a14' in x, 'a13 pattern'
x = re.sub(r'(<bpmn:endEvent id="a14" name="[^"]*")\s*/>', r'\1><bpmn:incoming>F_a13_a14</bpmn:incoming></bpmn:endEvent>', x)
x = re.sub(r'(<bpmn:endEvent id="a14" name="[^"]*")>(?!<bpmn:incoming>)', r'\1><bpmn:incoming>F_a13_a14</bpmn:incoming>', x)
x = x.replace('<bpmn:sequenceFlow id="F_r2_a13"', '<bpmn:sequenceFlow id="F_a13_a14" sourceRef="a13" targetRef="a14"/>\n<bpmn:sequenceFlow id="F_r2_a13"', 1)
x = x.replace('</bpmndi:BPMNPlane>', '<bpmndi:BPMNEdge id="F_a13_a14_di" bpmnElement="F_a13_a14" bioc:stroke="#0B1426" color:border-color="#0B1426"><di:waypoint x="1604" y="190"/><di:waypoint x="1672" y="190"/></bpmndi:BPMNEdge>\n</bpmndi:BPMNPlane>', 1)
V['asis-cash']['xml'] = x
V['asis-cash']['edges']['a13>a14'] = 'F_a13_a14'
if 'a14' not in V['asis-cash']['sim']:
    V['asis-cash']['sim'].append('a14')

# As-Is = our hypothesis
for k in ('asis-full', 'asis-cash'):
    m = V[k]['meta']
    if 'HYPOTHESIS' not in m['kicker']:
        m['kicker'] += ' · OUR HYPOTHESIS, TO CHECK IN INTERVIEWS'
    m['source'] = m['source'].rstrip('.') + '. As-Is drawn from our interviews and desk research: a hypothesis to validate with developers.'

# ---------- tobe-full: warranty as event subprocess, Dubai vocabulary ----------
x = V['tobe-full']['xml']
x = x.replace('name="Notary or land registry"', 'name="Land registry (DLD, Oqood)"')
x = x.replace('name="Legal review, signing at the notary or registry"', 'name="Legal review, signing, Oqood registration with the DLD"')
x = x.replace('name="Collections agent: one cycle per milestone (see zoom)"', 'name="Collections agent: each milestone, up to escrow release (zoom)"')
assert "Oqood registration" in x and "escrow release (zoom)" in x
# H4 now ends the handover; claims arrive any time in years 1–10
x = x.replace('<bpmn:outgoing>F_H4_A9</bpmn:outgoing></bpmn:userTask>', '<bpmn:outgoing>F_H4_E4</bpmn:outgoing></bpmn:userTask>\n<bpmn:endEvent id="E4" name="Handover signed"><bpmn:incoming>F_H4_E4</bpmn:incoming></bpmn:endEvent>', 1)
blk_start = x.index('<bpmn:intermediateCatchEvent id="A9"')
blk_end = x.index('</bpmn:endEvent>', x.index('<bpmn:endEvent id="A12"')) + len('</bpmn:endEvent>')
blk = x[blk_start:blk_end]
blk0 = blk
blk = blk.replace('<bpmn:intermediateCatchEvent id="A9" name="Claim reported (years 1–10)"><bpmn:incoming>F_H4_A9</bpmn:incoming>',
                  '<bpmn:startEvent id="A9" name="Claim reported (years 1–10)" isInterrupting="false">')
blk = blk.replace('</bpmn:intermediateCatchEvent>', '</bpmn:startEvent>', 1)
inner_flows = []
for fid in ['F_A9_A10', 'F_A10_g3', 'F_g3_A11', 'F_g3_H5', 'F_H5_A11', 'F_A11_A12']:
    mm = re.search(rf'<bpmn:sequenceFlow id="{fid}"[^>]*/>\n?', x)
    inner_flows.append(mm.group(0).strip()); x = x.replace(mm.group(0), '', 1)
x = x.replace(blk0, '', 1)
x = re.sub(r'<bpmn:sequenceFlow id="F_H4_A9"[^>]*/>', '<bpmn:sequenceFlow id="F_H4_E4" sourceRef="H4" targetRef="E4"/>', x)
esp = ('<bpmn:subProcess id="WSP" name="Warranty claims, years 1–10" triggeredByEvent="true">\n' + blk + '\n' + '\n'.join(inner_flows) + '\n</bpmn:subProcess>\n')
x = x.replace('</bpmn:process>', esp + '</bpmn:process>', 1)
# lanes: elements inside the subprocess leave the lane refs
for i in ['A9', 'A10', 'g3', 'H5', 'A11', 'A12']:
    x = x.replace(f'<bpmn:flowNodeRef>{i}</bpmn:flowNodeRef>', '')
x = x.replace('<bpmn:flowNodeRef>H4</bpmn:flowNodeRef>', '<bpmn:flowNodeRef>H4</bpmn:flowNodeRef><bpmn:flowNodeRef>E4</bpmn:flowNodeRef><bpmn:flowNodeRef>WSP</bpmn:flowNodeRef>', 1)
x = re.sub(r'<bpmndi:BPMNEdge id="F_H4_A9_di".*?</bpmndi:BPMNEdge>',
           '<bpmndi:BPMNEdge id="F_H4_E4_di" bpmnElement="F_H4_E4" bioc:stroke="#0B1426" color:border-color="#0B1426"><di:waypoint x="1970" y="345"/><di:waypoint x="1970" y="318"/></bpmndi:BPMNEdge>', x, flags=re.S)
shapes = ('<bpmndi:BPMNShape id="WSP_di" bpmnElement="WSP" isExpanded="true" bioc:stroke="#0B1426" color:border-color="#0B1426" bioc:fill="#FFFFFF" color:background-color="#FFFFFF"><dc:Bounds x="2056" y="196" width="668" height="236"/></bpmndi:BPMNShape>\n'
          '<bpmndi:BPMNShape id="E4_di" bpmnElement="E4" bioc:stroke="#0B1426" color:border-color="#0B1426" bioc:fill="#FFFFFF" color:background-color="#FFFFFF"><dc:Bounds x="1952" y="282" width="36" height="36"/><bpmndi:BPMNLabel><dc:Bounds x="1880" y="262" width="70" height="27"/></bpmndi:BPMNLabel></bpmndi:BPMNShape>\n')
first_shape = x.index('<bpmndi:BPMNShape id="A9_di"')
x = x[:first_shape] + shapes + x[first_shape:]
assert x.count('id="A9"') == 1
V['tobe-full']['xml'] = x
mi = V['tobe-full']['meta']['info']
mi['A9'] = {'d': 'Non-interrupting event subprocess: an owner can report a claim at any time during the warranty years, without stopping anything else.'}
mi['WSP'] = {'d': 'Warranty claims arrive at any time in years 1–10: each one opens its own case.'}
mi['E4'] = {'d': 'Handover report signed.'}
mi['A5'] = {'d': 'The collections agent runs each milestone: calculation, requests, matching, reminders validated by finance, day-30 escalation and DLD default procedure, then the escrow release file. See the zoom.',
            'g': 'Measure: time to collect a milestone, against today’s baseline.'}
mi['H2']['d'] = mi['H2']['d'].replace('notary or registry', 'DLD (Oqood registration)').replace('notary', 'DLD') if 'H2' in mi else ''
ed = V['tobe-full']['edges']
ed.pop('H4>A9', None); ed['H4>E4'] = 'F_H4_E4'
V['tobe-full']['sim'] = [i for i in V['tobe-full']['sim'] if i not in ('A9',)]
V['tobe-full']['sim'][V['tobe-full']['sim'].index('H4') + 1:V['tobe-full']['sim'].index('H4') + 1] = ['E4', 'A9']
V['tobe-full']['meta']['kicker'] = 'TARGET PROCESS (TO-BE) · WHAT THE SECTOR SHOULD AIM FOR, WHATEVER THE TOOL'

# generic text pass inside meta strings
txt = json.dumps(V, ensure_ascii=False)
for old, new in [('notary (France, Spain) or registering the sale (Oqood in Dubai)', 'registering the sale with the DLD (Oqood in Dubai)'),
                 ('notary or registry file', 'DLD registration file (Oqood)'),
                 ('notary or registry. The AI never signs', 'DLD (Oqood). The AI never signs'),
                 ('notary or registry', 'DLD (Oqood)'),
                 ('notary or register the sale', 'register the sale with the DLD (Oqood)'),
                 ('85%', '14 of 19 (demo)')]:
    txt = txt.replace(old, new)
V = json.loads(txt)
s = s[:a2] + json.dumps(V, ensure_ascii=False).replace('</', '<\\/') + s[b:]

# ---------- page text ----------
R = [
    ('2 · To-Be · the market', '2 · Target process'),
    ('2 · What the market should aim for (To-Be)', '2 · Target process (To-Be, any tool)'),
    ('data-l="2 · What the market should aim for"', 'data-l="2 · Target process"'),
    ('1 · As-Is · today', '1 · As-Is · our hypothesis'),
    ("'tobe-full': s => `The market should aim for a cycle", "'tobe-full': s => `The target process is a cycle"),
    ("['85%','transfers matched without intervention','ILLUSTRATIVE'],['< 1 day','to prepare a full cycle','TO TEST']",
     "['14 / 19','transfers matched with no human, in our demo','DEMO · FICTIONAL'],['0','buyer message sent without approval','PILOT RULE']"),
    ("['Time to prepare a milestone','By hand vs Halden; target under one day (to test).','PILOT',null]",
     "['Time to prepare a milestone','By hand vs Halden, measured against the team’s own baseline.','PILOT',null]"),
    ("['Transfers matched without help','85% in the demo (illustrative).','PILOT',['halden-cash','h12']]",
     "['Transfers matched without help','14 of 19 in our demo (fictional data); 0 wrong automatic matches on a 200-line bench.','PILOT',['halden-cash','h12']]"),
    ("['Share collected within 15 days','Measured in the live phase.','NEXT',null]",
     "['Buyer signals escalated','100% of signals (paid, lawyer, complaint, hardship) handed to a person.','PILOT',['halden-cash','h50']]"),
    ("['Slack','Where all work starts: tasks handed to agents in a thread.','PILOT',null]",
     "['Shared workspace','Tasks handed to agents; no client data outside the approved hosting.','PILOT',null]"),
    ("['Registries and notaries','DLD and Oqood in Dubai, notaries in France and Spain.','VISION',['tobe-full','H2']]",
     "['Land registry','DLD and Oqood registration in Dubai.','VISION',['tobe-full','H2']]"),
    ("A well-known partner (bank, notary, broker)", "A well-known partner (bank, broker, law firm)"),
    ("matches transfers and sends reminders on day 3 and day 10.", "matches transfers and drafts reminders on day 3 and day 10, each one validated by finance before it goes out."),
    ("(share of the milestone collected within 15 days)", "(time to collect a milestone, against today’s baseline)"),
    ("Approve each batch, confirm doubtful matches, decide for a buyer in difficulty.", "Approve each batch, validate every reminder, confirm doubtful matches, decide at day 30 (new plan or DLD default), submit the escrow release."),
    ("notary or registry file.", "DLD registration file (Oqood)."),
    ("Legal review and signing, with the notary or registry. The AI never signs.", "Legal review, signing and Oqood registration with the DLD. The AI never signs."),
]
for old, new in R:
    if old not in s:
        print('MISSING', old[:70])
    s = s.replace(old, new)
for leftover in ['Slack', 'notary', '85%', '< 1 day', 'the market']:
    hits = [m.start() for m in re.finditer(re.escape(leftover), s)]
    hits = [h for h in hits if not (leftover == '85%' and 'hsl(' in s[h - 20:h])]
    if hits:
        print('LEFT', leftover, len(hits), [s[h - 60:h + 40].replace('\n', ' ') for h in hits[:3]])
open(dst, 'w', encoding='utf-8').write(s)
print('written', len(s))
