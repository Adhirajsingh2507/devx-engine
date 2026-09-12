'use client';

import Link from 'next/link';
import {usePathname,useRouter} from 'next/navigation';
import {useEffect,useRef,useState,type ReactNode} from 'react';
import {orbitalDemo} from '../lib/orbital-demo';
import {reviewCases} from '../lib/demo-data';
import {WorkspaceProvider,useWorkspace} from './workspace-state';
import './workspace.css';

export const workspacePages=[
  {id:'overview',name:'Mission overview',group:'Operations',icon:'overview',description:'Review priorities and recent assessment results.'},
  {id:'satellites',name:'Satellites',group:'Operations',icon:'satellite',description:'Search the demo registry and inspect spacecraft.'},
  {id:'orbits',name:'Orbital view',group:'Operations',icon:'orbit',description:'Inspect the ray-traced Earth and illustrative constellation.'},
  {id:'collision',name:'Collision review',group:'Operations',icon:'collision',description:'Search cases and inspect the evidence behind each warning.'},
  {id:'agents',name:'Agent orchestrator',group:'Analysis tools',icon:'agents',description:'Run a local assessment and inspect each specialist branch.'},
  {id:'finance',name:'Financial analysis',group:'Analysis tools',icon:'finance',description:'Calculate conditional loss and compare explicit response assumptions.'},
  {id:'terrain',name:'Terrain analysis',group:'Analysis tools',icon:'terrain',description:'Inspect the inputs required for a ground-exposure assessment.'},
  {id:'activity',name:'Activity',group:'Workspace',icon:'activity',description:'Inspect local assessment results and supplied historical events.'},
  {id:'methods',name:'Methods & limits',group:'Workspace',icon:'methods',description:'Understand the data, models and current integration boundaries.'},
];
export type WorkspacePageId=typeof workspacePages[number]['id'];
export function WorkspaceIcon({name}:{name:string}){return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{name==='overview'?<><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><path d="M3 14h7v7H3zM14 14h7v7h-7z"/></>:name==='orbit'||name==='satellite'?<><circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="5" transform="rotate(-30 12 12)"/><circle cx="19" cy="7" r="1" fill="currentColor"/></>:name==='finance'?<><path d="M4 20V10m8 10V4m8 16v-7M2 20h20"/></>:name==='agents'?<><rect x="9" y="2" width="6" height="5"/><path d="M12 7v5M4 16v-4h16v4"/><rect x="1" y="16" width="6" height="5"/><rect x="9" y="16" width="6" height="5"/><rect x="17" y="16" width="6" height="5"/></>:name==='terrain'?<><path d="m2 18 6-12 5 8 3-5 6 9H2Z"/></>:name==='activity'?<path d="M2 12h5l3-7 4 14 3-7h5"/>:name==='search'?<><circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/></>:name==='collision'?<><path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3v.1"/></>:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/></>}</svg>;}

function Shell({children}:{children:ReactNode}){
  const pathname=usePathname(),router=useRouter(),store=useWorkspace();
  const current=workspacePages.find(p=>pathname.replace(/\/$/,'').endsWith('/'+p.id))??workspacePages[0];
  const [filter,setFilter]=useState(''),[menu,setMenu]=useState(false),[search,setSearch]=useState(false),[query,setQuery]=useState('');
  const [mobile,setMobile]=useState(false);
  const dialog=useRef<HTMLDialogElement>(null),input=useRef<HTMLInputElement>(null),menuButton=useRef<HTMLButtonElement>(null),side=useRef<HTMLElement>(null);
  const results=[...workspacePages.map(p=>({label:p.name,type:'Page',href:`/app/${p.id}/`,action:()=>{}})),...orbitalDemo.map(s=>({label:s.name,type:'Satellite',href:'/app/satellites/',action:()=>store.setSelectedSat(s.id)})),...reviewCases.map(c=>({label:`${c.id} · ${c.primary}`,type:'Case',href:'/app/collision/',action:()=>store.setCaseId(c.id)}))].filter(r=>`${r.label} ${r.type}`.toLowerCase().includes(query.toLowerCase()));
  useEffect(()=>{setMenu(false);setSearch(false);},[pathname]);
  useEffect(()=>{const mq=matchMedia('(max-width:850px)');const update=()=>setMobile(mq.matches);update();mq.addEventListener('change',update);return()=>mq.removeEventListener('change',update);},[]);
  useEffect(()=>{if(search){dialog.current?.showModal();input.current?.focus();}else dialog.current?.close();},[search]);
  useEffect(()=>{const onKey=(e:KeyboardEvent)=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();setSearch(v=>!v);}if(e.key==='Escape'){setMenu(false);menuButton.current?.focus();}};document.addEventListener('keydown',onKey);return()=>document.removeEventListener('keydown',onKey);},[]);
  useEffect(()=>{if(menu)side.current?.querySelector<HTMLInputElement>('input')?.focus();},[menu]);
  function navigate(result:typeof results[number]){result.action();setSearch(false);setQuery('');router.push(result.href);}
  return <div className="ot-app-shell">
    <a className="wa-skip" href="#workspace-content">Skip to page content</a>
    <aside ref={side} className={`wa-sidebar ${menu?'open':''}`} aria-label="Workspace navigation" inert={mobile&&!menu} onKeyDown={e=>{if(!mobile||!menu||e.key!=='Tab')return;const items=side.current?.querySelectorAll<HTMLElement>('a,button,input');if(!items?.length)return;const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}}>
      <Link href="/" className="wa-brand"><span className="wa-brand-mark"><i/></span>ORBIT<span>TRUST</span></Link>
      <div className="wa-workspace"><span>AO</span><div><strong>Asteria operations</strong><small>Demo workspace</small></div><button className="wa-mobile-close" onClick={()=>{setMenu(false);menuButton.current?.focus();}} aria-label="Close menu">×</button></div>
      <label className="wa-nav-filter"><WorkspaceIcon name="search"/><input aria-label="Filter pages" placeholder="Find a page…" value={filter} onChange={e=>setFilter(e.target.value)}/>{filter&&<button onClick={()=>setFilter('')} aria-label="Clear page filter">×</button>}</label>
      <nav>{['Operations','Analysis tools','Workspace'].map(group=>{const pages=workspacePages.filter(p=>p.group===group&&p.name.toLowerCase().includes(filter.toLowerCase()));return pages.length>0&&<section key={group}><p>{group}</p>{pages.map(p=><Link key={p.id} href={`/app/${p.id}/`} aria-current={p.id===current.id?'page':undefined} onClick={()=>setMenu(false)}><WorkspaceIcon name={p.icon}/><span>{p.name}</span>{p.id==='collision'&&<small>3</small>}</Link>)}</section>;})}{!workspacePages.some(p=>p.name.toLowerCase().includes(filter.toLowerCase()))&&<div className="wa-nav-empty">No matching pages.<button onClick={()=>setFilter('')}>Clear filter</button></div>}</nav>
      <footer><span className="wa-status-dot"/><div><strong>Local demonstration</strong><small>No live telemetry connected</small></div><Link href="/" aria-label="Back to landing page">↗</Link></footer>
    </aside>
    {menu&&<button className="wa-menu-backdrop" aria-label="Close navigation overlay" onClick={()=>setMenu(false)}/>}
    <div className="wa-main-column"><header className="wa-topbar"><button ref={menuButton} className="wa-menu-button" onClick={()=>setMenu(!menu)} aria-expanded={menu} aria-label="Open menu">☰</button><span className="wa-breadcrumb">Workspace <span>/</span> {current.name}</span><button className="wa-search-trigger" onClick={()=>{setQuery('');setSearch(true);}}><WorkspaceIcon name="search"/><span>Search pages, satellites, cases</span><kbd>Ctrl K</kbd></button><span className="wa-demo">DEMO</span></header>
      <main id="workspace-content" className="wa-content" key={current.id}><header className="wa-page-heading"><div><h1>{current.name}</h1><p>{current.description}</p></div><span className="wa-page-index">{String(workspacePages.indexOf(current)+1).padStart(2,'0')} / 09</span></header>{children}</main>
      <footer className="wa-app-footer"><span>ORBIT-TRUST / Mission workspace</span><span>Session data stays in this tab until refresh.</span></footer>
    </div>
    <dialog ref={dialog} className="wa-command" aria-label="Search workspace" onCancel={()=>setSearch(false)}><header><WorkspaceIcon name="search"/><input ref={input} aria-label="Search workspace" placeholder="Search a page, spacecraft or case…" value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&results[0])navigate(results[0]);if(e.key==='ArrowDown'){e.preventDefault();dialog.current?.querySelector<HTMLButtonElement>('.wa-search-results button')?.focus();}}}/><button onClick={()=>setSearch(false)} aria-label="Close search">Esc</button></header><div className="wa-search-results">{results.length?results.map(r=><button key={r.label} onClick={()=>navigate(r)}><span>{r.label}</span><small>{r.type} ↗</small></button>):<p>No matching pages, spacecraft or cases.</p>}</div><footer>Enter opens the first result. Tab through results to choose another.</footer></dialog>
  </div>;
}
export function WorkspaceShell({children}:{children:ReactNode}){return <WorkspaceProvider><Shell>{children}</Shell></WorkspaceProvider>;}
