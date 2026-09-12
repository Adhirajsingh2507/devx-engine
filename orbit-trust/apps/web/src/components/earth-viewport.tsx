'use client';
import {useEffect,useRef,useState} from 'react';
import {createEarthRenderer,projectOrbit,type EarthFrame} from '../../../../../3d-game/apps/client/src/earth/renderer';
import {orbitalDemo,satellitePoint} from '../lib/orbital-demo';

/** Shared engine viewport. Camera changes come from controls, never page scroll. */
export function EarthViewport({constellation=false,playing=false,zoom=1,selected,onSelect}:{constellation?:boolean;playing?:boolean;zoom?:number;selected?:string;onSelect?:(id:string)=>void}){
  const wrapper=useRef<HTMLDivElement>(null),canvas=useRef<HTMLCanvasElement>(null),dots=useRef<(HTMLButtonElement|null)[]>([]),paths=useRef<(SVGPathElement|null)[]>([]);
  const config=useRef({playing,zoom,selected});config.current={playing,zoom,selected};
  const hover=useRef(false);
  const [status,setStatus]=useState('loading'),[retry,setRetry]=useState(0);
  useEffect(()=>{
    const el=wrapper.current,canvasElement=canvas.current;if(!el||!canvasElement)return;
    const c:HTMLCanvasElement=canvasElement;
    const abort=new AbortController();let disposed=false,raf=0,last=0,seconds=0,width=el.clientWidth,height=el.clientHeight,visible=true,quality=.75,average=16.7,qualityTime=0,statsTime=0,draws=0;
    let renderer:Awaited<ReturnType<typeof createEarthRenderer>>|undefined;
    let lastPaths='';
    const mq=matchMedia('(prefers-reduced-motion: reduce)');
    const resize=new ResizeObserver(()=>{width=el.clientWidth;height=el.clientHeight;lastPaths='';});resize.observe(el);
    const observer=new IntersectionObserver(([entry])=>visible=entry.isIntersecting);observer.observe(el);
    const samples=orbitalDemo.map(s=>Array.from({length:113},(_,i)=>satellitePoint(s,0,i/112*Math.PI*2)));
    const lost=(e:Event)=>{e.preventDefault();renderer?.dispose();renderer=undefined;setStatus('Graphics session interrupted. Retry to restore Earth.');};c.addEventListener('webglcontextlost',lost);
    function tick(now:number){
      if(disposed)return;raf=requestAnimationFrame(tick);
      const ms=last?now-last:16.7;last=now;if(!visible||document.hidden)return;
      const moving=config.current.playing&&!mq.matches&&!hover.current;
      if(moving)seconds+=Math.min(ms/1000,.1);
      average=average*.9+Math.min(ms,2000)*.1;
      if(now-qualityTime>1500&&moving){quality=average>28?Math.max(.3,quality*.75):average<18?Math.min(1,quality+.025):quality;qualityTime=now;}
      const frame:EarthFrame={distance:constellation?(width<600?10:7.3)/config.current.zoom:3.6,centerX:.5,centerY:constellation?.5:1.12,rotation:.8+seconds*.016};
      if(renderer?.draw(frame,width,height,quality))draws++;
      if(now-statsTime>1000){c.dataset.renderFps=String(Math.round(draws*1000/(now-statsTime)));c.dataset.frameFps=String(Math.round(1000/average));c.dataset.renderScale=quality.toFixed(2);statsTime=now;draws=0;}
      if(!constellation)return;
      const pathKey=[width,height,frame.distance].join('/');
      orbitalDemo.forEach((s,i)=>{
        const p=projectOrbit(satellitePoint(s,seconds),frame,width,height),dot=dots.current[i],path=paths.current[i];
        if(dot){dot.style.transform=`translate3d(${p.x}px,${p.y}px,0)`;dot.style.visibility=p.visible?'visible':'hidden';dot.tabIndex=p.visible?0:-1;}
        if(path&&lastPaths!==pathKey){let d='',pen=false;for(const sample of samples[i]){const point=projectOrbit(sample,frame,width,height);if(!point.visible){pen=false;continue;}d+=`${pen?'L':'M'}${point.x.toFixed(1)},${point.y.toFixed(1)} `;pen=true;}path.setAttribute('d',d);}
        if(path)path.style.opacity=config.current.selected===s.id?'.85':'.23';
      });lastPaths=pathKey;
    }
    setStatus('loading');
    createEarthRenderer(c,abort.signal).then(r=>{if(disposed){r.dispose();return;}renderer=r;quality=r.initialQuality;c.dataset.triangles=String(r.triangleCount);setStatus('ready');}).catch(e=>{if(!disposed)setStatus(e instanceof Error?e.message:'Earth could not load.');});
    raf=requestAnimationFrame(tick);
    return()=>{disposed=true;abort.abort();cancelAnimationFrame(raf);resize.disconnect();observer.disconnect();c.removeEventListener('webglcontextlost',lost);renderer?.dispose();};
  },[constellation,retry]);
  return <div ref={wrapper} className={`wa-earth-viewport ${constellation?'constellation':'landing-globe'}`}><canvas ref={canvas} key={retry} aria-label="NASA Earth model rendered with the custom ray-tracing engine"/>{constellation&&<><svg aria-hidden="true">{orbitalDemo.map((s,i)=><path key={s.id} ref={e=>{paths.current[i]=e;}}/>)}</svg>{orbitalDemo.map((s,i)=><button key={s.id} className={`wa-orbit-dot ${selected===s.id?'selected':''}`} ref={e=>{dots.current[i]=e;}} aria-label={`Inspect ${s.name}`} aria-pressed={selected===s.id} onClick={()=>onSelect?.(s.id)} onPointerEnter={()=>{hover.current=true;}} onPointerLeave={()=>{hover.current=false;}} onFocus={()=>{hover.current=true;}} onBlur={()=>{hover.current=false;}}><i/><span>{s.name}</span></button>)}</>}{status!=='ready'&&<div className="wa-earth-status" role="status">{status==='loading'?'Loading Earth…':<><p>{status}</p><button onClick={()=>setRetry(r=>r+1)}>Retry Earth</button></>}</div>}</div>;
}
