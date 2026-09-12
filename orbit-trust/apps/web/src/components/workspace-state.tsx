'use client';

import {createContext,useContext,useState,type ReactNode} from 'react';
import {buildWorkflow,type ScenarioId,type WorkflowEvent} from '../lib/mission-workflow';

import {defaultFinance,type FinanceInputs} from '../lib/finance-scenario';
export {defaultFinance,financeTotals,type FinanceInputs} from '../lib/finance-scenario';
function useWorkspaceStore(){
  const [scenario,setScenario]=useState<ScenarioId>('review');
  const [trace,setTrace]=useState<WorkflowEvent[]>([]);
  const [runScenario,setRunScenario]=useState<ScenarioId|null>(null);
  const [runAt,setRunAt]=useState<string|null>(null);
  const [selectedSat,setSelectedSat]=useState('OT-001');
  const [caseId,setCaseId]=useState('OT-0911-014');
  const [notes,setNotes]=useState<Record<string,string>>({});
  const [finance,setFinance]=useState<FinanceInputs>(defaultFinance);
  const [financeResult,setFinanceResult]=useState<FinanceInputs|null>(null);
  const [acknowledged,setAcknowledged]=useState(false);
  const run=()=>{setTrace(buildWorkflow(scenario));setRunScenario(scenario);setRunAt(new Date().toISOString());setAcknowledged(false);};
  return {scenario,setScenario,trace,runScenario,runAt,run,selectedSat,setSelectedSat,caseId,setCaseId,notes,setNotes,finance,setFinance,financeResult,setFinanceResult,acknowledged,setAcknowledged};
}
const WorkspaceContext=createContext<ReturnType<typeof useWorkspaceStore>|null>(null);
export function WorkspaceProvider({children}:{children:ReactNode}){const value=useWorkspaceStore();return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;}
export function useWorkspace(){const value=useContext(WorkspaceContext);if(!value)throw new Error('WorkspaceProvider is required.');return value;}

export function downloadJson(name:string,value:unknown){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
