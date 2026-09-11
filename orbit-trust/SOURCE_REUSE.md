# Source reuse register (doc 03)

Records every component adapted from the owner's prior repositories: source URL,
pinned commit, original path, reused behavior, changed behavior, validation. No
component copied yet — this session scaffolds only original ORBIT-TRUST code.

Do not import unrelated automation, secrets, business logic or agent permissions
from these repos. Prefer newly drawn UI + fictional fixtures over copied media.

| Component | Source repo | Pinned commit | Original path | Reused behavior | Changed behavior | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| _(pending M4)_ | terrasight | 2e6445f0 | backend/app/terrain, scoring; frontend terrain-grid/site-table/stats-panel | measurement-vs-decision separation, spatial presentation | replace safety score with footprint/exposure model; drop `_walk_border` polygon assembler | — |
| _(pending M2/M5)_ | Error-404-Not-Found (Finora) | c66824b8 | formatting.py, agents.py, orchestrator.py, judge.py, finance_engine.py | deterministic specialists, provenance, small tool set, bounded loop, trace | replace finance formulas + fixed date + finding-count "confidence"; use doc-09 validator | — |
| _(pending M6)_ | sajawat | 600cf553 | apps/admin CRM page/[id], features/crm/stages, console/ui, Sidebar, Can | permission-aware detail, notes/assignment/stage UI | server-authoritative queue (not 100-row client board); 6 review stages; fixed routes w/ query IDs | — |
