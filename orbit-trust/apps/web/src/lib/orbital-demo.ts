import { Vec3 } from '@engine/math';

export interface DemoSatellite {
  id: string; name: string; mission: string; operator: string; altitude: number;
  inclination: number; ascending: number; phase: number; review: boolean; note: string;
}

/** Fictional fixtures. This experience is not a live orbit or conjunction feed. */
export const orbitalDemo: DemoSatellite[] = [
  { id:'OT-001',name:'ASTERIA-3',mission:'Earth observation',operator:'Asteria Operations',altitude:550,inclination:53,ascending:0.2,phase:0.9,review:true,note:'A supplied conjunction case needs analyst review. No maneuver recommendation has been issued.' },
  { id:'OT-002',name:'ASTERIA-7',mission:'Earth observation',operator:'Asteria Operations',altitude:580,inclination:53,ascending:0.2,phase:3.8,review:false,note:'No review flag in this fictional fixture. This is not a safety determination.' },
  { id:'OT-003',name:'HORIZON-1',mission:'Climate research',operator:'Horizon Science',altitude:705,inclination:98,ascending:1.1,phase:2.0,review:false,note:'Demonstration climate mission on an illustrative polar orbit.' },
  { id:'OT-004',name:'HORIZON-2',mission:'Ocean monitoring',operator:'Horizon Science',altitude:720,inclination:98,ascending:1.1,phase:5.2,review:false,note:'Demonstration ocean monitoring mission. All values are scenario inputs.' },
  { id:'OT-005',name:'RELAY-04',mission:'Communications',operator:'Relay Network',altitude:1200,inclination:40,ascending:2.0,phase:1.4,review:false,note:'Illustrative communications spacecraft. No live telemetry is connected.' },
  { id:'OT-006',name:'RELAY-09',mission:'Communications',operator:'Relay Network',altitude:1200,inclination:40,ascending:2.0,phase:4.2,review:true,note:'Example evidence gap: the latest maneuver record has not been supplied.' },
  { id:'OT-007',name:'KESTREL-1',mission:'Technology demonstrator',operator:'Kestrel Labs',altitude:850,inclination:72,ascending:0.8,phase:0.3,review:false,note:'Fictional technology demonstrator for exploring the interface.' },
  { id:'OT-008',name:'KESTREL-2',mission:'Technology demonstrator',operator:'Kestrel Labs',altitude:870,inclination:72,ascending:0.8,phase:3.1,review:false,note:'Fictional companion mission. Orbital shells are expanded for legibility.' },
];
const MU = 398600.4418;
export const periodMinutes = (s: DemoSatellite) => 2*Math.PI*Math.sqrt((6371+s.altitude)**3/MU)/60;
export const speedKmS = (s: DemoSatellite) => Math.sqrt(MU/(6371+s.altitude));
export function satellitePoint(s:DemoSatellite, seconds:number, fixedAngle?:number) {
  const theta=fixedAngle ?? s.phase+seconds*240/(periodMinutes(s)*60)*2*Math.PI;
  // Display spacing is deliberately exaggerated; real km values remain in the UI.
  const radius=1.17+s.altitude/2400;
  const inc=s.inclination*Math.PI/180, x=radius*Math.cos(theta),y=radius*Math.sin(theta)*Math.sin(inc),z=radius*Math.sin(theta)*Math.cos(inc);
  return new Vec3(x*Math.cos(s.ascending)+z*Math.sin(s.ascending),y,-x*Math.sin(s.ascending)+z*Math.cos(s.ascending));
}
