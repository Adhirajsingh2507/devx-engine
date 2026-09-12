'use client';

import { useEffect, useRef, useState } from 'react';
import { createEarthRenderer, projectOrbit, type EarthFrame } from '../../../../../3d-game/apps/client/src/earth/renderer';
import { orbitalDemo, periodMinutes, satellitePoint, speedKmS, type DemoSatellite } from '../lib/orbital-demo';
import './earth-hero.css';
import './mission-experience.css';
import { MissionExperience } from './mission-experience';
import { WelcomeSequence } from './welcome-sequence';

const ease=(t:number)=>t*t*(3-2*t);
const clamp=(t:number)=>Math.max(0,Math.min(1,t));

function Arrow({ down=false }: { down?:boolean }) {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" style={down?{transform:'rotate(90deg)'}:undefined}><path d="M4 12h15m-6-6 6 6-6 6"/></svg>;
}

export function EarthHero() {
  const journey=useRef<HTMLElement>(null),stage=useRef<HTMLDivElement>(null),canvas=useRef<HTMLCanvasElement>(null);
  const intro=useRef<HTMLDivElement>(null),explore=useRef<HTMLDivElement>(null),overlay=useRef<HTMLDivElement>(null);
  const dots=useRef<(HTMLButtonElement|null)[]>([]),paths=useRef<(SVGPathElement|null)[]>([]),progress=useRef<HTMLSpanElement>(null);
  const pausedRef=useRef(false),hoverRef=useRef(false),reducedRef=useRef(false),activeRef=useRef<string|null>(null);
  const [status,setStatus]=useState<'loading'|'ready'|'error'>('loading'),[error,setError]=useState('');
  const [retry,setRetry]=useState(0),[paused,setPaused]=useState(false),[reduced,setReduced]=useState(false);
  const [selected,setSelected]=useState<DemoSatellite|null>(null),[pinned,setPinned]=useState(false);
  const [menu,setMenu]=useState(false);
  const [arrived,setArrived]=useState(false);

  useEffect(()=>{pausedRef.current=paused;},[paused]);
  useEffect(()=>{activeRef.current=selected?.id??null;},[selected]);
  useEffect(()=>{
    // Opt-in local design capture; ordinary visits make no Figma request.
    if(process.env.NODE_ENV==='development'&&window.location.hash.includes('figmacapture=')&&!document.querySelector('script[data-earth-figma]')){
      const script=document.createElement('script');script.src='https://mcp.figma.com/mcp/html-to-design/capture.js';script.async=true;script.dataset.earthFigma='true';document.head.appendChild(script);
    }
  },[]);
  useEffect(()=>{
    const mq=window.matchMedia('(prefers-reduced-motion: reduce)');
    const update=()=>{setReduced(mq.matches);reducedRef.current=mq.matches;};update();
    mq.addEventListener('change',update);return()=>mq.removeEventListener('change',update);
  },[]);

  useEffect(()=>{
    const c=canvas.current,section=journey.current,el=stage.current;
    if(!c||!section||!el)return;
    const abort=new AbortController();let disposed=false,raf=0,last=0,seconds=0;
    let renderer:Awaited<ReturnType<typeof createEarthRenderer>>|undefined;
    let width=el.clientWidth,height=el.clientHeight,quality=.85,smoothedP=0,frameAverage=16.7,lastQualityCheck=0;
    let sectionTop=0,sectionTravel=1,currentScroll=window.scrollY,drawCount=0,statsTime=0;
    const measure=()=>{width=el.clientWidth;height=el.clientHeight;sectionTop=window.scrollY+section.getBoundingClientRect().top;sectionTravel=Math.max(1,section.offsetHeight-height);lastFrame='';};
    const onScroll=()=>{currentScroll=window.scrollY;};window.addEventListener('scroll',onScroll,{passive:true});
    let lastFrame='',lastOrbitFrame='',offscreen=false;
    const resize=new ResizeObserver(measure);resize.observe(el);resize.observe(section);measure();
    const visibility=new IntersectionObserver(([entry])=>{offscreen=!entry.isIntersecting;},{rootMargin:'50px'});visibility.observe(el);
    const orbitSamples=orbitalDemo.map(s=>Array.from({length:113},(_,j)=>satellitePoint(s,0,j/112*Math.PI*2)));
    const fail=(message:string)=>{setError(message);setStatus('error');};
    const contextLost=(event:Event)=>{event.preventDefault();fail('The graphics session was interrupted. Retry the scene, or use the satellite list below.');renderer?.dispose();renderer=undefined;};
    c.addEventListener('webglcontextlost',contextLost);
    const tick=(now:number)=>{
      if(disposed)return;
      raf=requestAnimationFrame(tick);
      const frameMs=last?now-last:16.7,delta=Math.min(frameMs/1000,0.1);last=now;
      if(document.hidden||offscreen)return;
      const targetP=clamp((currentScroll-sectionTop)/sectionTravel);
      smoothedP=reducedRef.current?targetP:smoothedP+(targetP-smoothedP)*(1-Math.exp(-delta*14));
      if(Math.abs(targetP-smoothedP)<.0001)smoothedP=targetP;
      const p=smoothedP;
      frameAverage=frameAverage*.9+Math.min(frameMs,2000)*.1;
      // Time-based adaptation remains responsive even on software renderers.
      if(now-lastQualityCheck>1500){if(frameAverage>28)quality=Math.max(.3,quality*.75);else if(frameAverage<18)quality=Math.min(1,quality+.025);lastQualityCheck=now;}
      const pull=ease(clamp(p/0.78)),mobile=width<768,reduce=reducedRef.current;
      const running=!pausedRef.current&&!hoverRef.current&&!reduce;
      if(running)seconds+=delta;
      const startX=Math.max(0.82,0.52+0.66*height/width);
      const frame:EarthFrame={distance:reduce?6.5:mobile?3.5+pull*3.4:2.65+pull*3.55,
        centerX:reduce?0.5:mobile?0.66-pull*0.16:startX+(0.5-startX)*pull,
        centerY:reduce?0.52:mobile?0.79-pull*0.25:0.65-pull*0.12,
        rotation:0.65+seconds*0.016+(reduce?0:pull*0.25)};
      const reveal=ease(clamp((p-0.36)/0.35));
      if(intro.current){intro.current.style.opacity=String(1-clamp(p/0.27));intro.current.style.transform=`translate3d(0,${reduce?0:-p*90}px,0)`;intro.current.inert=p>0.25;}
      if(explore.current){explore.current.style.opacity=String(reveal);explore.current.inert=reveal<0.8;}
      if(overlay.current){overlay.current.style.opacity=String(reveal);overlay.current.inert=reveal<0.8;}
      if(progress.current)progress.current.style.transform=`scaleX(${p})`;
      el.dataset.phase=p<0.35?'earth':'orbits';
      const key=[frame.distance.toFixed(3),frame.rotation.toFixed(4),width,height,quality].join('/');
      if(renderer&&key!==lastFrame){
        if(renderer.draw(frame,width,height,quality))drawCount++;lastFrame=key;
      }
      if(now-statsTime>1000){c.dataset.renderFps=String(Math.round(drawCount*1000/(now-statsTime)));c.dataset.frameFps=String(Math.round(1000/frameAverage));c.dataset.renderScale=quality.toFixed(2);drawCount=0;statsTime=now;}
      const orbitKey=[frame.distance.toFixed(3),frame.centerX.toFixed(3),frame.centerY.toFixed(3),width,height].join('/');
      const redrawPaths=orbitKey!==lastOrbitFrame;
      orbitalDemo.forEach((sat,i)=>{
        const point=projectOrbit(satellitePoint(sat,seconds),frame,width,height),dot=dots.current[i];
        if(dot){dot.style.transform=`translate3d(${point.x}px,${point.y}px,0)`;dot.style.visibility=point.visible&&reveal>0.5?'visible':'hidden';dot.tabIndex=point.visible&&reveal>0.8?0:-1;}
        // Draw only front-facing segments; hidden satellites cannot shine through Earth.
        const path=paths.current[i];
        if(path&&redrawPaths){
          let d='',pen=false;
          for(let j=0;j<=112;j++){
            const projected=projectOrbit(orbitSamples[i][j],frame,width,height);
            if(!projected.visible){pen=false;continue;}
            d+=`${pen?'L':'M'}${projected.x.toFixed(1)},${projected.y.toFixed(1)} `;pen=true;
          }
          path.setAttribute('d',d);
        }
        if(path)path.style.opacity=activeRef.current===sat.id?'0.85':i%2===0?'0.3':'0.13';
      });
      lastOrbitFrame=orbitKey;
    };
    setStatus('loading');setError('');
    createEarthRenderer(c,abort.signal).then(r=>{
      if(disposed){r.dispose();return;}renderer=r;quality=r.initialQuality;c.dataset.triangles=String(r.triangleCount);c.dataset.renderDevice=r.softwareRenderer?'software':'hardware-or-unknown';setStatus('ready');
    }).catch(e=>{if(!disposed)fail(e instanceof Error?e.message:'Earth scene could not load.');});
    raf=requestAnimationFrame(tick);
    return()=>{disposed=true;abort.abort();cancelAnimationFrame(raf);resize.disconnect();visibility.disconnect();window.removeEventListener('scroll',onScroll);c.removeEventListener('webglcontextlost',contextLost);renderer?.dispose();};
  },[retry]);

  const goToOrbits=()=>{
    if(!journey.current||!stage.current)return;
    const y=window.scrollY+journey.current.getBoundingClientRect().top+(journey.current.offsetHeight-stage.current.clientHeight)*0.86;
    window.scrollTo({top:y,behavior:reduced?'instant':'smooth'});setMenu(false);
  };
  const inspect=(sat:DemoSatellite,pin=false)=>{setSelected(sat);if(pin)setPinned(true);hoverRef.current=true;};
  const dismiss=()=>{setSelected(null);setPinned(false);hoverRef.current=false;};

  return <main className={`earth-experience ot-version-two ${arrived?'has-arrived':''} ${paused||reduced?'motion-paused':''}`}>
    <WelcomeSequence ready={status!=='loading'} onFinish={()=>setArrived(true)}/>
    <a className="earth-skip" href="#satellite-directory">Skip to satellite list</a>
    <header className="earth-nav">
      <a className="earth-brand" href="/" aria-label="ORBIT-TRUST home"><span className="earth-brand-icon" aria-hidden="true"><i/></span>ORBIT<span className="earth-brand-light">TRUST</span></a>
      <nav aria-label="Landing navigation" className={menu?'earth-links open':'earth-links'}>
        <a href="#mission" onClick={()=>setMenu(false)}>Mission</a><a href="#agent-architecture" onClick={()=>setMenu(false)}>Intelligence</a><a href="#activity" onClick={()=>setMenu(false)}>Activity</a><button onClick={goToOrbits}>Satellites</button>
      </nav>
      <a className="earth-console-link" href="/queue/">Review queue <Arrow/></a>
      <button className="earth-menu" aria-label={menu?'Close menu':'Open menu'} aria-expanded={menu} onClick={()=>setMenu(!menu)}>{menu?'Close':'Menu'}</button>
    </header>
    <section ref={journey} className="earth-journey" aria-label="Earth to orbit exploration">
      <div ref={stage} className="earth-stage" data-phase="earth">
        <canvas key={retry} ref={canvas} className="earth-canvas" aria-label="Ray-traced NASA Earth model with a scroll-controlled camera"/>
        <div className="earth-vignette" aria-hidden="true"/>
        {status!=='ready'&&<div className={`earth-load ${status}`} role="status">
          {status==='loading'?<><span className="earth-load-line"/>Preparing your view of Earth</>:<><p>{error}</p><button onClick={()=>setRetry(n=>n+1)}>Retry Earth scene <Arrow/></button><a href="#satellite-directory">Explore satellite list</a></>}
        </div>}
        <div ref={intro} className="earth-intro">
          <p className="earth-kicker"><span/> SPACE SITUATIONAL AWARENESS</p>
          <h1>A clearer view.<br/><span>A safer orbit.</span></h1>
          <p className="earth-lede">Understand the warnings. Uncover the uncertainty.<br className="desktop-break"/> Protect what keeps our world connected.</p>
          <button className="earth-primary" onClick={goToOrbits}>Explore the orbits <Arrow down/></button>
        </div>
        <div ref={explore} className="earth-explore" style={{opacity:0}}>
          <div className="earth-orbit-heading"><p className="earth-kicker">01 / THE ORBITAL PICTURE</p><h2>One planet.<br/>Many perspectives.</h2><p>Select a satellite.<br/>Get closer to its story.</p></div>
          <div className="earth-orbit-toolbar"><span className="earth-demo-label"><i/> DEMO CONSTELLATION</span><button aria-pressed={paused||reduced} onClick={()=>{setPaused(!paused);}} disabled={reduced}>{paused||reduced?'Resume motion':'Pause motion'}</button><small>{reduced?'Reduced motion enabled':'240× time · expanded orbital spacing'}</small></div>
        </div>
        <div ref={overlay} className="earth-orbit-overlay" style={{opacity:0}}>
          <svg className="earth-orbit-lines" aria-hidden="true">{orbitalDemo.map((s,i)=><path key={s.id} ref={e=>{paths.current[i]=e;}} fill="none" stroke="#f14c50" strokeWidth="1.15"/>)}</svg>
          {orbitalDemo.map((s,i)=><button key={s.id} ref={e=>{dots.current[i]=e;}} className={`earth-satellite ${s.review?'review':''} ${selected?.id===s.id?'selected':''}`} aria-label={`Inspect ${s.name}, ${s.mission}${s.review?', review flagged':''}`} aria-pressed={pinned&&selected?.id===s.id}
            onPointerEnter={e=>{if(e.pointerType==='mouse'&&!pinned)inspect(s);}} onPointerLeave={()=>{if(!pinned)dismiss();}}
            onFocus={()=>{if(!pinned)inspect(s);}} onBlur={()=>{if(!pinned)dismiss();}} onClick={()=>inspect(s,true)} onKeyDown={e=>{if(e.key==='Escape')dismiss();}}><span className="earth-dot"/>{(i<3||selected?.id===s.id)&&<span className="earth-sat-label">{s.name}</span>}</button>)}
          {selected&&<aside className="earth-satellite-detail" aria-label={`${selected.name} details`} onKeyDown={e=>{if(e.key==='Escape')dismiss();}}>
            <div className="earth-detail-top"><span>{selected.id} / SIMULATED</span><button onClick={dismiss} aria-label="Close satellite details">×</button></div>
            <h3>{selected.name}</h3><p>{selected.mission}</p>
            <dl><div><dt>Altitude</dt><dd>{selected.altitude.toLocaleString()} <small>km</small></dd></div><div><dt>Inclination</dt><dd>{selected.inclination}<small>°</small></dd></div><div><dt>Orbital period</dt><dd>{periodMinutes(selected).toFixed(1)} <small>min</small></dd></div><div><dt>Orbital speed</dt><dd>{speedKmS(selected).toFixed(2)} <small>km/s</small></dd></div></dl>
            <div className={`earth-detail-status ${selected.review?'review':''}`}>{selected.review?'Flagged for review':'No fixture review flag'}</div><p className="earth-detail-note">{selected.note}</p>
            {selected.id==='OT-001'?<a href="/case/">Inspect example case <Arrow/></a>:<a href="#satellite-directory">Open object registry <Arrow/></a>}
          </aside>}
        </div>
        <div className="earth-stage-foot"><span className="earth-coordinate">EARTH / SOL SYSTEM</span><button onClick={goToOrbits}>SCROLL TO DISCOVER <Arrow down/></button><a href="https://science.nasa.gov/resource/earth-3d-model/" target="_blank" rel="noreferrer">EARTH MODEL · NASA / VTAD <span>↗</span></a></div>
        <div className="earth-progress" aria-hidden="true"><span ref={progress}/></div>
      </div>
    </section>
    <MissionExperience onOrbit={goToOrbits} paused={paused} onPause={()=>setPaused(p=>!p)} satellites={orbitalDemo} onSelect={s=>{inspect(s,true);goToOrbits();}}/>
    <section className="earth-next"><p className="earth-kicker">FROM AWARENESS TO UNDERSTANDING</p><h2>The view is just<br/>the beginning.</h2><div><p>Behind every warning is evidence.<br/>Make space for the decisions that matter.</p><a className="earth-primary" href="/queue/">Review the evidence <Arrow/></a></div></section>
    <footer className="earth-footer"><span>ORBIT-TRUST <small> / EARTH TO ORBIT</small></span><a href="/about/">Methods & limits <Arrow/></a><span>Built for a more informed orbit.</span></footer>
  </main>;
}
