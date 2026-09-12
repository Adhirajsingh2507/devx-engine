'use client';

import { useEffect } from 'react';

/** Preserve existing bookmarks with the static-export deployment. */
export function LandingDestination({section,label}:{section:string;label:string}) {
  const destinations:Record<string,string>={mission:'overview','agent-architecture':'agents','satellite-directory':'satellites'};
  const href=`/app/${destinations[section]??section}/`;
  useEffect(()=>{window.location.replace(href);},[href]);
  return <main style={{padding:'4rem',fontFamily:'sans-serif'}}><h1>{label}</h1><p>Opening the mission workspace.</p><a href={href}>Open {label.toLowerCase()} →</a></main>;
}
