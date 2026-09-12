import { Vec3 } from '@engine/math';

export type BranchId = 'evidence' | 'collision' | 'terrain' | 'finance' | 'judge';
export interface Specialist { name: string; input: string; output: string }
export interface AgentBranch { id: BranchId; name: string; code: string; purpose: string; specialists: Specialist[] }

export const agentBranches: AgentBranch[] = [
  { id:'evidence',name:'Evidence audit',code:'01',purpose:'Establish what can be trusted before using an assessment.',specialists:[
    {name:'Schema & units',input:'Supplied state vectors and metadata',output:'Frame, epoch and unit validation'},
    {name:'Covariance auditor',input:'Covariance timestamp and policy',output:'Age check; uncertainty limitations'},
    {name:'Maneuver context',input:'Operator-provided maneuver records',output:'Missing-data requests and provenance'},
  ]},
  {id:'collision',name:'Collision analysis',code:'02',purpose:'Screen supplied encounters with deterministic geometry, then disclose model limits.',specialists:[
    {name:'Encounter geometry',input:'Relative position and velocity',output:'Linear closest approach via @engine/math Vec3'},
    {name:'Fleet pair screening',input:'Supplied candidate pairs',output:'Prioritized separation checks'},
    {name:'Uncertainty review',input:'Covariance and object dimensions',output:'Withhold collision probability when inputs are absent'},
    {name:'Response comparison',input:'Operator-supplied maneuver candidates',output:'Candidate comparison; never a flight command'},
  ]},
  {id:'terrain',name:'Terrain analysis',code:'03',purpose:'A separate consequence branch, only when a reentry footprint is supplied.',specialists:[
    {name:'Footprint gate',input:'Reentry footprint, epoch and provenance',output:'Run or withhold terrain assessment'},
    {name:'Terrain classifier',input:'Elevation, water and land-cover layers',output:'Terrain intersection summary'},
    {name:'Exposure estimator',input:'Population and asset overlays',output:'Scenario exposure ranges, not a crash destination'},
  ]},
  {id:'finance',name:'Financial analysis',code:'04',purpose:'Adapt the personal-CFO pattern to explicit satellite loss and response assumptions.',specialists:[
    {name:'Asset valuation',input:'Replacement cost and coverage assumptions',output:'Capital exposure range'},
    {name:'Service interruption',input:'Downtime days × daily revenue',output:'Scenario revenue loss'},
    {name:'Response budget',input:'Fuel, operations and recovery costs',output:'Supplied response-cost comparison'},
    {name:'Insurance review',input:'Policy limits and deductibles',output:'Net exposure only when coverage is supplied'},
    {name:'Consequence aggregation',input:'Terrain exposure + asset assumptions',output:'Conditional loss; no claim of money actually saved'},
  ]},
  {id:'judge',name:'Judge & synthesis',code:'05',purpose:'Check evidence, reconcile findings and return control to a human analyst.',specialists:[
    {name:'Numeric verifier',input:'Deterministic calculation outputs',output:'Finite values, unit checks and policy comparison'},
    {name:'Evidence guardrails',input:'Missing data and model applicability',output:'Block unsupported conclusions'},
    {name:'Brief composer',input:'Validated findings and source identifiers',output:'Evidence summary with explicit limitations'},
    {name:'Human approval',input:'Review package',output:'Await analyst decision; no autonomous command'},
  ]},
];

export type ScenarioId = 'review' | 'monitor';
export const scenarioInputs = {
  review:{label:'Close approach',r:[-12,0.12,0] as const,v:[0.04,0,0] as const,covarianceAge:19,replacement:18000000,dailyRevenue:24000,downtime:14,responseCost:85000},
  monitor:{label:'Wider separation',r:[-12,2.4,0] as const,v:[0.04,0,0] as const,covarianceAge:4,replacement:18000000,dailyRevenue:24000,downtime:2,responseCost:85000},
};

/** Short-horizon, constant relative velocity illustration, not an orbit propagator. */
export function closestApproach(position:Vec3,velocity:Vec3,horizon=600) {
  if(![position.x,position.y,position.z,velocity.x,velocity.y,velocity.z,horizon].every(Number.isFinite)||horizon<0)throw new Error('Finite states and a nonnegative horizon are required.');
  const speed2=velocity.lengthSq();
  const seconds=speed2===0?0:Math.max(0,Math.min(horizon,-position.dot(velocity)/speed2));
  return {seconds,distanceKm:position.add(velocity.scale(seconds)).length()};
}
export function evaluateScenario(id:ScenarioId) {
  const input=scenarioInputs[id];
  const approach=closestApproach(new Vec3(...input.r),new Vec3(...input.v));
  const thresholdKm=.5, review=approach.distanceKm<thresholdKm;
  const serviceLoss=input.dailyRevenue*input.downtime;
  return {input,...approach,thresholdKm,review,stale:input.covarianceAge>12,serviceLoss,conditionalLoss:input.replacement+serviceLoss,
    findings:{
      evidence:`Covariance age ${input.covarianceAge}h / 12h policy. ${input.covarianceAge>12?'Refresh required.':'Age check passed.'} Maneuver context not supplied.`,
      collision:`Linear miss distance ${(approach.distanceKm*1000).toFixed(0)} m at T+${approach.seconds.toFixed(0)} s. ${review?'Below':'Above'} 500 m demo review threshold. Probability withheld: no covariance matrix.`,
      terrain:'Withheld. No reentry footprint or geospatial exposure layers supplied. Orbital conjunction does not imply immediate reentry.',
      finance:`Conditional asset + service loss: $${(input.replacement+serviceLoss).toLocaleString('en-US')}. Not expected loss or realized savings. Insurance and ground exposure excluded.`,
      judge:`${review?'Analyst review required':'Continue evidence review'}. No autonomous maneuver. Terrain and collision-probability claims blocked by missing inputs.`,
    } satisfies Record<BranchId,string>};
}

export interface WorkflowEvent { id:string; index:number; branch:BranchId|'router'; title:string; detail:string; state:'complete'|'attention'|'withheld'; }
export function buildWorkflow(id:ScenarioId):WorkflowEvent[] {
  const result=evaluateScenario(id);
  return [
    {id:`${id}-router`,index:0,branch:'router',title:'Scenario routed',detail:`Synthetic ${result.input.label.toLowerCase()} fixture loaded. Calculations run locally; no LLM service called.`,state:'complete'},
    ...agentBranches.map((branch,i)=>({id:`${id}-${branch.id}`,index:i+1,branch:branch.id,title:branch.name,detail:result.findings[branch.id],state:(branch.id==='terrain'?'withheld':branch.id==='judge'||branch.id==='evidence'&&result.stale||branch.id==='collision'&&result.review?'attention':'complete') as WorkflowEvent['state']})),
  ];
}
