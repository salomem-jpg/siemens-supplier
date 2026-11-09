"""Presentation and assessment helpers for Supplier Atlas.

Score matrix is deliberately synthetic and independent of the Siemens questionnaire.
Do not use demo score averages for supplier qualification or automated approval.
"""
from __future__ import annotations

import copy
import html
import json
from pathlib import Path

import engine as E

BASE=Path(__file__).resolve().parent
BENCHMARK=3.1
SCORES_FILE=(BASE/'data'/'demo_scores.json') if (BASE/'data'/'demo_scores.json').exists() else (BASE/'demo_scores.json')
SCORES=json.loads(SCORES_FILE.read_text(encoding='utf-8'))
DOMAIN_LABELS={'A':'Future business readiness','B':'Production-system capability','C':'Resilience & continuity'}
DOMAIN_EXPLAINERS={
    'A':'Will this supplier have the people, capacity and technology to serve future requirements?',
    'B':'Can operations deliver stable quality, repeatable flow and sustained improvement?',
    'C':'How well could supply continue through dependencies, shocks and structural change?',
}
STAGE_OUTCOMES=[
    'Prioritized supplier and measurable business requirement',
    'Validated capability gap and baseline evidence',
    'Reviewed intervention shortlist with rationale',
    'Four feasibility checks and human investment decision',
    'Owners, milestone and mutual agreement',
    'Completed actions backed by implementation evidence',
    'Verified performance and sustainment',
    'Handover, lessons and follow-up cadence',
]


def new_scores():
    return copy.deepcopy(SCORES['assessments'])


def normalize_score(raw):
    """Blank/missing scores are NOT converted to zero."""
    if raw is None or raw=='':
        return None
    try:
        v=float(raw)
    except (TypeError,ValueError):
        raise ValueError('Score must be 1–5 or blank')
    if not (1<=v<=5):
        raise ValueError('Score must be between 1 and 5')
    return round(v,1)


def domain_summary(scores, prefix):
    selected=[r['code'] for r in E.CRITERIA if r['code'].startswith(prefix)]
    values=[float(scores[k]) for k in selected if scores.get(k) is not None]
    coverage=len(values)/len(selected) if selected else 0
    average=round(sum(values)/len(values),2) if values else None
    if average is None:
        signal='Unassessed'
    elif coverage<0.5:
        signal='Limited evidence'
    elif average>=BENCHMARK:
        signal='At/above reference'
    else:
        signal='Below reference'
    return {'domain':prefix,'average':average,'measured':len(values),'total':len(selected),
            'coverage':coverage,'signal':signal,'reference':BENCHMARK}


def case_profile(case, scores):
    known=[(k,v) for k,v in scores.items() if v is not None]
    lows=sorted([(k,float(v)) for k,v in known if float(v)<BENCHMARK],key=lambda x:x[1])
    highs=sorted([(k,float(v)) for k,v in known if float(v)>=BENCHMARK],key=lambda x:-x[1])
    names={r['code']:r['name'] for r in E.CRITERIA}
    missing=[r['code'] for r in E.CRITERIA if scores.get(r['code']) is None]
    return {'domains':[domain_summary(scores,c) for c in 'ABC'],
        'weaknesses':[{'code':k,'name':names[k],'score':v} for k,v in lows],
        'strengths':[{'code':k,'name':names[k],'score':v} for k,v in highs],
        'missing':missing,'coverage':round(len(known)/16,2),
        'assessment':'Synthetic scenario rubric; requires independent evidence verification'}


def compare_rows(cases, scores_by_id):
    """Structured comparison of criteria for 2–3 cases, no fabricated score fill."""
    if not 2<=len(cases)<=3:
        raise ValueError('Select two or three suppliers to compare')
    output=[]
    for crit in E.CRITERIA:
        code=crit['code']
        row={'Domain':code[0], 'Criterion':f"{code} · {crit['name']}"}
        for case in cases:
            val=scores_by_id.get(case['id'],{}).get(code)
            row[case['name']]=None if val is None else float(val)
        output.append(row)
    return output


def risk_notes(case, scores):
    profile=case_profile(case,scores)
    notes=[]
    if profile['missing']:
        notes.append(f"{len(profile['missing'])} of 16 capabilities unassessed; do not treat missing scores as poor performance.")
    for gap in profile['weaknesses'][:3]:
        notes.append(f"{gap['code']} {gap['name']}: {gap['score']:.1f}/5 in synthetic scenario (below the {BENCHMARK:.1f} reference).")
    if not case.get('evidence_verified'):
        notes.append('Human review of diagnosis and evidence remains outstanding.')
    if case.get('type')=='New':
        notes.append('New-supplier qualification evidence may be limited; a forecast is not a purchase award.')
    return notes


def short_status(case):
    f=E.calc(case)
    if f['human_go']:
        return 'Scenario GO recorded'
    if f['disposition']=='READY FOR HUMAN REVIEW':
        return 'Ready for human review'
    return 'Evidence or feasibility pending'


def snapshot_metrics(case):
    data=E.snowflake_case(case.get('id'))
    return data['record'] if data else None


def briefing_html(case, scores):
    """Standalone printable HTML decision brief, escaped user inputs."""
    p=case_profile(case,scores)
    v=E.calc(case)
    esc=lambda value:html.escape(str(value),quote=True)
    recommendations=E.recommendations(case,6)
    f=case.get('finance',{})
    gates=''.join(f'<tr><td>{esc(g["name"])}</td><td>{"Pass" if g["passed"] else "Review"}</td><td>{esc(g["reason"])}</td></tr>' for g in v['gates'])
    strengths=''.join(f'<li><b>{esc(x["code"])} · {esc(x["name"])}</b> — {x["score"]:.1f}/5</li>' for x in p['strengths'][:4]) or '<li>No evidenced strengths</li>'
    weaknesses=''.join(f'<li><b>{esc(x["code"])} · {esc(x["name"])}</b> — {x["score"]:.1f}/5</li>' for x in p['weaknesses'][:5]) or '<li>No assessed scores below reference</li>'
    picks=''.join(f'<li><b>{esc(r["name"])}</b> · {esc(r["mechanism"])} <em>({esc(r["evidence_status"])}, {esc(r["reference"])})</em></li>' for r in recommendations[:5]) or '<li>No research matches yet</li>'
    risks=''.join(f'<li>{esc(x)}</li>' for x in risk_notes(case,scores))
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Supplier brief — {esc(case['name'])}</title>
<style>body{{font:15px/1.55 system-ui,Arial;color:#253849;max-width:900px;margin:45px auto;padding:0 24px}}.eyebrow{{color:#007d86;font-weight:750;letter-spacing:.12em;font-size:11px}}h1{{font-size:36px;margin:8px 0 2px}}h2{{font-size:18px;margin-top:32px;border-bottom:1px solid #dbe5e7;padding-bottom:9px}}.sub{{color:#667984}}.hero{{background:#f1f8f8;padding:20px 24px;border-radius:15px;margin-top:24px}}.metrics{{display:flex;gap:18px;flex-wrap:wrap}}.metric{{flex:1;min-width:160px;background:#f5f8fa;border-radius:10px;padding:13px}}.metric b{{display:block;font-size:22px}}table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid #dde6e8;padding:11px}}li{{margin:8px 0}}footer{{font-size:12px;color:#72838a;margin-top:42px}}@media print{{body{{margin:0 auto}}}}</style></head>
<body><div class="eyebrow">SUPPLIER ATLAS · DECISION BRIEF</div><h1>{esc(case['name'])}</h1><p class="sub">{esc(case.get('type',''))} supplier · {esc(case.get('country',''))} · Case {esc(case.get('id',''))}</p>
<div class="hero"><b>Business requirement</b><p>{esc(case.get('trigger',''))}</p><b>Capability gap</b><p>{esc(case.get('gap',''))}</p></div>
<div class="metrics"><div class="metric">Probability scenario<b>{v['probability']:.0%}</b></div><div class="metric">Siemens expected net value<b>€{v['net']/1e6:,.2f}m</b></div><div class="metric">Supplier illustrative balance<b>€{v['supplier_balance']/1e6:,.2f}m</b></div></div>
<h2>Assessment · strengths and weaknesses</h2><p class="sub">Scenario scores, not measured supplier capabilities. Reference line: {BENCHMARK:.1f}/5. Coverage: {p['coverage']:.0%}. Missing data remain unscored.</p><table><tr><td><b>Strengths</b><ul>{strengths}</ul></td><td><b>Gaps</b><ul>{weaknesses}</ul></td></tr></table>
<h2>Research-linked intervention leads</h2><ul>{picks}</ul>
<h2>Investment decision · four gates</h2><table>{gates}</table><p><b>Current disposition:</b> {esc(short_status(case))}</p>
<h2>Open points</h2><ul>{risks}</ul>
<footer>Scenario data and reviewer decisions are fictional. The model is an undiscounted planning aid, not an authorized Siemens investment case. Probabilities are assumptions, not calibrated forecasts. Research candidates are not approved supplier interventions. Share only with approved recipients.</footer></body></html>'''
