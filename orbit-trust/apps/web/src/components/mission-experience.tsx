'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {agentBranches,buildWorkflow,evaluateScenario,scenarioInputs,type BranchId,type ScenarioId} from '../lib/mission-workflow';
import {activityItems,reviewCases,evidenceChecks} from '../lib/demo-data';
import type {DemoSatellite} from '../lib/orbital-demo';

const usd=(v:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);

export function MissionExperience({onOrbit,paused,onPause,satellites,onSelect}:{onOrbit:()=>void;paused:boolean;onPause:()=>void;satellites:DemoSatellite[];onSelect:(sat:DemoSatellite)=>void}) {
  const [scenario,setScenario]=useState<ScenarioId>('review');
  const result=useMemo(()=>evaluateScenario(scenario),[scenario]);
  const events=useMemo(()=>buildWorkflow(scenario),[scenario]);
  const [cursor,setCursor]=useState(-1),[playing,setPlaying]=useState(false),[branch,setBranch]=useState<BranchId>('collision');
  const [traceEvent,setTraceEvent]=useState<string|null>(null),[activityOpen,setActivityOpen]=useState(false),[activityFilter,setActivityFilter]=useState('all');
  const [alert,setAlert]=useState(false),[acknowledged,setAcknowledged]=useState(false),[caseIndex,setCaseIndex]=useState(0);
  const [query,setQuery]=useState(''),[onlyFlagged,setOnlyFlagged]=useState(false),[reduced,setReduced]=useState(false);
  const [lossDays,setLossDays]=useState(14);
  const wrapper=useRef<HTMLDivElement>(null),activity=useRef<HTMLElement>(null);
  const branchData=agentBranches.find(b=>b.id===branch)!;
  const currentCase=reviewCases[caseIndex];
  const filtered=satellites.filter(s=>(!onlyFlagged||s.review)&&`${s.name} ${s.mission} ${s.operator}`.toLowerCase().includes(query.toLowerCase()));
  const runEvents=events.slice(0,cursor+1);
  const ledger=runEvents.map(e=>({id:e.id,time:`T+${String(e.index).padStart(2,'0')}`,title:e.title,detail:e.detail,kind:e.state==='attention'?'alert':'calc'}));
  const historical=activityItems.map((e,i)=>({...e,id:`fixture-${i}`}));
  const timeline=[...ledger.toReversed(),...historical].filter(e=>activityFilter==='all'||e.kind===activityFilter);
  const eventDetail=timeline.find(e=>e.id===traceEvent);

  useEffect(()=>{
    const mq=matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setReduced(mq.matches);update();mq.addEventListener('change',update);return()=>mq.removeEventListener('change',update);
  },[]);
  useEffect(()=>{
    if(!wrapper.current)return;
    const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in-view');observer.unobserve(e.target);}}),{threshold:.08});
    wrapper.current.querySelectorAll('.ot-reveal').forEach(e=>observer.observe(e));return()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    if(!playing||paused)return;
    const timer=setInterval(()=>{
      if(document.hidden)return;
      setCursor(c=>{const n=Math.min(c+1,events.length-1);if(n===events.length-1)setPlaying(false);return n;});
    },reduced?250:1000);
    return()=>clearInterval(timer);
  },[playing,paused,events.length,reduced]);
  useEffect(()=>{
    if(cursor>=2&&result.review){setAlert(true);setAcknowledged(false);}
  },[cursor>=2,result.review]);
  function run(){setCursor(-1);setPlaying(true);setAlert(false);setAcknowledged(false);}
  function chooseScenario(value:ScenarioId){setScenario(value);setCursor(-1);setPlaying(false);setAlert(false);setAcknowledged(false);setLossDays(scenarioInputs[value].downtime);}
  function openActivity(){setActivityOpen(true);setTimeout(()=>activity.current?.scrollIntoView({behavior:reduced?'instant':'smooth',block:'start'}),30);}
  function exportTrace(){const blob=new Blob([JSON.stringify({schema:'orbit-trust.demo-trace.v1',scenario,mode:'local deterministic demonstration',inputs:result.input,findings:result.findings,events:runEvents},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`orbit-trust-${scenario}-trace.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

  return <div ref={wrapper} className={`ot-mission-experience ${paused||reduced?'motion-paused':''}`}>
    <nav className="ot-chapter-nav" aria-label="Explore mission chapters"><a href="#mission">01 / Mission</a><a href="#agent-architecture">02 / Intelligence</a><button onClick={openActivity}>03 / Activity <span>{timeline.length}</span></button><a href="#satellite-directory">04 / Satellites</a><button onClick={onPause} aria-pressed={paused}>{paused?'Resume motion':'Pause motion'}</button></nav>

    <section id="mission" className="ot-mission ot-reveal" aria-labelledby="mission-title">
      <div className="ot-section-heading"><p className="ot-eyebrow">01 / MISSION OVERVIEW</p><span className="ot-mode">● SYNTHETIC OPERATIONS</span></div>
      <div className="ot-mission-heading"><h2 id="mission-title">The whole picture.<br/><span>Before the next move.</span></h2><p>Watch the evidence.<br/>Understand the uncertainty.<br/>Keep the decision human.</p></div>
      <div className="ot-mission-grid">
        <div className="ot-mission-instrument"><div className="ot-instrument-label"><span>ENCOUNTER WINDOW</span><span>DEMONSTRATION</span></div>
          <div className="ot-reticle" aria-hidden="true"><div className="ot-reticle-sweep"/><i/><i/><i/><span className="ot-reticle-cross"/><b/><em/></div>
          <div className="ot-instrument-readout"><span>NEAREST APPROACH</span><strong>{(result.distanceKm*1000).toLocaleString()}<small>m</small></strong><p>Linear model · T+{result.seconds.toFixed(0)}s</p></div>
          <div className="ot-instrument-footer"><span>{result.review?'REVIEW THRESHOLD CROSSED':'ABOVE DEMO THRESHOLD'}</span><button onClick={onOrbit}>Enter orbital view ↗</button></div>
        </div>
        <div className="ot-mission-board"><div className="ot-metrics"><div><span>Demo spacecraft</span><strong>{String(satellites.length).padStart(2,'0')}</strong></div><div><span>Priority reviews</span><strong className="ot-red">{String(reviewCases.filter(c=>c.urgency==='P0'||c.urgency==='P1').length).padStart(2,'0')}</strong></div><div><span>Evidence checks passed</span><strong>{evidenceChecks.filter(c=>c.state==='pass').length}<small> / {evidenceChecks.length}</small></strong></div></div>
          <div className="ot-case-heading"><h3>Attention, in order.</h3><a href="/queue/">All cases ↗</a></div>
          <div className="ot-case-list">{reviewCases.slice(0,3).map((c,i)=><button key={c.id} className={caseIndex===i?'selected':''} onClick={()=>setCaseIndex(i)} aria-pressed={caseIndex===i}><span className="ot-priority">{c.urgency}</span><span><strong>{c.primary}</strong><small>{c.secondary}</small></span><span>{c.evidence}<b>↗</b></span></button>)}</div>
          <div className="ot-case-detail" aria-live="polite"><span>{currentCase.id} / SNAPSHOT</span><p>{currentCase.reason}.</p><div><span>Supplied P<sub>c</sub> <strong>{currentCase.pc}</strong></span><a href={caseIndex===0?'/case/':'/queue/'}>{caseIndex===0?'Inspect evidence':'Open review queue'} ↗</a></div></div>
        </div>
      </div>
      <p className="ot-disclaimer">A synthetic review snapshot. The near-approach instrument uses a separate local fixture; these are not current orbital warnings.</p>
    </section>

    <section id="agent-architecture" className="ot-architecture ot-reveal" aria-labelledby="architecture-title">
      <div className="ot-section-heading"><p className="ot-eyebrow">02 / AGENT ARCHITECTURE</p><span className="ot-mode">INSPECT EVERY LAYER</span></div>
      <div className="ot-architecture-title"><h2 id="architecture-title">Intelligence,<br/><span>with nothing to hide.</span></h2><div><p>One orchestrator. Five specialist branches.<br/>Every finding carries its evidence.</p><span>Local calculation + trace playback · no live LLM calls</span></div></div>
      <div className="ot-run-controls"><label>Scenario<select value={scenario} onChange={e=>chooseScenario(e.target.value as ScenarioId)}><option value="review">Close approach / incomplete evidence</option><option value="monitor">Wider separation / recent epoch</option></select></label><button className="ot-action" onClick={run} disabled={playing}>{cursor<0?'Run demonstration':'Replay demonstration'} <span>↗</span></button><button className="ot-text-button" disabled={cursor<0} onClick={exportTrace}>Export trace ↓</button></div>
      {paused&&playing&&<p className="ot-run-notice">Playback is paused with site motion. Resume motion to continue.</p>}
      <div className={`ot-network ${playing?'is-running':''}`}>
        <div className="ot-network-input"><span>SCENARIO INPUT</span><code>position · velocity · epoch · cost assumptions</code><span>↓</span></div>
        <div className={`ot-router ${cursor>=0?'is-active':''}`}><span className="ot-router-symbol" aria-hidden="true">⌘</span><div><small>ROOT / ORCHESTRATOR</small><h3>Route. Evaluate. Reconcile.</h3></div><span className="ot-run-state">{playing?'PROCESSING':cursor===5?'AWAITING ANALYST':cursor<0?'READY':'PAUSED'}</span></div>
        <div className="ot-network-bus" aria-hidden="true"/>
        <div className="ot-branches">{agentBranches.map((b,i)=>{
          const event=events[i+1],done=cursor>=i+1,active=playing&&cursor===i;
          return <button key={b.id} className={`ot-branch ${branch===b.id?'selected':''} ${active?'processing':''} ${done?'done':''}`} onClick={()=>setBranch(b.id)} aria-expanded={branch===b.id} aria-controls="ot-specialist-panel"><div><span>{b.code}</span><i className={done&&event.state!=='complete'?'attention':''}/></div><strong>{b.name}</strong><span>{b.specialists.length} specialist nodes</span><footer>{done?event.state:active?'evaluating':'inspect branch'}<b>{branch===b.id?'−':'+'}</b></footer></button>;
        })}</div>
        <div className="ot-network-exit"><span>↳</span> EVIDENCE PACKAGE <span>→</span> HUMAN REVIEW <strong>No flight commands</strong></div>
      </div>
      <div id="ot-specialist-panel" className="ot-specialist-panel" key={branch}>
        <div className="ot-specialist-heading"><span>{branchData.code} / EXPANDED BRANCH</span><h3>{branchData.name}</h3><p>{branchData.purpose}</p><div className="ot-dependencies">{branch==='finance'?'Evidence → Collision → Finance ← Terrain (if supplied)':branch==='terrain'?'Footprint gate → Terrain → Exposure → Finance':branch==='judge'?'All findings → Guardrails → Analyst':'Scenario → Evidence gate → Specialist findings'}</div></div>
        <div className="ot-specialists">{branchData.specialists.map((s,i)=><details key={s.name} className="ot-specialist"><summary><span>{String(i+1).padStart(2,'0')}</span><strong>{s.name}</strong><b>+</b></summary><dl><dt>Input</dt><dd>{s.input}</dd><dt>Output</dt><dd>{s.output}</dd><dt>Runtime</dt><dd>{branch==='terrain'?'Integration gate only; data not supplied.':'Architecture node; branch findings computed in local demonstration.'}</dd></dl></details>)}</div>
        <div className="ot-branch-finding"><span>{cursor>=agentBranches.findIndex(b=>b.id===branch)+1?'RECORDED FINDING':'PREVIEW / NOT YET RECORDED'}</span><p>{result.findings[branch]}</p></div>
      </div>
      {branch==='finance'&&<div className="ot-finance-lab"><div><p className="ot-eyebrow">FINANCIAL WHAT-IF / USD</p><h3>Make the assumptions visible.</h3><p>Replacement {usd(result.input.replacement)} + daily revenue {usd(result.input.dailyRevenue)} × downtime. No probability weighting or insurance recovery.</p></div><label>Service downtime <strong>{lossDays} days</strong><input type="range" min="0" max="60" value={lossDays} onChange={e=>setLossDays(Number(e.target.value))}/></label><div className="ot-finance-value"><span>Conditional loss</span><strong>{usd(result.input.replacement+result.input.dailyRevenue*lossDays)}</strong><small>Response-cost assumption: {usd(result.input.responseCost)}<br/>This sandbox value does not change the recorded trace.</small></div></div>}
      <div className="ot-trace-strip" aria-live="polite"><span className="ot-trace-led"/><span>{cursor<0?'Ready to run a reproducible scenario.':events[cursor].detail}</span><button onClick={openActivity}>View activity ↗</button></div>
      <p className="ot-disclaimer">Inspired by the router, specialist, judge and trace pattern in <a href="https://github.com/Adhirajsingh2507/Error-404-Not-Found" target="_blank" rel="noreferrer">your Finora repository ↗</a>. Satellite-specific modules shown here are a proposed architecture with a local demonstration, not a connected production agent service.</p>
    </section>

    <section id="activity" ref={activity} className={`ot-activity ot-reveal ${activityOpen?'expanded':''}`} aria-labelledby="activity-title">
      <button className="ot-activity-trigger" onClick={()=>setActivityOpen(v=>!v)} aria-expanded={activityOpen} aria-controls="ot-activity-content"><div><span className="ot-eyebrow">03 / ACTIVITY THEATRE</span><h2 id="activity-title">Every signal.<br/><span>A visible history.</span></h2><p>{activityOpen?'Close the event ledger':'Open the event ledger'} <b>↗</b></p></div><div className="ot-signal-sculpture" aria-hidden="true">{Array.from({length:24},(_,i)=><span key={i} style={{height:`${20+Math.abs(Math.sin(i*1.63))*95}%`,animationDelay:`${i*.07}s`}}/>)}</div></button>
      <div className="ot-activity-meta"><span>{timeline.length} visible events</span><span>3D signal sculpture / recorded trace</span><span>FIXTURE + LOCAL RUN</span></div>
      {activityOpen&&<div id="ot-activity-content" className="ot-activity-content"><div className="ot-ledger-toolbar"><div role="group" aria-label="Activity filter">{[['all','All signals'],['alert','Attention'],['calc','Calculations'],['data','Imports']].map(([key,label])=><button key={key} aria-pressed={activityFilter===key} onClick={()=>{setActivityFilter(key);setTraceEvent(null);}}>{label}</button>)}</div><span>Click an event to inspect</span></div>
        <div className="ot-ledger">{timeline.length===0?<p className="ot-empty">No events match this filter.</p>:timeline.map(e=><button key={e.id} onClick={()=>setTraceEvent(traceEvent===e.id?null:e.id)} aria-expanded={traceEvent===e.id}><time>{e.time}</time><i className={e.kind==='alert'?'attention':''}/><strong>{e.title}</strong><span>{e.kind}</span><b>{traceEvent===e.id?'−':'+'}</b></button>)}</div>
        {eventDetail&&<article className="ot-event-detail" aria-live="polite"><small>{eventDetail.id.startsWith('fixture')?'SUPPLIED HISTORICAL DEMO EVENT':'LOCAL DETERMINISTIC RUN'}</small><h3>{eventDetail.title}</h3><p>{eventDetail.detail}</p><code>event_id: {eventDetail.id}</code></article>}
      </div>}
    </section>

    <section id="satellite-directory" className="ot-satellites ot-reveal" aria-labelledby="satellites-title"><div className="ot-section-heading"><p className="ot-eyebrow">04 / THE CONSTELLATION</p><span className="ot-mode">{String(satellites.length).padStart(2,'0')} DEMO OBJECTS</span></div><div className="ot-satellites-heading"><h2 id="satellites-title">Nothing in orbit<br/><span>exists in isolation.</span></h2><button className="ot-action" onClick={onOrbit}>Explore the red orbits ↗</button></div>
      <div className="ot-satellite-ribbon" aria-hidden="true"><span className="ot-ribbon-orbit"/><span className="ot-ribbon-orbit"/><span className="ot-ribbon-orbit"/><i/><i/><i/><div>CONNECTED BY MOTION.<br/>UNDERSTOOD THROUGH EVIDENCE.</div></div>
      <div className="ot-search-row"><label>Find a spacecraft<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Name, mission or operator"/></label><button aria-pressed={onlyFlagged} onClick={()=>setOnlyFlagged(!onlyFlagged)}>Review flagged {onlyFlagged?'✓':'+'}</button><span>{filtered.length} of {satellites.length} objects</span></div>
      <div className="ot-satellite-grid">{filtered.map((s,i)=><button className="ot-satellite-card" key={s.id} onClick={()=>onSelect(s)}><div><span>{s.id}</span><span>{s.review?'REVIEW FLAG':'DEMO OBJECT'}</span></div><div className="ot-mini-orbit" aria-hidden="true" style={{transform:`rotate(${i*17-30}deg)`}}><i/><b/></div><h3>{s.name}</h3><p>{s.mission}</p><footer><span>{s.altitude} <small>km</small> / {s.inclination}°</span><b>↗</b></footer></button>)}</div>
      {filtered.length===0&&<div className="ot-empty"><h3>No matching spacecraft.</h3><button onClick={()=>{setQuery('');setOnlyFlagged(false);}}>Clear filters</button></div>}
      <div className="ot-alert-demo"><div><span>ENCOUNTER REHEARSAL</span><h3>Know what an alert feels like.</h3><p>Run the close-approach fixture to see a review alert with evidence and next steps.</p></div><button className="ot-action" onClick={()=>{setScenario('review');setCursor(2);setPlaying(false);setAlert(true);setAcknowledged(false);}}>Preview encounter alert ↗</button></div>
      <p className="ot-disclaimer">Fictional spacecraft; expanded orbit spacing and accelerated time. Pulsing red dots identify objects, not confirmed collisions. No live telemetry is connected.</p>
    </section>

    {alert&&!acknowledged&&<aside className="ot-collision-alert" role="alert" aria-label="Demonstration conjunction review alert"><div className="ot-alert-number">!</div><div className="ot-alert-content"><span>DEMO / CONJUNCTION REVIEW</span><h3>Close approach. Clear next steps.</h3><p>120 m linear miss distance at T+300 s.<br/>Covariance is stale. Collision probability is unavailable.</p><div><button onClick={()=>{setAlert(false);document.getElementById('agent-architecture')?.scrollIntoView({behavior:reduced?'instant':'smooth'});setBranch('collision');}}>Inspect evidence ↗</button><button onClick={()=>setAcknowledged(true)}>Acknowledge</button></div><small>A demonstration alert, not a forecast of an actual collision.</small></div><button className="ot-alert-close" onClick={()=>setAlert(false)} aria-label="Dismiss demonstration alert">×</button></aside>}
  </div>;
}
