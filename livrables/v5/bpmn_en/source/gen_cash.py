"""Rebuild the two collections-zoom diagrams (tobe-cash, halden-cash) of the Halden atlas.

Same corrected logic for both, as asked by the review of 24 Oct 2026:
- one follow-up subprocess per buyer (multi-instance), not one loop for 300 buyers;
- reminders drafted by the agent, validated by finance, never sent while a payment is pending;
- every match outcome handled (exact, partial, overpaid, other buyer's reference, unknown, not him);
- buyer signals (paid, lawyer, complaint, hardship) suspend all contact (interrupting event subprocess);
- day 30 ends the follow-up with an escalation; finance decides a new plan or the DLD default procedure;
- after the milestone, the escrow release file is prepared and submitted by finance.
"""
from xml.sax.saxutils import escape as _esc

def esc(s):
    return _esc(s, {'"': '&quot;'})

SIZES = {'task': (108, 70), 'event': (36, 36), 'gw': (50, 50), 'store': (50, 50)}
KIND = {
    'startEvent': 'event', 'endEvent': 'event', 'intermediateCatchEvent': 'event',
    'intermediateThrowEvent': 'event', 'boundaryEvent': 'event',
    'exclusiveGateway': 'gw', 'eventBasedGateway': 'gw', 'parallelGateway': 'gw',
    'dataStoreReference': 'store',
}
NAVY, CHAMP, SLATE, GREY = '#0B1426', '#8A6A3A', '#3A4A63', '#5B6472'


def build(v):
    """v = 'tobe' or 'halden'."""
    H = v == 'halden'
    p = 'h' if H else 't'
    W = 2380
    POOL_Y, LF, LA, LD = 120, (120, 320), (320, 790), (790, 890)
    BANK_Y = 930

    nodes, flows, msgs, assoc = [], [], [], []

    def n(i, t, name, cx, cy, parent='P', lane=None, ev=None, mi=False, label=None, attrs='', w=None, h=None):
        nodes.append(dict(id=i, t=t, name=name, cx=cx, cy=cy, parent=parent, lane=lane, ev=ev, mi=mi,
                          label=label, attrs=attrs, w=w, h=h))

    def f(a, b, pts, name='', lab=None, fid=None):
        flows.append(dict(id=fid or f'F_{a}_{b}', a=a, b=b, pts=pts, name=name, lab=lab))

    # ---------- top-level process: batch preparation ----------
    Y = 500   # agents main row
    FY = 220  # finance row
    n(f'{p}3', 'startEvent', 'Milestone certified', 110, Y, lane='A', ev='message')
    n(f'{p}4', 'businessRuleTask', 'Calculate each instalment', 224, Y, lane='A', mi=True)
    n('e1', 'boundaryEvent', 'Amount above plan or cap', 268, 465, ev='error', attrs=f' attachedToRef="{p}4"',
      lane='A', label=(280, 425, 96, 27))
    n(f'{p}5', 'userTask', 'Review the held request', 354, FY, lane='F')
    n(f'{p}6', 'serviceTask', "Draft each request in the buyer's language", 374, Y, lane='A', mi=True)
    n(f'{p}7', 'userTask', 'Approve the batch, exceptions first', 524, FY, lane='F')
    n(f'{p}9', 'sendTask', 'Send on behalf of the developer', 674, Y, lane='A', mi=True)

    # ---------- per-buyer follow-up (multi-instance subprocess) ----------
    SP = f'{p}SP'
    n(SP, 'subProcess', 'Follow up each buyer until paid or escalated', 1380, 555, lane='A', mi=True, w=1200, h=430)
    n(f'{p}20', 'startEvent', 'Request sent', 820, Y, parent=SP)
    n(f'{p}21', 'exclusiveGateway', '', 890, Y, parent=SP)
    n(f'{p}22', 'eventBasedGateway', '', 970, Y, parent=SP, label=(918, 532, 50, 14))
    n(f'{p}10', 'intermediateCatchEvent', 'Transfer seen on the escrow statement', 1050, Y, parent=SP, ev='message',
      label=(1004, 446, 100, 27))
    n(f'{p}12', 'serviceTask', 'Match: reference, payer, amount', 1154, Y, parent=SP)
    n(f'{p}13', 'exclusiveGateway', 'Match result?', 1270, Y, parent=SP, label=(1282, 455, 70, 14))
    n(f'{p}15', 'serviceTask', 'Log the payment, prepare the receipt', 1404, Y, parent=SP)
    n(f'{p}16', 'endEvent', 'Instalment paid', 1520, Y, parent=SP)
    # reminders (row above)
    RY = 400
    n(f'{p}30', 'intermediateCatchEvent', 'Day 3, day 10, no payment', 1050, RY, parent=SP, ev='timer',
      label=(990, 366, 130, 14))
    n(f'{p}31', 'exclusiveGateway', 'Payment pending or contact suspended?', 1130, RY, parent=SP,
      label=(1060, 428, 130, 27))
    n(f'{p}32', 'serviceTask', "Draft the reminder (buyer's language, or their bank)", 1244, RY, parent=SP)
    n(f'{p}33', 'userTask', 'Finance validates the reminder', 1384, RY, parent=SP)
    n(f'{p}34', 'exclusiveGateway', 'Validated?', 1500, RY, parent=SP, label=(1508, 428, 60, 14))
    n(f'{p}11', 'sendTask', 'Send the validated reminder', 1614, RY, parent=SP)
    # day 30 and doubtful matches (row below)
    CY = 600
    n(f'{p}40', 'intermediateCatchEvent', 'Day 30, still unpaid', 970, CY, parent=SP, ev='timer',
      label=(926, 623, 80, 27))
    n(f'{p}41', 'endEvent', 'Escalate to finance', 1100, CY, parent=SP, ev='escalation', label=(1062, 623, 80, 27))
    n(f'{p}14', 'userTask', 'Finance checks the match', 1364, CY, parent=SP)
    n(f'{p}14g', 'exclusiveGateway', 'Decision?', 1480, CY, parent=SP, label=(1500, 604, 60, 14))
    # buyer signals: interrupting event subprocess
    ES = f'{p}ES'
    n(ES, 'subProcess', 'Buyer signal: stop all contact', 1745, 710, parent=SP, w=410, h=90, attrs=' triggeredByEvent="true"')
    n(f'{p}50', 'startEvent', 'Paid, lawyer, complaint, hardship', 1575, 710, parent=ES, ev='message',
      label=(1530, 733, 90, 27))
    n(f'{p}51', 'serviceTask', 'Suspend every message, flag the file', 1669, 710, parent=ES)
    n(f'{p}52', 'userTask', 'Finance takes over the buyer', 1804, 710, parent=ES)
    n(f'{p}53', 'endEvent', '', 1905, 710, parent=ES)

    # ---------- day 30: human decision, DLD default procedure ----------
    n(f'{p}60', 'boundaryEvent', 'Day 30 escalation', 820, 335, ev='escalation',
      attrs=f' attachedToRef="{SP}" cancelActivity="false"', lane='A', label=(728, 290, 86, 27))
    n(f'{p}61', 'userTask', 'Decide: new plan or DLD default', 914, FY, lane='F')
    n(f'{p}62', 'exclusiveGateway', '', 1030, FY, lane='F')
    n(f'{p}63', 'endEvent', 'New plan agreed', 1098, 160, lane='F', label=(1122, 153, 90, 14))
    n(f'{p}64', 'userTask', 'Notify buyer via DLD: 30 days', 1154, FY, lane='F')
    n(f'{p}65', 'userTask', 'Decide by completion level', 1294, FY, lane='F')
    n(f'{p}66', 'endEvent', 'Default handled under DLD rules', 1400, FY, lane='F', label=(1356, 243, 90, 27))

    # ---------- after the milestone: escrow release ----------
    n(f'{p}70', 'serviceTask', 'Prepare the escrow release file', 2074, Y, lane='A')
    n(f'{p}71', 'userTask', 'Submit the release to the bank', 2214, FY, lane='F')
    n(f'{p}72', 'endEvent', 'Milestone closed', 2320, FY, lane='F')

    # ---------- stores ----------
    n('s1', 'dataStoreReference', 'Dubai country pack (approved by a lawyer)' if H else 'Country pack (table approved by a lawyer)',
      224, 840, lane='D', label=(80, 826, 116, 27))
    n('s2', 'dataStoreReference', 'Buyer memory' if H else 'Buyer file', 374, 840, lane='D', label=(406, 833, 90, 14))
    n('s3', 'dataStoreReference', 'Audit log', 2074, 840, lane='D', label=(2106, 833, 80, 14))

    # ---------- sequence flows ----------
    f(f'{p}3', f'{p}4', [(128, Y), (170, Y)])
    f('e1', f'{p}5', [(268, 447), (268, FY), (300, FY)])
    f(f'{p}4', f'{p}6', [(278, Y), (320, Y)])
    f(f'{p}5', f'{p}7', [(408, FY), (470, FY)])
    f(f'{p}6', f'{p}7', [(428, Y), (500, Y), (500, 255)])
    f(f'{p}7', f'{p}9', [(578, FY), (674, FY), (674, 465)])
    f(f'{p}9', SP, [(728, Y), (780, Y)])
    # inside the follow-up
    f(f'{p}20', f'{p}21', [(838, Y), (865, Y)])
    f(f'{p}21', f'{p}22', [(915, Y), (945, Y)])
    f(f'{p}22', f'{p}10', [(995, Y), (1032, Y)])
    f(f'{p}10', f'{p}12', [(1068, Y), (1100, Y)])
    f(f'{p}12', f'{p}13', [(1208, Y), (1245, Y)])
    f(f'{p}13', f'{p}15', [(1295, Y), (1350, Y)], 'exact', (1300, 482, 46, 14))
    f(f'{p}15', f'{p}16', [(1458, Y), (1502, Y)])
    f(f'{p}13', f'{p}14', [(1270, 525), (1270, CY), (1310, CY)], 'partial, overpaid, other ref, unknown',
      (1180, 545, 86, 40))
    f(f'{p}14', f'{p}14g', [(1418, CY), (1455, CY)])
    f(f'{p}14g', f'{p}15', [(1480, 575), (1480, 552), (1430, 552), (1430, 535)], 'confirmed', (1486, 553, 60, 14))
    f(f'{p}14g', f'{p}21', [(1480, 625), (1480, 655), (890, 655), (890, 525)], 'not this buyer', (1384, 657, 90, 14))
    f(f'{p}22', f'{p}30', [(970, 475), (970, RY), (1032, RY)])
    f(f'{p}30', f'{p}31', [(1068, RY), (1105, RY)])
    f(f'{p}31', f'{p}32', [(1155, RY), (1190, RY)], 'no', (1160, 384, 24, 14))
    f(f'{p}31', f'{p}21', [(1130, 375), (1130, 350), (890, 350), (890, 475)], 'yes: no reminder', (1000, 334, 100, 14))
    f(f'{p}32', f'{p}33', [(1298, RY), (1330, RY)])
    f(f'{p}33', f'{p}34', [(1438, RY), (1475, RY)])
    f(f'{p}34', f'{p}11', [(1525, RY), (1560, RY)], 'yes', (1530, 384, 24, 14))
    f(f'{p}34', f'{p}32', [(1500, 425), (1500, 444), (1244, 444), (1244, 435)], 'redraft', (1330, 428, 50, 14),
      fid=f'F_{p}34_{p}32r')
    f(f'{p}34', f'{p}21', [(1500, 375), (1500, 350), (890, 350), (890, 475)], 'drop', (1506, 352, 30, 14))
    f(f'{p}11', f'{p}21', [(1614, 365), (1614, 350), (890, 350), (890, 475)])
    f(f'{p}22', f'{p}40', [(970, 525), (970, 582)])
    f(f'{p}40', f'{p}41', [(988, CY), (1082, CY)])
    f(f'{p}50', f'{p}51', [(1593, 710), (1615, 710)])
    f(f'{p}51', f'{p}52', [(1723, 710), (1750, 710)])
    f(f'{p}52', f'{p}53', [(1858, 710), (1887, 710)])
    # day 30 and release
    f(f'{p}60', f'{p}61', [(820, 317), (820, FY), (860, FY)])
    f(f'{p}61', f'{p}62', [(968, FY), (1005, FY)])
    f(f'{p}62', f'{p}63', [(1030, 195), (1030, 160), (1080, 160)], 'new plan', (1036, 168, 50, 14))
    f(f'{p}62', f'{p}64', [(1055, FY), (1100, FY)], 'default', (1056, 224, 44, 14))
    f(f'{p}64', f'{p}65', [(1208, FY), (1240, FY)])
    f(f'{p}65', f'{p}66', [(1348, FY), (1382, FY)])
    f(SP, f'{p}70', [(1980, Y), (2020, Y)])
    f(f'{p}70', f'{p}71', [(2074, 465), (2074, FY), (2160, FY)])
    f(f'{p}71', f'{p}72', [(2268, FY), (2302, FY)])

    # ---------- message flows ----------
    msgs += [
        (f'M_B_ch_{p}3', 'B_ch', f'{p}3', 'Certificate', [(110, 80), (110, 482)], (116, 250, 70, 14)),
        (f'M_{p}9_B_ach', f'{p}9', 'B_ach', 'Payment requests', [(700, 465), (700, 80)], (706, 92, 90, 14)),
        (f'M_{p}11_B_ach', f'{p}11', 'B_ach', 'Validated reminders', [(1640, 365), (1640, 80)], (1646, 92, 100, 14)),
        (f'M_B_bank_{p}10', 'B_bank', f'{p}10', 'Statement (read-only)' if H else 'Statement', [(1050, BANK_Y), (1050, 518)],
         (1056, 900, 110, 14)),
        (f'M_{p}71_B_bank', f'{p}71', 'B_bank', 'Release request', [(2240, 255), (2240, BANK_Y)], (2246, 900, 90, 14)),
        ('M_B_ach_B_bank', 'B_ach', 'B_bank', 'Transfer straight to escrow' if H else 'Transfer',
         [(W, 50), (W + 30, 50), (W + 30, BANK_Y + 30), (W, BANK_Y + 30)], (W - 140, 52, 130, 14)),
    ]
    # ---------- data associations ----------
    assoc += [('in', 's1', f'{p}4', [(224, 815), (224, 535)]),
              ('in', 's2', f'{p}6', [(374, 815), (374, 535)]),
              ('out', f'{p}70', 's3', [(2074, 535), (2074, 815)])]

    # ---------- XML ----------
    by = {x['id']: x for x in nodes}
    inc, out = {}, {}
    for fl in flows:
        out.setdefault(fl['a'], []).append(fl['id'])
        inc.setdefault(fl['b'], []).append(fl['id'])

    lane_names = {
        'F': 'Finance team · Halden approval queue' if H else 'Finance team',
        'A': 'Halden agents' if H else 'AI agents',
        'D': 'Halden data layer' if H else 'Shared records',
    }
    pool_name = 'Developer, using Halden' if H else 'Developer'

    def node_xml(x):
        t, i = x['t'], x['id']
        a = f'<bpmn:{t} id="{i}"'
        if x['name'] or t not in ('exclusiveGateway', 'eventBasedGateway'):
            a += f' name="{esc(x["name"])}"'
        a += x['attrs']
        if t == 'startEvent' and x['parent'] == ES:
            a += ' isInterrupting="true"'
        if t == 'dataStoreReference':
            return a + '/>'
        body = ''.join(f'<bpmn:incoming>{k}</bpmn:incoming>' for k in inc.get(i, []))
        body += ''.join(f'<bpmn:outgoing>{k}</bpmn:outgoing>' for k in out.get(i, []))
        for kind, s, tg, _ in assoc:
            if kind == 'in' and tg == i:
                body += f'<bpmn:property id="Prop_D_{s}_{i}" name="__targetRef_placeholder"/>'
                body += (f'<bpmn:dataInputAssociation id="D_{s}_{i}"><bpmn:sourceRef>{s}</bpmn:sourceRef>'
                         f'<bpmn:targetRef>Prop_D_{s}_{i}</bpmn:targetRef></bpmn:dataInputAssociation>')
            if kind == 'out' and s == i:
                body += f'<bpmn:dataOutputAssociation id="D_{i}_{tg}"><bpmn:targetRef>{tg}</bpmn:targetRef></bpmn:dataOutputAssociation>'
        if x['ev'] == 'escalation':
            body += f'<bpmn:escalationEventDefinition id="ED_{i}" escalationRef="Esc_day30"/>'
        elif x['ev']:
            body += f'<bpmn:{x["ev"]}EventDefinition id="ED_{i}"/>'
        if t == 'subProcess':
            if x['mi']:
                body += f'<bpmn:multiInstanceLoopCharacteristics id="MI_{i}"/>'
            kids = [k for k in nodes if k['parent'] == i]
            inner = '\n'.join(node_xml(k) for k in kids)
            inner += '\n' + '\n'.join(flow_xml(fl) for fl in flows if by[fl['a']]['parent'] == i)
            return f'{a}>{body}\n{inner}\n</bpmn:{t}>'
        if x['mi']:
            body += f'<bpmn:multiInstanceLoopCharacteristics id="MI_{i}"/>'
        return f'{a}>{body}</bpmn:{t}>'

    def flow_xml(fl):
        nm = f' name="{esc(fl["name"])}"' if fl['name'] else ''
        return f'<bpmn:sequenceFlow id="{fl["id"]}"{nm} sourceRef="{fl["a"]}" targetRef="{fl["b"]}"/>'

    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0" xmlns:color="http://www.omg.org/spec/BPMN/non-normative/color/1.0" id="Defs_{v}-cash" targetNamespace="https://halden.example/bpmn" exporter="Halden" exporterVersion="1.1">',
         '<bpmn:escalation id="Esc_day30" name="Day 30, still unpaid" escalationCode="DAY30"/>',
         f'<bpmn:collaboration id="Collab_{v}-cash">',
         '<bpmn:participant id="B_ch" name="Construction site"/>',
         '<bpmn:participant id="B_ach" name="Buyers (about 300 per tower)"/>',
         f'<bpmn:participant id="P_prom" name="{esc(pool_name)}" processRef="Proc_P_prom"/>',
         '<bpmn:participant id="B_bank" name="Escrow bank"/>']
    for mid, a, b, nm, _, _ in msgs:
        X.append(f'<bpmn:messageFlow id="{mid}" name="{esc(nm)}" sourceRef="{a}" targetRef="{b}"/>')
    X.append('</bpmn:collaboration>')
    X.append('<bpmn:process id="Proc_P_prom" isExecutable="false">')
    X.append('<bpmn:laneSet id="LS_P_prom">')
    for L in 'FAD':
        refs = ''.join(f'<bpmn:flowNodeRef>{x["id"]}</bpmn:flowNodeRef>' for x in nodes
                       if x['parent'] == 'P' and x['lane'] == L)
        X.append(f'<bpmn:lane id="L_{L}" name="{esc(lane_names[L])}">{refs}</bpmn:lane>')
    X.append('</bpmn:laneSet>')
    for x in nodes:
        if x['parent'] == 'P':
            X.append(node_xml(x))
    for fl in flows:
        if by[fl['a']]['parent'] == 'P':
            X.append(flow_xml(fl))
    X.append('</bpmn:process>')

    # ---------- DI ----------
    D = [f'<bpmndi:BPMNDiagram id="Diag_{v}-cash"><bpmndi:BPMNPlane id="Plane_{v}-cash" bpmnElement="Collab_{v}-cash">']

    def shape(i, x, y, w, h, stroke, fill=None, extra='', label=None):
        s = f'<bpmndi:BPMNShape id="{i}_di" bpmnElement="{i}"{extra} bioc:stroke="{stroke}" color:border-color="{stroke}"'
        if fill:
            s += f' bioc:fill="{fill}" color:background-color="{fill}"'
        s += f'><dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}"/>'
        if label:
            lx, ly, lw, lh = label
            s += f'<bpmndi:BPMNLabel><dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}"/></bpmndi:BPMNLabel>'
        return s + '</bpmndi:BPMNShape>'

    D.append(shape('B_ch', 20, 20, 192, 60, SLATE, extra=' isHorizontal="true"'))
    D.append(shape('B_ach', 228, 20, W - 228, 60, SLATE, extra=' isHorizontal="true"'))
    D.append(shape('P_prom', 20, POOL_Y, W - 20, LD[1] - POOL_Y, NAVY, extra=' isHorizontal="true"'))
    for L, (y0, y1) in zip('FAD', (LF, LA, LD)):
        D.append(shape(f'L_{L}', 50, y0, W - 50, y1 - y0, NAVY, extra=' isHorizontal="true"'))
    D.append(shape('B_bank', 20, BANK_Y, W - 20, 60, SLATE, extra=' isHorizontal="true"'))
    # containers first, then the rest (boundary events last so they sit on top)
    order = [x for x in nodes if x['t'] == 'subProcess'] + \
            [x for x in nodes if x['t'] not in ('subProcess', 'boundaryEvent')] + \
            [x for x in nodes if x['t'] == 'boundaryEvent']
    for x in order:
        t = x['t']
        if t == 'subProcess':
            w, h = x['w'], x['h']
            D.append(shape(x['id'], x['cx'] - w // 2, x['cy'] - h // 2, w, h, CHAMP if x['id'] == SP else NAVY,
                           '#FFFFFF', ' isExpanded="true"'))
            continue
        k = KIND.get(t, 'task')
        w, h = SIZES[k]
        x0, y0 = x['cx'] - w // 2, x['cy'] - h // 2
        stroke = CHAMP if t == 'userTask' else (SLATE if k == 'store' else NAVY)
        fill = '#F4F5F7' if k == 'task' and t != 'userTask' else '#FFFFFF'
        extra = ' isMarkerVisible="true"' if t == 'exclusiveGateway' else ''
        label = x['label']
        if label is None and k in ('event', 'gw', 'store') and x['name']:
            label = (x['cx'] - 50, y0 + h + 5, 100, 27)
        D.append(shape(x['id'], x0, y0, w, h, stroke, fill, extra, label))

    def edge(i, pts, stroke, lab=None):
        s = f'<bpmndi:BPMNEdge id="{i}_di" bpmnElement="{i}" bioc:stroke="{stroke}" color:border-color="{stroke}">'
        s += ''.join(f'<di:waypoint x="{a}" y="{b}"/>' for a, b in pts)
        if lab:
            s += f'<bpmndi:BPMNLabel><dc:Bounds x="{lab[0]}" y="{lab[1]}" width="{lab[2]}" height="{lab[3]}"/></bpmndi:BPMNLabel>'
        return s + '</bpmndi:BPMNEdge>'

    for fl in flows:
        D.append(edge(fl['id'], fl['pts'], NAVY, fl['lab']))
    for kind, s, tg, pts in assoc:
        D.append(edge(f'D_{s}_{tg}', pts, SLATE))
    for mid, a, b, nm, pts, lab in msgs:
        D.append(edge(mid, pts, GREY, lab))
    D.append('</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>')
    xml = '\n'.join(X) + '\n' + '\n'.join(D) + '\n</bpmn:definitions>'

    edges = {f"{fl['a']}>{fl['b']}": fl['id'] for fl in flows}
    edges.update({f'{s}>{tg}': f'D_{s}_{tg}' for _, s, tg, _ in assoc})
    edges.update({f'{a}>{b}': mid for mid, a, b, *_ in msgs})
    return xml, edges, W + 60, BANK_Y + 60, p


if __name__ == '__main__':
    import sys
    for v in ('tobe', 'halden'):
        xml, edges, w, h, p = build(v)
        open(f'{sys.argv[1]}/{v}-cash.bpmn', 'w').write(xml)
        print(v, len(xml), len(edges), w, h)
