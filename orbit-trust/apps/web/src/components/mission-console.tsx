"use client";

import { useMemo, useState } from "react";
import { OrbitScene } from "./orbit-scene";
import { activityItems, evidenceChecks, fleetRows, reviewCases, type ReviewCase, type Urgency } from "../lib/demo-data";

export type ConsoleView = "overview" | "queue" | "case" | "fleet" | "satellites" | "reentry" | "activity" | "settings" | "about";

const nav: Array<{ view: ConsoleView; href: string; label: string; icon: string }> = [
  { view: "overview", href: "/", label: "Mission overview", icon: "grid" },
  { view: "queue", href: "/queue/", label: "Review queue", icon: "queue" },
  { view: "fleet", href: "/fleet/", label: "Fleet response", icon: "orbit" },
  { view: "satellites", href: "/satellites/", label: "Satellites", icon: "satellite" },
  { view: "reentry", href: "/reentry/", label: "Reentry sandbox", icon: "map" },
  { view: "activity", href: "/activity/", label: "Activity", icon: "pulse" },
];

const pageMeta: Record<ConsoleView, { eyebrow: string; title: string; description: string }> = {
  overview: { eyebrow: "Mission control", title: "Operational picture", description: "Prioritize conjunction reviews, verify evidence, and compare supplied response options." },
  queue: { eyebrow: "Conjunction review", title: "Review queue", description: "Cases ranked by urgency, evidence quality, and remaining decision time." },
  case: { eyebrow: "OT-0911-014 · revision r18", title: "ASTERIA-3 ↔ COSMOS 2251 DEB", description: "Immediate review required because the command window is closing and evidence is incomplete." },
  fleet: { eyebrow: "Fleet response · 3 objects", title: "Candidate comparison", description: "Check every supplied pair before preferring a response option." },
  satellites: { eyebrow: "Object registry", title: "Satellites", description: "Operator metadata, maneuver capability, contact windows, and economic assumptions." },
  reentry: { eyebrow: "Separate consequence model", title: "Reentry exposure sandbox", description: "Compare supplied footprints against fictional population and asset layers." },
  activity: { eyebrow: "Provenance ledger", title: "Activity", description: "Calculation, import, agent, and analyst events without hidden reasoning." },
  settings: { eyebrow: "Workspace", title: "Settings", description: "Identity, display, data portability, and versioned policy controls." },
  about: { eyebrow: "Method and limits", title: "About ORBIT-TRUST", description: "Evidence-first decision support for conjunction review." },
};

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  if (name === "grid") return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>;
  if (name === "queue") return <svg {...common}><path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r=".8" fill="currentColor"/><circle cx="3.5" cy="12" r=".8" fill="currentColor"/><circle cx="3.5" cy="18" r=".8" fill="currentColor"/></svg>;
  if (name === "orbit") return <svg {...common}><circle cx="12" cy="12" r="2.2"/><ellipse cx="12" cy="12" rx="9" ry="4.2" transform="rotate(-28 12 12)"/><circle cx="19" cy="7" r="1.1" fill="currentColor"/></svg>;
  if (name === "satellite") return <svg {...common}><path d="m9 9 6 6M7.5 12.5l4-4 5 3-4 4zM4 4l5 2-3 3zm16 16-5-2 3-3z"/></svg>;
  if (name === "map") return <svg {...common}><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15"/></svg>;
  if (name === "pulse") return <svg {...common}><path d="M3 12h4l2.2-6 4.1 12 2.2-6H21"/></svg>;
  if (name === "search") return <svg {...common}><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>;
  if (name === "bell") return <svg {...common}><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>;
  if (name === "arrow") return <svg {...common}><path d="M5 12h14m-5-5 5 5-5 5"/></svg>;
  if (name === "check") return <svg {...common}><path d="m5 12 4 4L19 6"/></svg>;
  if (name === "download") return <svg {...common}><path d="M12 3v12m-4-4 4 4 4-4M4 20h16"/></svg>;
  if (name === "menu") return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16"/></svg>;
  if (name === "close") return <svg {...common}><path d="m6 6 12 12M18 6 6 18"/></svg>;
  if (name === "settings") return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></svg>;
  return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></svg>;
}

function StatusPill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function UrgencyBadge({ value }: { value: Urgency }) {
  return <span className={`urgency urgency-${value.toLowerCase()}`}><span aria-hidden="true" />{value}</span>;
}

function AppShell({ view, children }: { view: ConsoleView; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const meta = pageMeta[view];
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <aside className={`sidebar ${open ? "is-open" : ""}`} aria-label="Primary navigation">
        <div className="brand-row">
          <a className="brand" href="/" aria-label="ORBIT-TRUST home">
            <span className="brand-mark"><span /><i /></span>
            <span><strong>ORBIT</strong><b>TRUST</b></span>
          </a>
          <button className="icon-button mobile-close" onClick={() => setOpen(false)} aria-label="Close navigation"><Icon name="close" /></button>
        </div>
        <div className="workspace-switcher">
          <span className="workspace-avatar">AT</span>
          <span><small>Active workspace</small><strong>ASTERIA OPS</strong></span>
          <span className="chevron">⌄</span>
        </div>
        <nav className="nav-list">
          <p>OPERATIONS</p>
          {nav.map((item) => <a key={item.view} href={item.href} className={view === item.view || (view === "case" && item.view === "queue") ? "active" : ""}><Icon name={item.icon} /><span>{item.label}</span>{item.view === "queue" && <em>3</em>}</a>)}
          <p>WORKSPACE</p>
          <a href="/settings/" className={view === "settings" ? "active" : ""}><Icon name="settings" /><span>Settings</span></a>
          <a href="/about/" className={view === "about" ? "active" : ""}><Icon name="info" /><span>Methods & limits</span></a>
        </nav>
        <div className="sidebar-foot">
          <div className="system-state"><span className="live-dot" /><span><strong>Deterministic core</strong><small>Available · demo-2.0</small></span></div>
          <div className="profile"><span className="avatar">AR</span><span><strong>Adhiraj Singh</strong><small>Mission administrator</small></span><button aria-label="Profile menu">•••</button></div>
        </div>
      </aside>
      {open && <button className="backdrop" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <div className="main-column">
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setOpen(true)} aria-label="Open navigation"><Icon name="menu" /></button>
          <div className="global-search"><Icon name="search" size={16} /><span>Search cases, satellites, reports</span><kbd>⌘ K</kbd></div>
          <StatusPill tone="synthetic">SYNTHETIC DATA</StatusPill>
          <button className="icon-button notification" aria-label="Notifications"><Icon name="bell" /><span>3</span></button>
        </header>
        <main id="main-content" className="main-content">
          <div className="page-heading">
            <div><p>{meta.eyebrow}</p><h1>{meta.title}</h1><span>{meta.description}</span></div>
            <div className="heading-actions"><button className="button secondary"><Icon name="download" size={16} /> Export</button><button className="button primary">Import report</button></div>
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}

function Metric({ label, value, note, tone = "" }: { label: string; value: string; note: string; tone?: string }) {
  return <article className={`metric ${tone}`}><div><span>{label}</span><i aria-hidden="true">↗</i></div><strong>{value}</strong><small>{note}</small></article>;
}

function QueueTable({ compact = false }: { compact?: boolean }) {
  const [filter, setFilter] = useState<"All" | Urgency>("All");
  const rows = useMemo(() => reviewCases.filter((item) => filter === "All" || item.urgency === filter), [filter]);
  return (
    <section className="panel queue-panel">
      <div className="panel-header split">
        <div><h2>{compact ? "Needs attention" : "Active conjunctions"}</h2><p>{compact ? "Ordered by urgency and remaining decision time" : `${reviewCases.length} active cases · updated 28 seconds ago`}</p></div>
        {compact ? <a className="text-link" href="/queue/">Open full queue <Icon name="arrow" size={15} /></a> : <button className="button secondary">Filter & sort</button>}
      </div>
      {!compact && <div className="filter-row" role="group" aria-label="Filter queue by urgency">{(["All", "P0", "P1", "P2", "P3"] as const).map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item}{item !== "All" && <span>{reviewCases.filter((row) => row.urgency === item).length}</span>}</button>)}</div>}
      <div className="table-scroll">
        <table className="queue-table">
          <thead><tr><th>Priority</th><th>Object pair</th><th>Review window</th><th>Reported Pc</th><th>Evidence</th><th>Main reason</th><th>Owner</th><th><span className="sr-only">Open</span></th></tr></thead>
          <tbody>{rows.slice(0, compact ? 4 : rows.length).map((item) => <QueueRow item={item} key={item.id} />)}</tbody>
        </table>
      </div>
    </section>
  );
}

function QueueRow({ item }: { item: ReviewCase }) {
  const evidenceTone = item.evidence === "Usable" ? "success" : item.evidence === "Conflicting" ? "danger" : "warning";
  return <tr>
    <td><UrgencyBadge value={item.urgency} /></td>
    <td><a className="object-pair" href="/case/?id=OT-0911-014"><strong>{item.primary}</strong><span>{item.secondary}</span><small>{item.catalogIds}</small></a></td>
    <td><strong className={item.urgency === "P0" ? "danger-text" : ""}>{item.slack}</strong><small>{item.deadline}</small></td>
    <td><code>{item.pc}</code></td>
    <td><StatusPill tone={evidenceTone}>{item.evidence}</StatusPill></td>
    <td className="reason-cell">{item.reason}<small>{item.stage}</small></td>
    <td><span className="analyst"><i>{item.analyst === "Unassigned" ? "—" : item.analyst.split(" ").map((x) => x[0]).join("")}</i>{item.analyst}</span></td>
    <td><a className="row-arrow" href="/case/?id=OT-0911-014" aria-label={`Open ${item.id}`}><Icon name="arrow" size={16} /></a></td>
  </tr>;
}

function Overview() {
  return <AppShell view="overview">
    <div className="notice-strip urgent"><span className="notice-icon">!</span><div><strong>1 urgent case is past its review deadline</strong><p>ASTERIA-3 remains unacknowledged. The P0 urgency floor cannot be lowered silently.</p></div><a href="/case/?id=OT-0911-014">Review case <Icon name="arrow" size={15} /></a></div>
    <div className="metrics-grid"><Metric label="Review now" value="03" note="1 deadline exceeded" tone="critical"/><Metric label="Evidence issues" value="04" note="Across 3 active cases" tone="warn"/><Metric label="Pending review" value="07" note="2 assigned to you"/><Metric label="Fleet coverage" value="100%" note="3 of 3 supplied objects" tone="positive"/></div>
    <div className="overview-grid">
      <section className="panel scene-panel"><div className="panel-header split"><div><h2>Active encounter</h2><p>OT-0911-014 · closest approach in 2h 18m</p></div><StatusPill tone="danger">P0 · REVIEW NOW</StatusPill></div><OrbitScene/><div className="scene-facts"><div><span>Miss distance</span><strong>100 m</strong></div><div><span>Reported Pc</span><strong>2.73 × 10⁻³</strong></div><div><span>Evidence</span><strong className="amber-text">Incomplete</strong></div></div></section>
      <section className="panel decision-panel"><div className="panel-header"><h2>Decision clock</h2><p>Time remaining against operational gates</p></div><div className="countdown"><small>REVIEW DEADLINE</small><strong>OVERDUE</strong><span>by 08 minutes</span></div><div className="timeline"><div className="timeline-track"><i className="done"/><i className="done"/><i className="late"/><i/></div><div className="timeline-labels"><span>Report<br/><b>09:49</b></span><span>Audit<br/><b>09:50</b></span><span>Review<br/><b>09:42</b></span><span>Command<br/><b>10:35</b></span></div></div><div className="callout"><span>Evidence gap</span><strong>Request a current covariance and secondary maneuver status.</strong><p>This additional observation would reduce the largest uncertainty in the assessment.</p></div><a href="/case/?id=OT-0911-014" className="button primary full">Open evidence review <Icon name="arrow" size={16}/></a></section>
    </div>
    <QueueTable compact />
  </AppShell>;
}

function QueueView() {
  return <AppShell view="queue"><div className="notice-strip urgent"><span className="notice-icon">!</span><div><strong>Capacity threshold exceeded</strong><p>3 cases need review now; 2 analysts are currently available.</p></div><a href="/activity/">View activity <Icon name="arrow" size={15}/></a></div><div className="metrics-grid"><Metric label="P0 / P1" value="03" note="60% of active queue" tone="critical"/><Metric label="Incomplete evidence" value="02" note="1 missing deadline" tone="warn"/><Metric label="Unassigned" value="01" note="Immediate triage needed"/><Metric label="Median review slack" value="2h 08m" note="Active cases only"/></div><QueueTable/></AppShell>;
}

function CaseView() {
  const [tab, setTab] = useState("Evidence");
  return <AppShell view="case">
    <div className="case-banner"><div><UrgencyBadge value="P0"/><span><strong>Review deadline exceeded by 08 minutes</strong><small>Urgency cannot be lowered until this assessment is acknowledged.</small></span></div><button className="button danger-button">Acknowledge P0</button></div>
    <div className="case-layout"><div className="case-main">
      <section className="panel attention-panel"><div className="attention-copy"><p>WHY THIS NEEDS ATTENTION</p><h2>Current risk is material, but the evidence is not yet strong enough for a defensible response decision.</h2><div className="reason-list"><span><i>1</i>Reported collision probability exceeds demo policy.</span><span><i>2</i>Primary covariance is older than the accepted evidence window.</span><span><i>3</i>Secondary-object maneuver status is missing.</span></div></div><div className="attention-action"><small>RECOMMENDED NEXT STEP</small><strong>Request updated covariance and maneuver context</strong><button className="button primary">Draft information request</button></div></section>
      <div className="tabs" role="tablist" aria-label="Case sections">{["Evidence","Reports","Response comparison","Economics","Activity"].map((item) => <button key={item} role="tab" aria-selected={tab===item} className={tab===item?"active":""} onClick={() => setTab(item)}>{item}</button>)}</div>
      {tab === "Evidence" ? <div className="evidence-grid"><section className="panel"><div className="panel-header split"><div><h2>Evidence audit</h2><p>Assessment asmt-r18 · policy demo-2.0</p></div><StatusPill tone="warning">2 ACTIONS NEEDED</StatusPill></div><div className="check-list">{evidenceChecks.map((check) => <div className={`check-item ${check.state}`} key={check.label}><span className="check-symbol">{check.state === "pass" ? "✓" : check.state === "fail" ? "×" : "!"}</span><div><strong>{check.label}</strong><p>{check.detail}</p></div><button aria-label={`Expand ${check.label}`}>⌄</button></div>)}</div></section><section className="panel"><div className="panel-header"><h2>Encounter geometry</h2><p>Mean position and supplied uncertainty</p></div><OrbitScene/></section></div> : <section className="panel placeholder-panel"><span>{tab.slice(0,1)}</span><h2>{tab}</h2><p>This foundation preserves the final information architecture. Data wiring for this panel follows its versioned contract in the implementation handoff.</p><button className="button secondary">View contract</button></section>}
    </div><aside className="case-side"><section className="panel side-card"><h3>Case control</h3><label>Assigned analyst<select defaultValue="A. Rao"><option>A. Rao</option><option>M. Chen</option><option>S. Iyer</option></select></label><label>Review stage<select defaultValue="Review now"><option>Review now</option><option>Evidence check</option><option>Analysis ready</option></select></label><label>Operator note<textarea placeholder="Add an evidence-linked note…"/></label><button className="button secondary full">Save note</button></section><section className="panel source-card"><h3>Assessment record</h3><dl><div><dt>Method</dt><dd>linear-gaussian-2d</dd></div><div><dt>Input revision</dt><dd>r18</dd></div><div><dt>Calculated</dt><dd>09:50:42 IST</dd></div><div><dt>Runtime</dt><dd>18 ms</dd></div></dl><a href="/activity/">View provenance <Icon name="arrow" size={14}/></a></section></aside></div>
  </AppShell>;
}

function FleetView() {
  const [candidate, setCandidate] = useState("two");
  return <AppShell view="fleet"><div className="coverage-strip"><div><span className="coverage-icon"><Icon name="check"/></span><span><strong>Complete supplied-fleet coverage</strong><small>All 3 objects · all 3 unordered pairs · 10-second synthetic segment</small></span></div><StatusPill tone="success">CALCULATION COMPLETE</StatusPill></div><div className="candidate-grid"><button className={candidate==="base"?"candidate active":"candidate"} onClick={()=>setCandidate("base")}><span>Baseline</span><strong>No response</strong><small>1 pair over threshold</small><StatusPill tone="danger">Blocked</StatusPill></button><button className={candidate==="one"?"candidate active":"candidate"} onClick={()=>setCandidate("one")}><span>Candidate 01</span><strong>Along-track +0.1 m/s</strong><small>Creates a new A–C concern</small><StatusPill tone="danger">Blocked</StatusPill></button><button className={candidate==="two"?"candidate active":"candidate"} onClick={()=>setCandidate("two")}><span>Candidate 02</span><strong>Along-track −0.2 m/s</strong><small>All supplied pairs below threshold</small><StatusPill tone="success">Passes demo checks</StatusPill></button></div><section className="panel"><div className="panel-header split"><div><h2>Pair-by-pair comparison</h2><p>Probability of collision · demo threshold 1.00 × 10⁻⁴</p></div><StatusPill tone="synthetic">SUPPLIED TRAJECTORIES</StatusPill></div><div className="table-scroll"><table className="matrix-table"><thead><tr><th>Object pair</th><th>Baseline</th><th>Candidate 01</th><th className="selected-col">Candidate 02</th></tr></thead><tbody>{fleetRows.map(row=><tr key={row.pair}><td><strong>{row.pair}</strong></td><td><MatrixValue value={row.baseline} state={row.baselineState}/></td><td><MatrixValue value={row.one} state={row.oneState}/></td><td className="selected-col"><MatrixValue value={row.two} state={row.twoState}/></td></tr>)}</tbody></table></div><div className="fleet-verdict"><span className="verdict-icon"><Icon name="check"/></span><div><small>PREFERRED AMONG SUPPLIED OPTIONS UNDER DEMO POLICY</small><strong>Candidate 02 avoids the secondary conjunction introduced by Candidate 01.</strong><p>This is a comparison of supplied trajectories. It is not an optimized or flight-ready maneuver.</p></div><button className="button primary">Open response record</button></div></section></AppShell>;
}

function MatrixValue({value,state}:{value:string;state:string}) { return <span className={`matrix-value ${state}`}><i>{state==="good"?"✓":"!"}</i><code>{value}</code></span>; }

function SatellitesView() {
  const satellites = [
    ["ASTERIA-3","58422","Asteria Labs","Capable","Bengaluru · 10:21–10:29","Active"],
    ["VARUNA-2","59103","Oceanic Research","Capable","Sriharikota · 10:44–10:52","Active"],
    ["PRITHVI-7","57431","GeoVision India","Limited","Lucknow · 11:08–11:14","Active"],
    ["OCEANWATCH-1","55390","Blue Orbit","Unknown","Not supplied","Evidence needed"],
  ];
  return <AppShell view="satellites"><section className="panel"><div className="panel-header split"><div><h2>Supplied catalogue</h2><p>4 operator-managed objects · metadata revision 12</p></div><button className="button primary">Add satellite</button></div><div className="table-scroll"><table className="registry-table"><thead><tr><th>Satellite</th><th>Catalog ID</th><th>Operator</th><th>Maneuver capability</th><th>Next contact</th><th>Data state</th><th/></tr></thead><tbody>{satellites.map((sat)=><tr key={sat[0]}><td><span className="sat-name"><i><Icon name="satellite" size={16}/></i><strong>{sat[0]}</strong></span></td><td><code>{sat[1]}</code></td><td>{sat[2]}</td><td>{sat[3]}</td><td>{sat[4]}</td><td><StatusPill tone={sat[5]==="Active"?"success":"warning"}>{sat[5]}</StatusPill></td><td><button className="row-arrow" aria-label={`Edit ${sat[0]}`}>•••</button></td></tr>)}</tbody></table></div></section></AppShell>;
}

function ReentryView() {
  const [footprint,setFootprint]=useState<"A"|"B">("B");
  return <AppShell view="reentry"><div className="notice-strip sandbox"><span className="notice-icon"><Icon name="info"/></span><div><strong>Supplied footprint scenario · no reentry trajectory prediction</strong><p>This sandbox estimates exposure only for the fictional points and assumptions shown below.</p></div></div><div className="reentry-layout"><section className="panel map-panel"><div className="panel-header split"><div><h2>Exposure layer</h2><p>Fictional regional sample · layer revision terrain-2</p></div><div className="segmented"><button className={footprint==="A"?"active":""} onClick={()=>setFootprint("A")}>Footprint A</button><button className={footprint==="B"?"active":""} onClick={()=>setFootprint("B")}>Footprint B</button></div></div><div className="terrain-map"><div className="map-grid"/><svg viewBox="0 0 800 440" role="img" aria-label={`Synthetic terrain exposure map showing footprint ${footprint}`}><path className="terrain-coast" d="M35 120C140 55 225 92 312 55s174 11 239 1 122 27 214 82v252H35Z"/><path className="terrain-line" d="M78 301c116-76 210-50 303-111s185-21 340 48"/><path className="terrain-line faint" d="M64 192c121 41 174-25 261 21s176 28 353-39"/>{footprint==="A"?<path className="footprint danger" d="M282 103c88-23 174 18 218 77s1 108-73 137-182-7-221-71 4-124 76-143Z"/>:<path className="footprint safe" d="M443 69c83-9 165 33 205 91s21 106-45 133-149 6-196-49-43-139 36-175Z"/>}<g className="map-points"><circle cx="318" cy="198" r="7"/><circle cx="380" cy="252" r="7"/><circle cx="514" cy="168" r="7"/><circle cx="584" cy="224" r="7"/><rect x="465" y="204" width="13" height="13" rx="2"/><rect x="621" y="272" width="13" height="13" rx="2"/></g></svg><div className="map-legend"><span><i className="pop-dot"/>Population sample</span><span><i className="asset-dot"/>Asset sample</span><span><i className="area-swatch"/>Supplied footprint</span></div></div></section><aside className="reentry-side"><section className="panel"><div className="panel-header"><h2>Exposure summary</h2><p>Conditional on Footprint {footprint}</p></div><div className="exposure-stats"><div><span>Represented population</span><strong>{footprint==="A"?"18,420":"4,860"}</strong><small>{footprint==="A"?"3 of 4":"1 of 4"} samples included</small></div><div><span>Assets in footprint</span><strong>{footprint==="A"?"₹38.6 Cr":"₹9.2 Cr"}</strong><small>Replacement value supplied</small></div><div><span>Conditional expected loss</span><strong>{footprint==="A"?"₹2.74 Cr":"₹0.41 Cr"}</strong><small>Assumptions visible below</small></div></div></section><section className="panel assumptions"><h3>Model boundaries</h3><ul><li><Icon name="check" size={15}/>Valid supplied GeoJSON polygon</li><li><Icon name="check" size={15}/>Boundary and holes preserved</li><li><span>!</span>No breakup or survivability model</li><li><span>!</span>No predicted landing corridor</li></ul><button className="button secondary full">View all assumptions</button></section></aside></div></AppShell>;
}

function ActivityView() {
  return <AppShell view="activity"><section className="panel activity-panel"><div className="panel-header split"><div><h2>Assessment timeline</h2><p>Immutable workspace events · newest first</p></div><div className="segmented"><button className="active">All</button><button>Calculations</button><button>Analyst</button></div></div><div className="activity-list">{activityItems.map((item,index)=><div className="activity-item" key={item.time}><div className={`activity-glyph ${item.kind}`}>{item.kind==="calc"?"ƒ":item.kind==="data"?"↓":"!"}</div><div><strong>{item.title}</strong><p>{item.detail}</p><small>ASTERIA OPS · assessment r18</small></div><time>{item.time} IST</time>{index<activityItems.length-1&&<i className="activity-line"/>}</div>)}</div></section></AppShell>;
}

function SettingsView() {
  return <AppShell view="settings"><div className="settings-grid"><section className="panel settings-section"><div className="panel-header"><h2>Display</h2><p>Preferences apply to this workspace.</p></div><label>Display currency<select defaultValue="INR"><option>INR — Indian rupee</option><option>USD — US dollar</option></select></label><label>Density<select defaultValue="Comfortable"><option>Comfortable</option><option>Compact</option></select></label><label className="toggle-row"><span><strong>Reduced motion</strong><small>Limit nonessential interface animation</small></span><input type="checkbox"/></label></section><section className="panel settings-section"><div className="panel-header"><h2>Data portability</h2><p>Export a reproducible assessment bundle.</p></div><button className="button secondary full"><Icon name="download" size={16}/>Export workspace data</button><button className="button secondary full">Import validated bundle</button></section><section className="panel settings-section"><div className="panel-header"><h2>Policy</h2><p>Current version is read-only.</p></div><dl><div><dt>Version</dt><dd>demo-2.0</dd></div><div><dt>Pc threshold</dt><dd>1.00 × 10⁻⁴</dd></div><div><dt>Immediate slack</dt><dd>60 minutes</dd></div></dl><button className="button secondary full">Create policy revision</button></section></div></AppShell>;
}

function AboutView() {
  return <AppShell view="about"><div className="about-grid"><section className="panel prose-panel"><span className="about-mark"><span/><i/></span><h2>Evidence before automation</h2><p>ORBIT-TRUST helps an analyst decide which conjunction warning deserves attention, whether its inputs are trustworthy, and which supplied response deserves deeper review.</p><h3>What this demonstration does</h3><ul><li>Separates urgency from evidence quality.</li><li>Preserves report revisions and calculation provenance.</li><li>Compares supplied alternatives across the loaded fleet.</li><li>Explains missing information and the next analyst action.</li></ul><h3>Scientific boundary</h3><p>The current encounter model is a declared short, linear, Gaussian approximation. The interface labels unsupported inputs instead of turning them into confident prose.</p></section><section className="panel engine-card"><div className="panel-header"><h2>Reusable engine foundation</h2><p>Imported from the preserved 3d-game ecosystem</p></div><div className="engine-stack"><div><span>01</span><strong>Math core</strong><small>Vec3 · Mat4 · Quaternion · Transform · geometry</small></div><div><span>02</span><strong>Physics core</strong><small>Rigid body · broadphase · contacts · impulse solver</small></div><div><span>03</span><strong>Graphics</strong><small>WebGL2 · PBR · shadows · HDR · bloom · ACES</small></div><div><span>04</span><strong>Server renderer</strong><small>Path tracing · GI · metals · depth of field</small></div></div><div className="engine-note">The live encounter visual reuses the engine’s vector math and procedural sphere model. Operational orbital calculations remain a separate, versioned scientific core.</div></section></div></AppShell>;
}

export function MissionConsole({ view }: { view: ConsoleView }) {
  if (view === "queue") return <QueueView/>;
  if (view === "case") return <CaseView/>;
  if (view === "fleet") return <FleetView/>;
  if (view === "satellites") return <SatellitesView/>;
  if (view === "reentry") return <ReentryView/>;
  if (view === "activity") return <ActivityView/>;
  if (view === "settings") return <SettingsView/>;
  if (view === "about") return <AboutView/>;
  return <Overview/>;
}
