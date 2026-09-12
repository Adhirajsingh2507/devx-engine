'use client';
import Link from 'next/link';
import {useEffect} from 'react';
import {EarthViewport} from './earth-viewport';
import './workspace.css';

export function LandingPage(){
  useEffect(()=>{const old:Record<string,string>={'#mission':'overview','#agent-architecture':'agents','#activity':'activity','#satellite-directory':'satellites'};if(old[location.hash])location.replace(`/app/${old[location.hash]}/`);},[]);
  return <main className="wa-landing"><section className="wa-landing-hero" aria-labelledby="brand-title"><EarthViewport playing/><header><Link href="/" className="wa-brand"><span className="wa-brand-mark"><i/></span>ORBIT<span>TRUST</span></Link><Link className="wa-landing-enter" href="/app/overview/">Enter app ↗</Link></header><div className="wa-brand-reveal"><p>SPACE SITUATIONAL AWARENESS</p><h1 id="brand-title">ORBIT<span>—</span>TRUST</h1><p>Clarity before the next move.</p></div><footer><span>EARTH / SOL SYSTEM</span><a href="#introduction">Discover the workspace ↓</a><span>01 / INTRODUCTION</span></footer></section><section id="introduction" className="wa-landing-intro"><span className="wa-red-rule"/><p className="wa-eyebrow">THE MISSION WORKSPACE</p><h2>Every warning deserves<br/>a clear next step.</h2><p>Review conjunction evidence, explore your spacecraft, and understand financial exposure in one focused workspace. Open a tool, inspect the inputs, and decide what needs attention.</p><Link className="wa-enter-button" href="/app/overview/">Enter app <span>↗</span></Link><small>Interactive demonstration · no live telemetry</small><footer><span>ORBIT-TRUST</span><Link href="/app/methods/">Methods & limits ↗</Link><a href="https://science.nasa.gov/resource/earth-3d-model/" target="_blank" rel="noreferrer">Earth model · NASA / VTAD ↗</a></footer></section></main>;
}
