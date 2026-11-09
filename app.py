"""Supplier Atlas — a decision-led Streamlit workbench for supplier capability building.

All cases and criterion ratings are explicitly synthetic; calculations are shared
with the optional Microsoft Copilot Studio API bridge in api/service.py.
"""
from __future__ import annotations

import copy
import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st

import engine as E
import workspace as W

st.set_page_config(
    page_title='Supplier Atlas | Capability decisions',
    page_icon='◈', layout='wide', initial_sidebar_state='expanded',
)

BASE=Path(__file__).resolve().parent
H=lambda v:html.escape(str(v),quote=True)
MONEY=lambda v:f'€{v/1_000_000:,.2f}m' if abs(v)>=100_000 else f'€{v:,.0f}'
NAMES={r['code']:r['name'] for r in E.CRITERIA}
NAV=[
    ('Overview','Overview'),
    ('Supplier assessment','Supplier assessment'),
    ('Compare suppliers','Compare suppliers'),
    ('Intervention planner','Intervention planner'),
    ('Investment case','Investment case'),
    ('Eight-stage delivery','Eight-stage delivery'),
    ('Supplier questionnaire','Supplier questionnaire'),
    ('Research library','Research library'),
    ('Data & Snowflake','Data & Snowflake'),
    ('Microsoft Copilot','Microsoft Copilot'),
    ('Briefing & export','Briefing & export'),
]

if 'cases' not in st.session_state:st.session_state.cases=E.new_cases()
if 'scores' not in st.session_state:st.session_state.scores=W.new_scores()
if 'active_case' not in st.session_state:st.session_state.active_case=next(iter(st.session_state.cases))
if 'nav' not in st.session_state:st.session_state.nav='Overview'
if 'chat' not in st.session_state:st.session_state.chat={}
if 'compare_ids' not in st.session_state:st.session_state.compare_ids=list(st.session_state.cases)[:3]

st.markdown('''<style>
/* SUPPLIER ATLAS / V4 — entirely original editorial workbench system.
   Intentionally light, warm, high contrast, no dark mode dependence. */
:root{--canvas:#F6FAFA;--white:#FFFFFF;--ink:#1E4D5B;--muted:#68838A;
 --line:#DDE9EA;--teal:#087F85;--teal-2:#0CA5A3;--teal-soft:#E5F6F4;
 --purple:#7260AE;--purple-soft:#F0ECFB;--coral:#E77B5D;--coral-soft:#FFF0EA;
 --gold:#E8A85E;--gold-soft:#FFF5E7;--green:#237F69;--green-soft:#E8F7F1;
 --r:15px;}
html,.stApp{color-scheme:light!important;background:var(--canvas)!important;color:var(--ink)!important}
.stApp [data-testid="stAppViewContainer"],.stApp [data-testid="stMain"],
.stApp [data-testid="stMainBlockContainer"],.stApp [data-testid="stBottomBlockContainer"]{
 background:var(--canvas)!important;color:var(--ink)!important}
.stApp p,.stApp label,.stApp li,.stApp span{font-family:Inter,"Segoe UI",Arial,sans-serif}
.stApp h1,.stApp h2,.stApp h3{font-family:Inter,"Segoe UI",Arial,sans-serif;
 color:var(--ink)!important;letter-spacing:-.035em}
.stApp h2{font-size:1.45rem!important}.stApp h3{font-size:1.10rem!important}
[data-testid="stHeader"]{background:var(--canvas)!important}
[data-testid="stToolbar"]{background:var(--canvas)!important}
#MainMenu,footer{visibility:hidden}
.block-container{max-width:1450px;padding-top:1.4rem;padding-bottom:4rem}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{background:#FFFFFF!important;
 border-right:1px solid var(--line)}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:1.3rem}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]{
 padding:8px 10px;border-radius:10px;transition:.12s;color:var(--ink)!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){
 background:var(--teal-soft)!important;color:var(--teal)!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{font-size:.85rem!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{color:var(--muted)!important;font-size:.73rem!important;font-weight:650}
.atlas-brand{display:flex;align-items:center;gap:12px;padding:4px 2px 20px}
.atlas-glyph{height:44px;width:44px;display:flex;align-items:center;justify-content:center;
 border-radius:13px;background:#D6F2EF;color:var(--teal);font-size:29px;font-weight:600}
.atlas-name{font-size:1.1rem;letter-spacing:-.045em;font-weight:790;color:var(--ink)}
.atlas-caption{font-size:.68rem;color:var(--muted);letter-spacing:.025em}
.sidebar-group{color:#9BAEB3;font-size:.66rem;letter-spacing:.16em;font-weight:800;
 margin:15px 0 8px}
.side-foot{background:#F3F8F8;border:1px solid var(--line);border-radius:11px;
 padding:12px 14px;color:var(--muted);line-height:1.5;font-size:.75rem;margin:18px 0}
.hero{background:linear-gradient(120deg,#E7F8F4 0%,#F7F9FF 52%,#FFF5EC 100%);
 border:1px solid #DEECEC;border-radius:20px;padding:30px 35px;margin-bottom:18px;
 position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-65px;top:-115px;width:290px;height:290px;
 border:38px solid rgba(8,127,133,.075);border-radius:50%;pointer-events:none}
.eyebrow{font-size:.67rem;text-transform:uppercase;letter-spacing:.19em;color:var(--teal);font-weight:800}
.hero h1{font-size:clamp(2.1rem,3.3vw,3.05rem)!important;margin:10px 0 11px!important;
 color:var(--ink)!important;letter-spacing:-.065em;line-height:1.05;font-weight:790}
.hero p{font-size:1rem;max-width:800px;color:#63848C;margin:0;line-height:1.55}
.hero .small-tag{display:inline-block;background:#fff;border:1px solid #CCE5E3;
 color:#2C7477;padding:6px 12px;font-weight:700;font-size:.7rem;border-radius:99px;margin-top:17px}
.page-head{margin:24px 0 17px}
.page-head h2{font-size:1.7rem!important;margin:6px 0 5px!important}
.page-head p{color:var(--muted);font-size:.89rem;margin:0;max-width:900px;line-height:1.5}
.section-kicker{font-weight:800;color:var(--purple);font-size:.67rem;
 letter-spacing:.14em;text-transform:uppercase}
.section-title{font-size:1.15rem;color:var(--ink);font-weight:790;letter-spacing:-.025em;margin:21px 0 12px}
.tile{border:1px solid var(--line);background:var(--white);border-radius:var(--r);
 padding:20px 21px;min-height:114px;margin-bottom:9px;box-shadow:0 3px 15px rgba(30,77,91,.025)}
.tile .label{font-size:.72rem;font-weight:700;color:var(--muted)}
.tile .value{font-size:1.93rem;letter-spacing:-.065em;font-weight:790;color:var(--ink);margin:10px 0 5px}
.tile .note{font-size:.73rem;line-height:1.45;color:#81969B}
.card{background:#FFFFFF;border:1px solid var(--line);border-radius:var(--r);
 padding:20px 22px;margin:8px 0 12px;min-height:110px;box-shadow:0 3px 15px rgba(30,77,91,.02)}
.card .head{font-size:.66rem;letter-spacing:.13em;color:var(--purple);font-weight:800;
 text-transform:uppercase;margin-bottom:10px}
.card h3{font-size:1.07rem!important;letter-spacing:-.02em;margin:0 0 7px!important;color:var(--ink)!important}
.card p{color:#69858C;font-size:.85rem;line-height:1.55;margin:0}
.card .foot{font-size:.73rem;color:#9BAEB3;margin-top:12px}
.fingerprint{background:#fff;border:1px solid var(--line);border-radius:12px;
 padding:11px 17px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.fingerprint strong{color:var(--ink);font-size:.86rem}.fingerprint span{font-size:.76rem;color:var(--muted)}
.chip{display:inline-flex;gap:6px;align-items:center;padding:5px 10px;border-radius:99px;
 background:var(--teal-soft);color:#16767B;font-size:.72rem;font-weight:750}
.chip.warn{background:var(--gold-soft);color:#996926}
.chip.coral{background:var(--coral-soft);color:#B45F49}
.chip.purple{background:var(--purple-soft);color:#645094}
.chip.green{background:var(--green-soft);color:#287D66}
.stage-rail{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:7px;margin:11px 0 18px}
.stage-chip{background:#FFFFFF;border:1px solid var(--line);border-radius:11px;
 padding:11px 8px;min-height:90px;text-align:left}
.stage-chip .num{font-size:.66rem;font-weight:800;color:#A2B3B5;margin-bottom:9px}
.stage-chip .name{font-size:.72rem;line-height:1.25;font-weight:740;color:var(--ink)}
.stage-chip.done{background:#EAF8F4;border-color:#C5EADF}
.stage-chip.done .num{color:var(--green)}
.stage-chip.active{background:#F0EDFA;border:1px solid #D4CCEB}
.stage-chip.active .num{color:var(--purple)}
.domain-panel{background:white;border:1px solid var(--line);border-radius:14px;
 padding:18px 20px;margin:8px 0;min-height:145px}
.domain-panel.a{border-top:4px solid #10A29E}.domain-panel.b{border-top:4px solid #7B6AB5}
.domain-panel.c{border-top:4px solid #E49B70}
.domain-panel .tag{font-size:.65rem;text-transform:uppercase;letter-spacing:.13em;
 font-weight:800;color:#90A5A9}
.domain-panel h3{font-size:.94rem!important;margin:9px 0!important}
.domain-panel .score{font-size:1.65rem;font-weight:800;color:var(--ink);letter-spacing:-.05em}
.domain-panel .msg{font-size:.76rem;color:var(--muted);margin-top:7px}
.progress-track{width:100%;height:7px;background:#ECF2F2;border-radius:9px;overflow:hidden;margin:9px 0}
.progress-fill{height:100%;background:#0B9693;border-radius:9px}
.insight{background:#fff;border:1px solid var(--line);border-radius:12px;
 padding:15px 18px;margin:7px 0;display:flex;justify-content:space-between;gap:14px;align-items:center}
.insight .name{font-size:.83rem;font-weight:720;color:var(--ink)}
.insight .desc{font-size:.72rem;color:var(--muted);margin-top:4px}
.insight .rating{font-size:1.04rem;font-weight:800;color:var(--teal);white-space:nowrap}
.insight.low .rating{color:var(--coral)}
.gate{padding:16px 16px;border:1px solid var(--line);border-radius:12px;
 min-height:125px;background:#fff;margin-bottom:9px}
.gate.ok{border-top:4px solid var(--green)}
.gate.no{border-top:4px solid var(--coral)}
.gate .num{font-size:.64rem;font-weight:780;color:var(--muted)}
.gate .name{font-size:.90rem;font-weight:770;color:var(--ink);margin-top:8px}
.gate .status{font-size:.73rem;color:var(--muted);margin-top:9px}
.data-step{border:1px solid var(--line);background:white;border-radius:13px;
 padding:17px 18px;min-height:125px;margin-bottom:9px}
.data-step .index{font-size:.67rem;font-weight:800;letter-spacing:.11em;color:var(--purple)}
.data-step h3{font-size:.9rem!important;margin:11px 0 7px!important}
.data-step p{font-size:.76rem;color:var(--muted);line-height:1.45;margin:0}
.note-box{border-left:3px solid var(--teal);background:#EAF7F5;color:#507B80;
 padding:13px 16px;margin:12px 0 18px;border-radius:0 9px 9px 0;
 line-height:1.5;font-size:.84rem}
.notice{border:1px solid #F4DEBC;background:#FFF9EE;color:#7D6440;
 padding:12px 15px;border-radius:11px;font-size:.81rem;line-height:1.5;margin:12px 0}
.stApp [data-testid="stMetric"]{background:#FFFFFF!important;border:1px solid var(--line);
 border-radius:12px;padding:14px 16px;margin-bottom:8px}
.stApp [data-testid="stMetricValue"]{color:var(--ink)!important;font-size:1.5rem!important}
.stApp [data-testid="stMetricLabel"]{color:var(--muted)!important}
.stApp .stButton>button[kind="primary"],.stApp .stFormSubmitButton button[kind="primary"]{
 background:var(--teal)!important;border-color:var(--teal)!important;color:white!important;
 border-radius:9px!important;font-weight:700}
.stApp .stButton>button[kind="primary"]:hover{background:#066B70!important}
.stApp button,.stApp [data-baseweb="select"]>div,.stApp input,.stApp textarea{
 border-radius:9px!important}
.stApp [data-testid="stDataFrame"],.stApp [data-testid="stExpander"]{
 background:#FFFFFF!important;border:1px solid var(--line);border-radius:12px}
.stApp [data-testid="stAlert"]{border-radius:12px}
.stApp [data-testid="stTabs"] button{font-weight:650}
.stApp [data-testid="stMarkdownContainer"] a{color:var(--teal)!important}
@media(max-width:1080px){.stage-rail{grid-template-columns:repeat(4,1fr)}}
@media(max-width:620px){.stage-rail{grid-template-columns:repeat(2,1fr)}
 .hero{padding:24px 20px}.hero h1{font-size:2rem!important}.block-container{padding-top:1.1rem}}
</style>''',unsafe_allow_html=True)


def card(label,title,body,footer=''):
    st.markdown(f'<div class="card"><div class="head">{H(label)}</div><h3>{H(title)}</h3><p>{H(body)}</p>'+ (f'<div class="foot">{H(footer)}</div>' if footer else '')+'</div>',unsafe_allow_html=True)


def tile(label,value,note=''):
    st.markdown(f'<div class="tile"><div class="label">{H(label)}</div><div class="value">{H(value)}</div><div class="note">{H(note)}</div></div>',unsafe_allow_html=True)


def heading(label,title,desc=''):
    st.markdown(f'<div class="page-head"><div class="section-kicker">{H(label)}</div><h2>{H(title)}</h2><p>{H(desc)}</p></div>',unsafe_allow_html=True)


def title_line(text):
    st.markdown(f'<div class="section-title">{H(text)}</div>',unsafe_allow_html=True)


def chip(text,style=''):
    return f'<span class="chip {style}">{H(text)}</span>'


def save(changes):
    if E.revise_case(case(),changes):
        st.toast('Saved. Relevant reviews were reopened when assumptions changed.')
    else:st.toast('No changes detected')


def save_diagnosis(criteria,gap,evidence,verified,approved):
    # Update supporting inputs first, then record the assessor attestation.
    # A material evidence edit invalidates all *old* attestations.
    E.revise_case(case(),{'criteria':criteria,'gap':gap,'evidence':evidence})
    E.revise_case(case(),{'evidence_verified':bool(verified),'diagnosis_approved':bool(approved) and bool(verified)})
    st.toast('Diagnosis saved. Review required for any changed downstream decisions.')


def save_shortlist(selected,reviewed):
    E.revise_case(case(),{'selected':list(selected)})
    E.revise_case(case(),{'solution_approved':bool(selected) and bool(reviewed)})
    st.toast('Shortlist recorded; subsequent stage decisions may require review.')


def case():return st.session_state.cases[st.session_state.active_case]
def score():return st.session_state.scores.get(st.session_state.active_case,{})


def gate_ui(v):
    cols=st.columns(4)
    for idx,(col,g) in enumerate(zip(cols,v['gates']),1):
        with col:
            st.markdown(f'<div class="gate {"ok" if g["passed"] else "no"}"><div class="num">GATE {idx:02d}</div><div class="name">{H(g["name"])}</div><div class="status">{H("Satisfied in scenario" if g["passed"] else "Open / not satisfied")}</div></div>',unsafe_allow_html=True)


def domain_ui(scores):
    prof=W.case_profile(case(),scores)
    cols=st.columns(3)
    for col,dom in zip(cols,prof['domains']):
        with col:
            pct=round(dom['coverage']*100)
            name=W.DOMAIN_LABELS[dom['domain']]
            val=f"{dom['average']:.2f}" if dom['average'] is not None else '—'
            st.markdown(f'<div class="domain-panel {dom["domain"].lower()}"><div class="tag">DOMAIN {dom["domain"]} · {dom["measured"]}/{dom["total"]} assessed</div><h3>{H(name)}</h3><div class="score">{val}<span style="font-size:.8rem;color:#8BA0A5"> / 5</span></div><div class="progress-track"><div class="progress-fill" style="width:{pct}%"></div></div><div class="msg">{H(dom["signal"])} · {pct}% evidence coverage</div></div>',unsafe_allow_html=True)


def insights(items,kind,limit=4):
    if not items:
        st.caption('No assessed criteria in this group.')
    for row in items[:limit]:
        st.markdown(f'<div class="insight {"low" if kind=="low" else ""}"><div><div class="name">{H(row["code"])} · {H(row["name"])}</div><div class="desc">{H("Capability improvement area" if kind=="low" else "Demonstrated in the synthetic scenario")}</div></div><span class="rating">{row["score"]:.1f} / 5</span></div>',unsafe_allow_html=True)


def reset_case():
    cid=st.session_state.active_case
    seed=next((x for x in E.CASES if x['id']==cid),None)
    if not seed:
        st.warning('Imported case has no original scenario.')
        return
    st.session_state.cases[cid]=copy.deepcopy(seed)
    st.session_state.scores[cid]=copy.deepcopy(W.SCORES['assessments'][cid])
    st.rerun()

with st.sidebar:
    st.markdown('<div class="atlas-brand"><div class="atlas-glyph">◈</div><div><div class="atlas-name">Supplier Atlas</div><div class="atlas-caption">CAPABILITY DECISION PLATFORM</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-group">ACTIVE SUPPLIER</div>',unsafe_allow_html=True)
    keys=list(st.session_state.cases)
    selected=st.selectbox('Select supplier',keys,format_func=lambda k:st.session_state.cases[k]['name'],index=keys.index(st.session_state.active_case),label_visibility='collapsed')
    if selected!=st.session_state.active_case:
        st.session_state.active_case=selected
        st.rerun()
    current=case()
    st.caption(f"{current.get('type','')} supplier · {current.get('country','')} · {current['id']}")
    st.progress(min(current.get('completed_stage',0)/8,1.0),text=f"Stage {current.get('completed_stage',0)}/8 recorded")
    st.markdown('<div class="sidebar-group">WORKSPACE</div>',unsafe_allow_html=True)
    choices=[x[0] for x in NAV]
    nav=st.radio('Workspace sections',choices,index=choices.index(st.session_state.nav) if st.session_state.nav in choices else 0,label_visibility='collapsed')
    st.session_state.nav=nav
    st.markdown('<div class="side-foot"><b>Evaluation environment</b><br>Four fictional supplier cases. Changes remain inside your browser session. Use Export to keep a copy.</div>',unsafe_allow_html=True)

c=case();s=score();v=E.calc(c);profile=W.case_profile(c,s)
# Hero remains visual but keeps case context visible on every page.
st.markdown('''<div class="hero"><div class="eyebrow">Supplier development · evidence to action</div><h1>Make the next supplier decision clear.</h1><p>Explore capability gaps, compare alternatives, test intervention economics and carry decisions through implementation—using one consistent decision engine.</p><span class="small-tag">DEMONSTRATION DATA · FOUR FICTIONAL SUPPLIERS</span></div>''',unsafe_allow_html=True)
st.markdown(f'<div class="fingerprint"><strong>{H(c["name"])}</strong>{chip(c.get("type",""))}{chip("Stage "+str(min(c.get("completed_stage",0)+1,8))+" / 8","purple")}{chip(W.short_status(c),"green" if v["human_go"] else "warn")}<span>{H(c.get("country",""))} · {H(c["id"])}</span></div>',unsafe_allow_html=True)


# ——— 01 / THE COMMAND CENTER —————————————————————————————————————————
if nav=='Overview':
    heading('Decision overview','From the capability gap to the investment decision',
            'One complete path through the eight stages. Choose a supplier on the left; every page updates to that case.')
    cols=st.columns(4)
    with cols[0]:tile('Supplier cases',str(len(st.session_state.cases)),'Two existing and two new in the seed scenarios')
    with cols[1]:tile('Assessment coverage',f"{profile['coverage']:.0%}",'Share of 16 capabilities scored in demo')
    with cols[2]:tile('Expected net value',MONEY(v['net']),'Siemens scenario · before discounting')
    with cols[3]:tile('Intervention candidates',str(len(E.recommendations(c,30))),'Matches to case criteria; review required')

    left,right=st.columns([1.3,1],gap='large')
    with left:
        title_line('The business problem')
        card('01 / BUSINESS NEED','What the supplier must deliver',c.get('objective') or 'Objective not defined',c.get('trigger',''))
        card('02 / ROOT CAPABILITY GAP','Why intervention may be needed',c.get('gap') or 'Assessment not recorded',f"Gap criteria: {', '.join(c.get('criteria',[])) or 'pending'}")
    with right:
        title_line('Decision pulse')
        card('04 / FEASIBILITY',W.short_status(c),
             'All four feasibility gates must be checked, then reviewed by a responsible manager.',
             f"{sum(g['passed'] for g in v['gates'])}/4 gates satisfied in current scenario")
        card('NEXT STEP',f"Stage {min(c.get('completed_stage',0)+1,8)} · {E.STAGES[min(c.get('completed_stage',0),7)]}",
             W.STAGE_OUTCOMES[min(c.get('completed_stage',0),7)],'The application never auto-approves a stage.')

    title_line('Capability picture')
    domain_ui(s)
    a,b=st.columns(2,gap='large')
    with a:
        title_line('Capability strengths')
        insights(profile['strengths'],'high',3)
    with b:
        title_line('Gaps to resolve')
        insights(profile['weaknesses'],'low',3)
    title_line('Engagement progress')
    rail=[]
    for i,name in enumerate(E.STAGES,1):
        state='done' if i<=c.get('completed_stage',0) else ('active' if i==min(c.get('completed_stage',0)+1,8) else '')
        rail.append(f'<div class="stage-chip {state}"><div class="num">{i:02d} / {"DONE" if state=="done" else ("NEXT" if state=="active" else "OPEN")}</div><div class="name">{H(name)}</div></div>')
    st.markdown('<div class="stage-rail">'+''.join(rail)+'</div>',unsafe_allow_html=True)
    title_line('Investment gates')
    gate_ui(v)
    st.markdown('<div class="note-box">A green benchmark score (≥3.1) is only a reference signal. The Siemens decision still depends on evidence, a relevant intervention, the four Stage 4 gates, supplier economics and human approval.</div>',unsafe_allow_html=True)


# ——— 02 / CAPABILITY ASSESSMENT —————————————————————————————————————————
elif nav=='Supplier assessment':
    heading('Assessment','Assess what the supplier can actually do',
            'Sixteen project criteria across three domains. These 1–5 ratings are synthetic illustrations; questionnaire scores are separate and not automatically converted.')
    domain_ui(s)
    tabs=st.tabs(['Strengths & weaknesses','Edit assessment matrix','Evidence & risk signals'])
    with tabs[0]:
        a,b=st.columns(2,gap='large')
        with a:
            title_line('Strongest capabilities')
            insights(profile['strengths'],'high',7)
        with b:
            title_line('Improvement priorities')
            insights(profile['weaknesses'],'low',7)
        st.caption('Scores ≥3.1 are shown as at/above the reference benchmark; scores below are improvement flags. None of these are an award decision.')
    with tabs[1]:
        st.markdown('<div class="note-box">Edit the fictional 1–5 assessment scores below to demonstrate how a new diagnosis changes comparison. A changed score reopens previous diagnosis and approval status.</div>',unsafe_allow_html=True)
        rows=[]
        for crit in E.CRITERIA:
            key=crit['code']
            rows.append({'Domain':key[0], 'Code':key,'Criterion':crit['name'],'Demo score':s.get(key),'Definition':crit['definition']})
        df=pd.DataFrame(rows)
        edited=st.data_editor(df,use_container_width=True,hide_index=True,num_rows='fixed',key=f'editor_{c["id"]}',
            disabled=['Domain','Code','Criterion','Definition'],column_config={'Demo score':st.column_config.NumberColumn('Demo score (1–5)',min_value=1,max_value=5,step=.1,format='%.1f'), 'Definition':st.column_config.TextColumn(width='large')})
        if st.button('Save assessment ratings',type='primary'):
            try:
                newvals={r['Code']:W.normalize_score(r['Demo score']) if pd.notna(r['Demo score']) else None for _,r in edited.iterrows()}
                if newvals!=s:
                    st.session_state.scores[c['id']]=newvals
                    E.revise_case(c,{'diagnosis_approved':False,'evidence_verified':False,'solution_approved':False,'finance':{'sponsor_review':'Pending'}})
                    st.success('Assessment updated. Prior assessment and investment approvals require revalidation.')
                    st.rerun()
                else:st.info('No score changes.')
            except ValueError as ex:st.error(str(ex))
        st.download_button('Download assessment CSV',pd.DataFrame(rows).to_csv(index=False),'supplier_assessment.csv','text/csv')
    with tabs[2]:
        a,b=st.columns([1.1,1],gap='large')
        with a:
            title_line('Evidence completeness')
            st.metric('Assessed criteria',f"{16-len(profile['missing'])} / 16")
            st.write('Unassessed criteria:',', '.join(profile['missing']) or 'None')
            st.markdown('**Recorded gap evidence**')
            st.write(c.get('evidence') or 'No evidence narrative recorded.')
        with b:
            title_line('Signals to investigate')
            for item in W.risk_notes(c,s):st.markdown(f'- {H(item)}')
            st.caption('Scenario signal only. Actual risks require verified, authorized supplier records.')


# ——— 03 / SIDE-BY-SIDE COMPARISON ————————————————————————————————————
elif nav=='Compare suppliers':
    heading('Comparison studio','Compare suppliers on the same evidence basis',
            'Select two or three fictional supplier scenarios. Missing scores remain blank; the 3.1 reference does not imply qualification or a GO decision.')
    pool=list(st.session_state.cases)
    ids=st.multiselect('Suppliers to compare',pool,default=[x for x in st.session_state.compare_ids if x in pool][:3],
                       format_func=lambda k:st.session_state.cases[k]['name'],max_selections=3)
    st.session_state.compare_ids=ids
    if len(ids)<2:
        st.info('Choose at least two suppliers to view the comparison.')
    else:
        chosen=[st.session_state.cases[x] for x in ids]
        cols=st.columns(len(chosen),gap='medium')
        for col,item in zip(cols,chosen):
            pr=W.case_profile(item,st.session_state.scores.get(item['id'],{}))
            gates=E.calc(item)
            with col:
                card('SUPPLIER',item['name'],item.get('gap','')[:170],f"{item.get('type','')} · {item.get('country','')}")
                a,b=st.columns(2)
                a.metric('Assessed',f"{pr['coverage']:.0%}")
                b.metric('Critical gaps',str(len(pr['weaknesses'])))
                st.caption(f"Decision: {W.short_status(item)}")
                st.caption('Strongest: '+', '.join(x['code'] for x in pr['strengths'][:3]))
                st.caption('Weakest: '+', '.join(x['code'] for x in pr['weaknesses'][:3]))
        title_line('Domain profile')
        drows=[]
        for prefix in 'ABC':
            row={'Domain':f'{prefix} · {W.DOMAIN_LABELS[prefix]}'}
            for item in chosen:
                summ=W.domain_summary(st.session_state.scores.get(item['id'],{}),prefix)
                row[item['name']]=f"{summ['average']:.2f} / 5 · {summ['measured']}/{summ['total']}" if summ['average'] is not None else 'No evidence'
            drows.append(row)
        st.dataframe(pd.DataFrame(drows),use_container_width=True,hide_index=True)
        title_line('Full 16-criterion comparison')
        rows=W.compare_rows(chosen,st.session_state.scores)
        view=pd.DataFrame(rows)
        fmt={k['name']:'{:.1f}' for k in chosen}
        def heat_cell(val):
            if not isinstance(val,(float,int)) or pd.isna(val):return 'background-color:#F1F4F5;color:#778C93'
            return 'background-color:#DFF4EC;color:#236C57;font-weight:750' if val>=W.BENCHMARK else 'background-color:#FFF0E9;color:#AD6649;font-weight:750'
        style=view.style.format(fmt,na_rep='—').map(heat_cell,subset=[r['name'] for r in chosen])
        st.dataframe(style,use_container_width=True,hide_index=True,height=680)
        st.markdown('<div class="note-box">Mint = synthetic rating ≥3.1. Peach = below 3.1. Grey = not assessed. A high average does not override a critical gap, evidence requirement or feasibility gate.</div>',unsafe_allow_html=True)
        title_line('Which case needs what kind of intervention?')
        for item in chosen:
            picks=E.recommendations(item,3)
            st.markdown(f"**{item['name']}** — "+('; '.join(f"{p['name']} ({', '.join(p['matched'])})" for p in picks) if picks else 'No case-specific matches yet'))


# ——— 04 / INTERVENTION DESIGN ———————————————————————————————————————
elif nav=='Intervention planner':
    heading('Step 3 · intervention design','Turn a capability gap into a practical solution',
            'Research-linked candidates are ranked by criterion fit, then reviewed for scope, evidence, supplier context and feasibility. They are not Siemens-approved interventions.')
    st.markdown(f'<div class="note-box"><b>Gap to solve:</b> {H(c.get("gap") or "Not recorded")}<br><b>Criteria:</b> {H(", ".join(c.get("criteria",[])) or "None selected")}</div>',unsafe_allow_html=True)
    items=E.recommendations(c,30)
    if not items:
        st.info('No matching interventions. Add relevant criteria in the eight-stage diagnosis first.')
    else:
        left,right=st.columns([1.4,.75],gap='large')
        with left:
            title_line('Recommended intervention candidates')
            for idx,item in enumerate(items[:9],1):
                st.markdown(f'<div class="card"><div class="head">MATCH {idx:02d} · {H(item["id"])} · {H(item["evidence_status"])}</div><h3>{H(item["name"])}</h3><p>{H(item["mechanism"])}</p><div class="foot">Matched criteria: {H(", ".join(item["matched"]))} · Research reference: {H(item["reference"])}</div></div>',unsafe_allow_html=True)
                with st.expander('Scope and evidence limitations',expanded=False):
                    st.write('Scope / boundary:',item.get('boundary','No boundary recorded'))
                    st.write('Screening:',item.get('evidence_status','Unknown'))
                    st.write('Approval status:',item.get('approval','Unreviewed'))
        with right:
            title_line('Shortlist and route for approval')
            options=[r['id'] for r in items]
            default=[x for x in c.get('selected',[]) if x in options]
            with st.form('intervention_shortlist'):
                selected=st.multiselect('Chosen interventions',options,default=default,
                    format_func=lambda x: next((r['name']+' · '+x for r in items if r['id']==x),x))
                reviewed=st.checkbox('I have reviewed the fit, evidence and limitations',value=c.get('solution_approved',False))
                if st.form_submit_button('Save intervention shortlist',type='primary'):
                    save_shortlist(selected,reviewed)
                    st.rerun()
            st.markdown('<div class="notice">The coordinator may suggest options, but the supplier team confirms the final shortlist. A benchmark lead is not evidence that the intervention will work for this supplier.</div>',unsafe_allow_html=True)
            title_line('Three domain specialists')
            for a in E.specialist_analysis(c):
                st.markdown(f"**{a['code']} — {a['name']}**")
                st.caption(', '.join(a['criteria']) if a['active'] else 'Not invoked for this gap')


# ——— 05 / INVESTMENT CASE ————————————————————————————————————————————
elif nav=='Investment case':
    heading('Step 4 · two-sided business case','Is this intervention feasible for both parties?',
            'Model Siemens value, supplier incentives and four decision gates. Probabilities are explicit assumptions; the numbers are not approved forecasts.')
    a,b,d,e=st.columns(4)
    with a:tile('Success probability',f"{v['probability']:.0%}",'Technical × on-time × sustained')
    with b:tile('Expected gross benefit',MONEY(v['expected_gain']),'Before Siemens support costs')
    with d:tile('Siemens expected net',MONEY(v['net']),'Expected benefit − intervention cost')
    with e:tile('Supplier balance',MONEY(v['supplier_balance']),'Supplier benefits − CapEx and OpEx')
    title_line('Four feasibility gates')
    gate_ui(v)
    with st.expander('Edit scenario economics and feasibility assumptions',expanded=True):
        with st.form('finance_form'):
            f=c.get('finance',{})
            x1,x2,x3=st.columns(3)
            gain=x1.number_input('Potential benefit (€)',min_value=0.0,value=float(f.get('gain',0)),step=100_000.0,format='%.0f')
            pt=x2.slider('Technical closure likelihood',0,100,int(float(f.get('p_technical',0))*100),1)/100
            po=x3.slider('On-time likelihood',0,100,int(float(f.get('p_on_time',0))*100),1)/100
            y1,y2,y3=st.columns(3)
            ps=y1.slider('Sustainment likelihood',0,100,int(float(f.get('p_sustain',0))*100),1)/100
            tech=y2.checkbox('Technically feasible (assessor judgement)',value=bool(f.get('tech_ok',False)))
            timing=y3.checkbox('Timeline and resources feasible',value=bool(f.get('timing_ok',False)))
            st.markdown('**Siemens intervention cost components**')
            k1,k2,k3,k4,k5=st.columns(5)
            experts=k1.number_input('Experts (€)',min_value=0.0,value=float(f.get('cost_experts',0)),step=50_000.0)
            travel=k2.number_input('Travel (€)',min_value=0.0,value=float(f.get('cost_travel',0)),step=10_000.0)
            testing=k3.number_input('Testing (€)',min_value=0.0,value=float(f.get('cost_testing',0)),step=10_000.0)
            tooling=k4.number_input('Tooling (€)',min_value=0.0,value=float(f.get('cost_tooling',0)),step=50_000.0)
            incentives=k5.number_input('Incentives (€)',min_value=0.0,value=float(f.get('cost_incentives',0)),step=50_000.0)
            st.markdown('**Supplier economics and willingness**')
            z1,z2,z3=st.columns(3)
            capex=z1.number_input('Supplier CapEx (€)',min_value=0.0,value=float(f.get('supplier_capex',0)),step=50_000.0)
            opex=z2.number_input('Supplier OpEx (€)',min_value=0.0,value=float(f.get('supplier_opex',0)),step=50_000.0)
            contribution=z3.number_input('Supplier contribution / support (€)',min_value=0.0,value=float(f.get('supplier_contribution',0)),step=50_000.0)
            z4,z5,z6=st.columns(3)
            retained=z4.number_input('Retained savings (€)',min_value=0.0,value=float(f.get('retained_savings',0)),step=50_000.0)
            relief=z5.number_input('Productivity ask relief (€)',min_value=0.0,value=float(f.get('productivity_relief',0)),step=50_000.0)
            upside=z6.number_input('Other-customer upside (€)',min_value=0.0,value=float(f.get('other_customer_upside',0)),step=50_000.0)
            willing_options=['Unknown','No','Yes with conditions','Yes']
            willingness=st.selectbox('Supplier willingness',willing_options,index=willing_options.index(f.get('supplier_willing','Unknown')) if f.get('supplier_willing') in willing_options else 0)
            mechanism=st.text_input('Supplier incentive mechanism',value=f.get('mechanism',''))
            if st.form_submit_button('Recalculate business case',type='primary'):
                save({'finance':{
                    'gain':gain,'p_technical':pt,'p_on_time':po,'p_sustain':ps,'tech_ok':tech,'timing_ok':timing,
                    'cost_experts':experts,'cost_travel':travel,'cost_testing':testing,'cost_tooling':tooling,'cost_incentives':incentives,
                    'supplier_capex':capex,'supplier_opex':opex,'supplier_contribution':contribution,
                    'retained_savings':retained,'productivity_relief':relief,'other_customer_upside':upside,
                    'supplier_willing':willingness,'mechanism':mechanism}})
                st.rerun()
    title_line('Scenario sensitivity')
    f=c.get('finance',{})
    rates=[.3,.4,.5,.6,.7,.8,.9]
    vals=[f.get('gain',0)*p-v['total_cost'] for p in rates]
    st.line_chart(pd.DataFrame({'Success probability':[f'{p:.0%}' for p in rates], 'Net value (€)':vals}).set_index('Success probability'),height=230,use_container_width=True)
    st.caption('Sensitivity varies the total success probability only. The nominal scenario probability is the product of the three entered assumptions.')
    cols=st.columns([1,1],gap='large')
    with cols[0]:
        title_line('Siemens value calculation')
        st.latex(r'\text{Expected net} = \text{Potential gain}\times(P_T P_O P_S)-\text{Siemens costs}')
        st.write(f"{MONEY(v['gross_gain'])} × {v['probability']:.1%} − {MONEY(v['total_cost'])} = **{MONEY(v['net'])}**")
    with cols[1]:
        title_line('Supplier-side value calculation')
        st.latex(r'\text{Balance} = \text{Support} + \text{Retained value} - \text{CapEx} - \text{OpEx}')
        st.write(f"Benefits {MONEY(v['supplier_value'])} − costs {MONEY(v['supplier_cost'])} = **{MONEY(v['supplier_balance'])}**")
    title_line('Open review points')
    if v['blockers']:
        for item in v['blockers']:st.markdown('- '+item)
    else:st.success('All model checks pass. A responsible manager still needs to confirm the approval.')
    decision_options=['Pending','Approved in simulated scenario','Not approved']
    with st.form('sponsor_form'):
        choice=st.selectbox('Recorded scenario decision (human review simulation)',decision_options,
            index=decision_options.index(f.get('sponsor_review','Pending')) if f.get('sponsor_review','Pending') in decision_options else 0)
        approved=st.form_submit_button('Record reviewer decision',type='primary')
        if approved:
            if choice=='Approved in simulated scenario' and v['blockers']:
                st.error('Resolve the open gates and reviews before recording a GO.')
            else:
                save({'finance':{'sponsor_review':choice}})
                st.rerun()
    st.markdown('<div class="notice">Economic figures are undiscounted, scenario-only assumptions. Supplier benefit streams may overlap. A positive model result does not award volume, approve spending or bypass procurement governance.</div>',unsafe_allow_html=True)


# ——— 06 / ALL EIGHT STAGES ———————————————————————————————————————————
elif nav=='Eight-stage delivery':
    heading('Engagement delivery','Every stage, one accountable record',
            'Navigate through stages 1–8. Inputs, approvals and evidence are recorded in the current session; the rules block skipped stages.')
    rail=[]
    for i,name in enumerate(E.STAGES,1):
        state='done' if i<=c.get('completed_stage',0) else ('active' if i==min(c.get('completed_stage',0)+1,8) else '')
        rail.append(f'<div class="stage-chip {state}"><div class="num">{i:02d}</div><div class="name">{H(name)}</div></div>')
    st.markdown('<div class="stage-rail">'+''.join(rail)+'</div>',unsafe_allow_html=True)
    n=st.selectbox('Open stage',list(range(1,9)),index=min(c.get('completed_stage',0),7),format_func=lambda i:f'{i:02d} · {E.STAGES[i-1]}')
    title_line(W.STAGE_OUTCOMES[n-1])
    if n==1:
        with st.form('stage1'):
            a,b=st.columns(2)
            name=a.text_input('Supplier name',value=c.get('name',''))
            owner=b.text_input('Siemens engagement owner',value=c.get('owner',''))
            trigger=st.text_area('Business trigger',value=c.get('trigger',''))
            objective=st.text_area('Measurable business objective',value=c.get('objective',''))
            a,b=st.columns(2)
            date=a.text_input('Need-by date (YYYY-MM-DD)',value=c.get('need_date',''))
            country=b.text_input('Country',value=c.get('country',''))
            if st.form_submit_button('Save business need',type='primary'):
                save({'name':name,'owner':owner,'trigger':trigger,'objective':objective,'need_date':date,'country':country});st.rerun()
    elif n==2:
        with st.form('stage2'):
            crit=st.multiselect('Relevant capability criteria',list(NAMES),default=c.get('criteria',[]),format_func=lambda k:f'{k} · {NAMES[k]}')
            gap=st.text_area('Capability gap',value=c.get('gap',''))
            evidence=st.text_area('Baseline and evidence trail',value=c.get('evidence',''),height=130)
            verified=st.checkbox('Assessor has checked the evidence',value=c.get('evidence_verified',False))
            approved=st.checkbox('Assessor approves this diagnosis',value=c.get('diagnosis_approved',False))
            if st.form_submit_button('Save diagnosis',type='primary'):
                save_diagnosis(crit,gap,evidence,verified,approved);st.rerun()
        if c.get('data_snapshot'):
            with st.expander('Attached synthetic data snapshot'):st.json(c['data_snapshot'])
        if st.button('Pull matching mock Snowflake record (resets diagnosis)'):
            try:E.attach_synthetic_snapshot(c);st.rerun()
            except ValueError as ex:st.error(str(ex))
    elif n==3:
        items=E.recommendations(c,30)
        eligible=[x['id'] for x in items]
        with st.form('stage3'):
            chosen=st.multiselect('Evidence-matched intervention shortlist',eligible,default=[x for x in c.get('selected',[]) if x in eligible],format_func=lambda x:next((i['name'] for i in items if i['id']==x),x))
            approved=st.checkbox('Human reviewed the solution fit and evidence boundaries',value=c.get('solution_approved',False))
            if st.form_submit_button('Save solution selection',type='primary'):
                save_shortlist(chosen,approved);st.rerun()
        st.caption('For full evidence and alternative recommendations, open Intervention planner.')
    elif n==4:
        gate_ui(E.calc(c))
        st.write('Current disposition:',W.short_status(c))
        st.caption('Change assumptions and record the scenario decision in Investment case.')
        if st.button('Open the investment case',type='primary'):
            st.session_state.nav='Investment case';st.rerun()
    elif n==5:
        data=c.get('commitments',{})
        with st.form('stage5'):
            a,b=st.columns(2)
            se=a.text_input('Siemens owner',value=data.get('siemens_owner',''))
            su=b.text_input('Supplier owner',value=data.get('supplier_owner',''))
            milestone=st.text_area('Agreed scope / first milestone',value=data.get('milestone',''))
            a,b=st.columns(2)
            sa=a.checkbox('Simulated Siemens approval',value=data.get('siemens_approved',False))
            sb=b.checkbox('Simulated supplier approval',value=data.get('supplier_approved',False))
            if st.form_submit_button('Save mutual commitments',type='primary'):
                save({'commitments':{'siemens_owner':se,'supplier_owner':su,'milestone':milestone,'siemens_approved':sa,'supplier_approved':sb}});st.rerun()
    elif n==6:
        st.caption('Record implementation tasks with completion evidence. Every action must be complete before Stage 6 can be recorded.')
        tasks=pd.DataFrame(c.get('actions',[]))
        for key in ('task','owner','due','status','evidence'):
            if key not in tasks.columns:tasks[key]=''
        tasks=tasks[['task','owner','due','status','evidence']]
        edited=st.data_editor(tasks,hide_index=True,num_rows='dynamic',use_container_width=True,key=f'tasks_{c["id"]}',
            column_config={'status':st.column_config.SelectboxColumn('Status',options=['Not started','In progress','Done'])})
        if st.button('Save implementation actions',type='primary'):
            actions=[{k:str(val).strip() for k,val in row.items()} for row in edited.fillna('').to_dict('records') if str(row.get('task','')).strip()]
            save({'actions':actions});st.rerun()
    elif n==7:
        data=c.get('verification',{})
        with st.form('stage7'):
            metric=st.text_input('Verified outcome metric',value=data.get('metric',''))
            a,b,d=st.columns(3)
            baseline=a.number_input('Baseline',value=float(data.get('baseline',0)))
            target=b.number_input('Target',value=float(data.get('target',0)))
            actual=d.number_input('Actual',value=float(data.get('actual',0)))
            evidence=st.text_area('Measured evidence',value=data.get('evidence',''))
            verifier=st.text_input('Independent reviewer',value=data.get('verifier',''))
            sustained=st.checkbox('Improvement is sustained',value=data.get('sustained',False))
            if st.form_submit_button('Save verification',type='primary'):
                save({'verification':{'metric':metric,'baseline':baseline,'target':target,'actual':actual,
                    'evidence':evidence,'verifier':verifier,'sustained':sustained}});st.rerun()
    elif n==8:
        data=c.get('closure',{})
        with st.form('stage8'):
            owner=st.text_input('Handover owner',value=data.get('owner',''))
            followup=st.text_area('Monitoring cadence and follow-up trigger',value=data.get('followup',''))
            lessons=st.text_area('Lessons to retain',value=data.get('lessons',''))
            approver=st.text_input('Human closure reviewer',value=data.get('approved_by',''))
            if st.form_submit_button('Save closure',type='primary'):
                save({'closure':{'owner':owner,'followup':followup,'lessons':lessons,'approved_by':approver}});st.rerun()
    ok,reason=E.stage_check(c,n)
    st.markdown(f'<div class="note-box"><b>{"Ready to record" if ok else "Stage gate open"}:</b> {H(reason)}</div>',unsafe_allow_html=True)
    if n==c.get('completed_stage',0)+1:
        if st.button(f'Record Stage {n} completion',type='primary',disabled=not ok):
            try:E.complete_stage_local(c,n);st.success('Stage completion recorded.');st.rerun()
            except ValueError as ex:st.error(str(ex))
    elif n<=c.get('completed_stage',0):
        st.caption('This stage was already recorded in the fictional scenario. Editing material inputs can reopen later stages.')
    else:st.info(f"Complete Stage {c.get('completed_stage',0)+1} before recording Stage {n}.")


# ——— 07 / QUESTIONNAIRE —————————————————————————————————————————————
elif nav=='Supplier questionnaire':
    heading('Source instrument','Supplier questionnaire · 55 rated questions',
            'The 55 Q7–Q61 items come from the supplied project questionnaire. The answers shown are synthetic. The mapping to the 16 project criteria is illustrative, not an approved scoring conversion.')
    questions=E.SURVEY['ratedQuestions']
    responses=c.get('survey',{})
    rated=[responses.get(f"Q{q['id']}",{}).get('rating') for q in questions]
    a,b,d=st.columns(3)
    with a:tile('Rated questions',str(sum(r is not None for r in rated))+' / 55','Unanswered questions remain unrated')
    with b:tile('Survey categories',str(len({q['section'] for q in questions})),'Different from the A/B/C capability domains')
    with d:tile('Scoring relationship','Not automatic','Survey and project criteria are distinct')
    sections=list(dict.fromkeys(q['section'] for q in questions))
    sec=st.selectbox('Questionnaire section',sections)
    sec_q=[q for q in questions if q['section']==sec]
    with st.form('survey_section'):
        answers={}
        for q in sec_q:
            key=f"Q{q['id']}";existing=responses.get(key,{})
            st.markdown(f"**Q{q['id']}** · {q['text']}")
            a,b=st.columns([1,2])
            current=existing.get('rating')
            values=['Not rated','1','2','3','4','5']
            rating=a.selectbox('Illustrative rating',values,index=values.index(str(current)) if str(current) in values else 0,key=f'question_{c["id"]}_{key}')
            evidence=b.text_input('Source / evidence note',value=existing.get('evidence',''),key=f'question_e_{c["id"]}_{key}')
            answers[key]={'rating':int(rating) if rating!='Not rated' else None,'evidence':evidence}
            st.divider()
        if st.form_submit_button('Save questionnaire section',type='primary'):
            save({'survey':answers});st.rerun()
    st.caption('A supplier self-report should be independently checked before it supports a capability score or intervention decision.')


# ——— 08 / RESEARCH LIBRARY ——————————————————————————————————————————
elif nav=='Research library':
    heading('Evidence library','Keep the benchmark behind the recommendation',
            'Explore intervention leads and the research excerpts bundled with the project. Check original sources, sector context, scope caveats and reuse permissions before external distribution.')
    a,b,d=st.columns(3)
    with a:tile('Candidate interventions',str(len(E.INTERVENTIONS)),'Research screening, not approval')
    with b:tile('Research sectors',str(len(E.RESEARCH)),'Industrials · aerospace · semiconductors · automotive')
    with d:tile('Coverage framework','A / B / C','16 capability criteria')
    tabs=st.tabs(['Intervention catalog','Search benchmark research','Evidence rules'])
    with tabs[0]:
        selected_domain=st.selectbox('Filter intervention domain',['All','A','B','C'])
        filtered=[r for r in E.INTERVENTIONS if selected_domain=='All' or selected_domain in r['domain']]
        st.dataframe(pd.DataFrame([{'Intervention':r['name'],'Domains':', '.join(r['domain']),
                                   'Criteria':r['criteria'],'Evidence screen':r['evidence_status'],'Source':r['reference'],
                                   'Limitation':r.get('boundary','')} for r in filtered]),hide_index=True,use_container_width=True,height=470)
    with tabs[1]:
        query=st.text_input('Search benchmark notes',placeholder='e.g. capacity, ramp up, supplier training, resilience')
        if query:
            results=E.search_research(query,limit=10)
            if not results:st.info('No matching excerpts found. Try a broader keyword.')
            for row in results:
                st.markdown(f'<div class="card"><div class="head">{H(row["sector"])} · {H(row["title"])}</div><h3>{H(row["section"])}</h3><p>{H(row["quote"])}</p><div class="foot">Document excerpt; verify exact context in original source.</div></div>',unsafe_allow_html=True)
        else:st.info('Search is local keyword retrieval of the bundled research extracts—not a live internet or Copilot search.')
    with tabs[2]:
        st.markdown('''- **KEEP:** scoped evidence supports investigating the mechanism for a defined use case.
- **INVESTIGATE:** plausible mechanism but evidence, scope or applicability remains unclear.
- **REJECT:** insufficient relevance or support for recommendation.

The intervention catalog contains research leads, **not** Siemens-approved supplier improvement packages. The case-specific match is a transparent criterion rule, not a causal or statistically validated prediction.''')
        st.markdown('<div class="notice">Project research excerpts and questionnaire wording may be subject to reuse restrictions. Confirm permission before committing these materials to a public repository or external hosted application.</div>',unsafe_allow_html=True)


# ——— 09 / SNOWFLAKE & PROVENANCE ———————————————————————————————————————
elif nav=='Data & Snowflake':
    heading('Data architecture','Know what every recommendation is based on',
            'A transparent explanation of the project datasets, how the mock Snowflake views join to a supplier, and what IT must do before any production connection.')
    flow=[('01','Supplier inputs','55-question instrument, assessment evidence, approval records'),
          ('02','Snowflake views','Risk, performance, evaluation and relationship management'),
          ('03','Decision engine','16 criteria, three specialists, evidence matches, four gates'),
          ('04','User interfaces','Streamlit demonstration and future Copilot Studio tools')]
    cols=st.columns(4)
    for col,(num,title,desc) in zip(cols,flow):
        with col:st.markdown(f'<div class="data-step"><div class="index">DATA FLOW · {num}</div><h3>{H(title)}</h3><p>{H(desc)}</p></div>',unsafe_allow_html=True)
    title_line('Data register')
    dataset_rows=[
        ['Supplier scenarios',f'{len(E.CASES)} fictional cases','Synthetic','Business need, gaps, stage history and economic assumptions'],
        ['Capability rubric',f'{len(E.CRITERIA)} criteria','Project methodology','A:5, B:7, C:4; not identical to questionnaire sections'],
        ['Demo assessment scores','16 scores × 4 cases, some missing','Synthetic','Side-by-side comparison; reference line 3.1, never auto-approval'],
        ['Supplier questionnaire',f"{len(E.SURVEY['ratedQuestions'])} rated questions",'Project-supplied instrument','Question wording source; responses fictional; mapping illustrative'],
        ['Intervention catalog',f'{len(E.INTERVENTIONS)} records','Project research leads','Candidate mechanisms with screen status, boundaries and references'],
        ['Benchmark research',f'{len(E.RESEARCH)} sector documents','Project-provided excerpts','Retrieval context; source usage clearance required'],
        ['Snowflake view snapshot',f"{len(E.MOCK['sources'])} views × {len(E.MOCK['suppliers'])} suppliers",'Synthetic / mock','A demonstration of the four-source join; no database connection'],
    ]
    st.dataframe(pd.DataFrame(dataset_rows,columns=['Dataset','Scale','Data status','Role in decision']),hide_index=True,use_container_width=True)
    title_line('Four Snowflake subject areas')
    descriptions={
        'SUPPLIER_RISK_MANAGEMENT':'Dependencies, continuity flags and potential disruptions. Helps prioritize resilience and investigate exposure.',
        'SUPPLIER_PERFORMANCE_MANAGEMENT':'OTD, yield, current vs required capacity and lead time. Helps establish performance baselines.',
        'SUPPLIER_EVALUATION':'Supplier assessment status, gap codes and reviewer notes. Helps validate diagnosis and identify missing evidence.',
        'SUPPLIER_RELATIONSHIP_MANAGEMENT':'Supplier owner, forecasting status, willingness and commercial context. Helps evaluate feasibility and incentives.'
    }
    cols=st.columns(2)
    for idx,name in enumerate(E.MOCK['sources']):
        with cols[idx%2]:card(f'PROPOSED READ-ONLY VIEW {idx+1:02d}',name.replace('SUPPLIER_','').replace('_',' ').title(),descriptions.get(name,''),'Joined on an approved supplier ID in a real implementation')
    title_line('Current supplier · synthetic Snowflake preview')
    record=W.snapshot_metrics(c)
    if record:
        tabs=st.tabs(['Risk','Performance','Evaluation','Relationship'])
        for tab,(k,label) in zip(tabs,[('risk','Risk'),('performance','Performance'),('evaluation','Evaluation'),('relationship_mgmt','Relationship')]):
            with tab:
                data=record.get(k,{})
                for key,val in data.items():
                    st.markdown(f"**{key.replace('_',' ').capitalize()}**: {val if val is not None else 'Not supplied'}")
        st.caption('These entries are hard-coded mock data from snowflake_mock.json, not fetched from a Siemens account.')
    else:st.info('No corresponding mock record for this imported case.')
    title_line('What a real connection requires')
    st.markdown('''1. Siemens approves four supplier-scoped **read-only Snowflake views**, with confirmed schema and data ownership.
2. IT configures identity, network access, role-based permissions, row-level supplier restrictions and audit logging.
3. The API service retrieves permitted records by supplier ID. Missing fields remain explicitly missing.
4. Evidence is presented for supplier-development review; changes to diagnosis or economics invalidate previous scenario approvals.
5. Copilot Studio invokes the approved tools. It does not receive unrestricted database access or decide supplier awards.''')
    st.markdown('<div class="notice">Live status: <b>not connected to Siemens Snowflake.</b> Mock records are synthetic. The included SQL view contract and adapter are proposals for Siemens IT review, not approved schemas.</div>',unsafe_allow_html=True)


# ——— 10 / COPILOT STUDIO —————————————————————————————————————————————
elif nav=='Microsoft Copilot':
    heading('Microsoft Copilot Studio','The same decision logic, inside Siemens tools',
            'Streamlit is the evaluation screen. For Siemens users, the intended interface is a Copilot Studio coordinator and three domain specialists calling the shared Python API.')
    title_line('Architecture and status')
    cols=st.columns(4)
    steps=[('01','Employee asks Copilot','Describe the supplier need and select an approved supplier ID.'),
           ('02','Coordinator scopes','Calls the A, B and C specialists only where the evidence warrants.'),
           ('03','API evaluates','Validated tool inputs invoke the same deterministic decision engine.'),
           ('04','Human decides','The agent returns sources, gates, blockers and next actions for approval.')]
    for col,(num,title,desc) in zip(cols,steps):
        with col:st.markdown(f'<div class="data-step"><div class="index">COPILOT FLOW · {num}</div><h3>{H(title)}</h3><p>{H(desc)}</p></div>',unsafe_allow_html=True)
    a,b=st.columns([1.1,1],gap='large')
    with a:
        title_line('Three specialist responsibilities')
        for code,label in W.DOMAIN_LABELS.items():
            card('DOMAIN '+code,label,W.DOMAIN_EXPLAINERS[code],
                 'Inputs: approved criteria, permitted supplier evidence and scoped intervention records')
    with b:
        title_line('Integration readiness')
        for label,detail in [
            ('Shared business engine','Implemented and tested locally'),
            ('Authenticated FastAPI bridge','Implemented and tested locally, not publicly hosted'),
            ('API specification and agent instructions','Included in this package'),
            ('Copilot Studio connected agent','Not connected; needs Siemens tenant'),
            ('Live Snowflake data','Not connected; needs approved views'),
            ('Enterprise identity / audit controls','Requires Siemens IT implementation')]:
            st.markdown(f'<div class="insight"><div><div class="name">{H(label)}</div><div class="desc">{H(detail)}</div></div></div>',unsafe_allow_html=True)
    with st.expander('API tool contract · example inputs and responses'):
        st.code('''POST /v1/solutions     {"case_id":"DEMO-EX-001"}
POST /v1/feasibility   {"case_id":"DEMO-EX-001"}
POST /v1/data-preview  {"case_id":"DEMO-EX-001"}
POST /v1/questions     {"case_id":"DEMO-EX-001","question":"What blocks Stage 4?"}
Header: X-API-Key: <server-managed-demo-secret>''',language='text')
        st.caption('For enterprise use, replace demo API-key authentication with Siemens-approved identity and authorization controls.')
    title_line('Ask the grounded decision assistant')
    st.caption('This embedded preview is rule-based. It is not a live Copilot or a hosted LLM. It shows grounded answers and model outputs for the selected synthetic case.')
    conversation=st.session_state.chat.setdefault(c['id'],[])
    with st.container(border=True):
        for turn in conversation[-10:]:
            with st.chat_message(turn['role']):st.markdown(turn['content'])
        q=st.chat_input('Try: Which interventions fit? What blocks Stage 4? Why would a new supplier invest?')
        if q:
            conversation.append({'role':'user','content':q})
            ans=E.bounded_copilot(c,q)
            conversation.append({'role':'assistant','content':ans['answer']})
            st.rerun()
    st.markdown('<div class="notice">This package is Copilot-connectable, but no Siemens tenant, credentials, production API, Microsoft 365 channel or Snowflake data connection has been configured.</div>',unsafe_allow_html=True)


# ——— 11 / STAKEHOLDER BRIEF + EXPORT —————————————————————————————————
elif nav=='Briefing & export':
    heading('Briefing room','Share a decision narrative—not a wall of data',
            'Produce a printable stakeholder brief from the current synthetic scenario. Export case and score records for future demonstration sessions.')
    a,b=st.columns([1.2,.8],gap='large')
    with a:
        title_line('Executive readout')
        card('BUSINESS PROBLEM',c['name'],c.get('trigger',''),c.get('objective',''))
        card('CAPABILITY CONSTRAINT','What the assessment indicates',c.get('gap',''),
             f"{len(profile['weaknesses'])} assessed criteria below the 3.1 reference · {len(profile['missing'])} missing")
        picks=E.recommendations(c,4)
        card('INTERVENTION DIRECTION','What to investigate',', '.join(x['name'] for x in picks) or 'No matching candidates','Research leads; subject to evidence and owner review')
        gate_ui(v)
        st.write('**Siemens scenario net value:**',MONEY(v['net']))
        st.write('**Supplier-side balance:**',MONEY(v['supplier_balance']))
        st.write('**Current decision:**',W.short_status(c))
    with b:
        title_line('Download and reset')
        brief=W.briefing_html(c,s)
        st.download_button('Download stakeholder brief (HTML)',brief,file_name=f'{c["id"]}_decision_brief.html',mime='text/html',type='primary',use_container_width=True)
        st.caption('Open the HTML in your browser and use Print → Save as PDF if needed.')
        st.download_button('Export current supplier case (JSON)',json.dumps(c,indent=2,ensure_ascii=False),file_name=f'{c["id"]}_case.json',mime='application/json',use_container_width=True)
        st.download_button('Export assessment ratings (JSON)',json.dumps({'case_id':c['id'],'scores':s,'data_status':'synthetic'},indent=2),file_name=f'{c["id"]}_ratings.json',mime='application/json',use_container_width=True)
        st.markdown('<div class="note-box">This workbench stores edits in your current Streamlit session only. Export the records you want to retain before closing the tab.</div>',unsafe_allow_html=True)
        uploaded=st.file_uploader('Import a previously exported case JSON',type=['json'])
        if uploaded and st.button('Import as unverified scenario'):
            try:
                raw=json.load(uploaded)
                validated=E.clean_imported_case(raw)
                st.session_state.cases[validated['id']]=validated
                st.session_state.scores.setdefault(validated['id'],{r['code']:None for r in E.CRITERIA})
                st.session_state.active_case=validated['id']
                st.success('Imported. Evidence and approvals require review.');st.rerun()
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as ex:st.error('Invalid case JSON: '+str(ex))
        if c['id'] in W.SCORES['assessments']:
            if st.button('Reset this supplier to original demo scenario',use_container_width=True):reset_case()

st.markdown('<div style="height:34px"></div><div style="border-top:1px solid #DDE9EA;padding:13px 3px;font-size:.72rem;color:#9BAAB0">SUPPLIER ATLAS · Decision support, not decision replacement &nbsp;·&nbsp; Synthetic evaluation records &nbsp;·&nbsp; Siemens production integration pending approval</div>',unsafe_allow_html=True)
