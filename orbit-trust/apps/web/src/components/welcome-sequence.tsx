'use client';
import {useEffect,useRef,useState} from 'react';

export function WelcomeSequence({ready,onFinish}:{ready:boolean;onFinish:()=>void}) {
  const [visible,setVisible]=useState(false),[leaving,setLeaving]=useState(false);
  const dialog=useRef<HTMLDialogElement>(null),elapsed=useRef(false),readyRef=useRef(ready),finishRef=useRef(onFinish);
  readyRef.current=ready;finishRef.current=onFinish;
  useEffect(()=>{
    let seen=false;try{seen=sessionStorage.getItem('orbit-welcome-v2')==='seen';}catch{}
    if(seen||matchMedia('(prefers-reduced-motion: reduce)').matches){finishRef.current();return;}
    setVisible(true);
    const timer=setTimeout(()=>{elapsed.current=true;if(readyRef.current)setLeaving(true);},2200);
    const max=setTimeout(()=>setLeaving(true),4500);
    return()=>{clearTimeout(timer);clearTimeout(max);};
  },[]);
  useEffect(()=>{if(visible)dialog.current?.showModal();},[visible]);
  useEffect(()=>{if(ready&&elapsed.current)setLeaving(true);},[ready]);
  useEffect(()=>{if(!leaving)return;const timer=setTimeout(()=>{try{sessionStorage.setItem('orbit-welcome-v2','seen');}catch{}dialog.current?.close();setVisible(false);finishRef.current();},550);return()=>clearTimeout(timer);},[leaving]);
  if(!visible)return null;
  return <dialog ref={dialog} className={`ot-welcome ${leaving?'leaving':''}`} aria-label="Welcome to ORBIT-TRUST" onCancel={e=>{e.preventDefault();setLeaving(true);}}>
    <div className="ot-welcome-top"><span>ORBIT—TRUST</span><span>EARTH / SOL SYSTEM</span></div>
    <div className="ot-welcome-core" aria-hidden="true"><span/><span/><span/><i/></div>
    <div className="ot-welcome-copy"><p>ESTABLISHING PERSPECTIVE</p><h2>Space to<br/><em>understand.</em></h2><span>{ready?'Earth is ready. Your perspective starts here.':'Preparing your view of Earth.'}</span></div>
    <div className="ot-welcome-bottom"><span>01 — ARRIVAL</span><button onClick={()=>setLeaving(true)} autoFocus>Skip introduction ↗</button></div>
  </dialog>;
}
