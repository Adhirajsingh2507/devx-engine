import type {ReactNode} from 'react';
import {WorkspaceShell} from '../../src/components/workspace-shell';
export default function AppLayout({children}:{children:ReactNode}){return <WorkspaceShell>{children}</WorkspaceShell>;}
