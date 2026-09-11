# Multi-Agent Personal CFO — Architecture

> Gemma 4 12B-IT driving a custom 7-agent orchestrator with native function
> calling, a deterministic Python finance engine, a Judge (Reflection) loop,
> exposed via a FastAPI backend that serves a single-page web app.

---

## 1. System overview

```mermaid
flowchart TB
    subgraph UI["Frontend — SPA (web/)"]
        CHAT["AI Advisor: Ask your CFO"]
        DASH["Dashboard sections<br/>CIBIL · Budget · Bills · Loans · Investments"]
        PANEL["Live panel<br/>Agent trace · Judge status · Confidence · Risk badge"]
    end

    subgraph API["Backend — FastAPI"]
        ADV["POST /advise"]
        DBD["GET /dashboard"]
        HLT["GET /health"]
    end

    SVC["service.py<br/>(shared singleton — one loaded model)"]

    subgraph CORE["Agentic core"]
        ORCH["Finance Orchestrator<br/>Plan → ReAct → Reflection"]
        JUDGE["Judge Agent<br/>rule-based Reflection"]
    end

    subgraph AGENTS["7 specialist agents (Gemma tools)"]
        A1["Budget"]:::a
        A2["Bills"]:::a
        A3["Loan"]:::a
        A4["Fraud"]:::a
        A5["Affordability"]:::a
        A6["Investment"]:::a
        A7["Tax"]:::a
    end

    ENG["finance_engine.py<br/>DETERMINISTIC math — no LLM"]
    DATA["mock_data.py<br/>profile · txns · bills · investments · fraud intel"]
    LLM["llm.py — Gemma 4 client<br/>transformers · 4-bit · tool-call parser"]
    GEMMA["Gemma 4 12B-IT<br/>Kaggle T4 x2"]

    CHAT --> SVC
    DASH --> SVC
    ADV --> SVC
    DBD --> SVC
    HLT --> SVC
    SVC --> ORCH
    ORCH <--> JUDGE
    ORCH -->|function calls| AGENTS
    AGENTS --> ENG
    ENG --> DATA
    ORCH -->|prompts| LLM
    JUDGE -.optional phrasing.-> LLM
    LLM --> GEMMA
    ORCH -->|trace + verdict| PANEL

    classDef a fill:#eef2ff,stroke:#6366f1;
```

---

## 2. Request flow — one query end to end

```mermaid
sequenceDiagram
    actor User
    participant UI as Web SPA / FastAPI
    participant ORCH as Orchestrator
    participant GEMMA as Gemma 4 12B
    participant AGENTS as Agents
    participant ENG as finance_engine
    participant JUDGE as Judge

    User->>UI: "Can I afford an iPhone for Rs.90,000?"
    UI->>ORCH: advise(query)

    rect rgb(238,242,255)
    note over ORCH,GEMMA: PLAN / ACT (ReAct)
    ORCH->>GEMMA: query + 7 tool schemas (enable_thinking)
    GEMMA-->>ORCH: tool_calls[check_affordability, evaluate_loan, ...]
    end

    loop each selected agent
        ORCH->>AGENTS: run_agent(name, args)
        AGENTS->>ENG: deterministic math
        ENG-->>AGENTS: numbers
        AGENTS-->>ORCH: finding + summary
    end

    rect rgb(255,244,229)
    note over ORCH,JUDGE: REFLECT (bounded <= 2)
    ORCH->>JUDGE: evaluate(findings)
    JUDGE-->>ORCH: response_ok · transaction_safe · risk · advisories
    alt revision_suggested and iterations remain
        ORCH->>GEMMA: re-plan with advisories fed back
    end
    end

    rect rgb(236,253,245)
    note over ORCH,GEMMA: SYNTHESISE
    ORCH->>GEMMA: write explainable answer from findings
    GEMMA-->>ORCH: prose (scrubbed of control tokens)
    end

    ORCH-->>UI: {answer, confidence, trace[], judge_verdict}
    UI-->>User: recommendation + live agent trace
```

---

## 3. The Judge — split verdict (Reflection)

```mermaid
flowchart TD
    F["Agent findings"] --> J{Judge evaluate}

    J --> R1{"Loan EMI ><br/>40% income?"}
    J --> R2{"Purchase breaks<br/>emergency fund?"}
    J --> R3{"Fraud risk<br/>HIGH / CRITICAL?"}
    J --> R4{"Any agent<br/>actually ran?"}

    R1 -->|yes| ADV["advisories += EMI flag"]
    R2 -->|yes| ADV2["advisories += EF flag"]
    R3 -->|yes| ADV3["advisories += fraud flag"]
    R4 -->|no| INC["inconsistencies += no findings"]

    ADV --> OUT
    ADV2 --> OUT
    ADV3 --> OUT
    INC --> OUT

    OUT["Verdict"]
    OUT --> V1["response_ok = findings valid<br/>(answer quality badge)"]
    OUT --> V2["transaction_safe = no advisories<br/>(purchase safety)"]
    OUT --> V3["risk_level = safe / caution / high"]
    OUT --> V4["confidence = coverage-based"]
    OUT --> V5["revision_suggested -> loop back"]

    style V1 fill:#ecfdf5,stroke:#16a34a
    style V2 fill:#fff7ed,stroke:#d97706
```

> **Key design point:** `response_ok` (is the answer good) is separate from
> `transaction_safe` (is the purchase safe). A correct "do NOT pay this scam"
> reply is `response_ok = True` **and** `transaction_safe = False`.

---

## 4. Layers & responsibilities

```mermaid
flowchart LR
    subgraph L1["Presentation"]
        direction TB
        G["Web SPA (web/)"]
        RF["FastAPI REST"]
    end
    subgraph L2["Service"]
        S["service.py<br/>singleton · swappable backend"]
    end
    subgraph L3["Reasoning"]
        O["Orchestrator"]
        JU["Judge"]
    end
    subgraph L4["Skills"]
        AG["7 agents (tools)"]
    end
    subgraph L5["Computation"]
        FE["finance_engine<br/>deterministic"]
    end
    subgraph L6["Data"]
        MD["mock_data<br/>(AA / Plaid-ready)"]
    end
    subgraph L7["Model"]
        LB["llm.py"]
        GM["Gemma 4 12B-IT"]
    end

    L1 --> L2 --> L3 --> L4 --> L5 --> L6
    L3 --> L7
```

| Layer | Module(s) | Rule |
|---|---|---|
| Presentation | `web/`, `api.py` | Render only — never compute |
| Service | `service.py` | One model instance; backend swap via `GEMMA_BACKEND` |
| Reasoning | `orchestrator.py`, `judge.py` | LLM plans/explains; Judge validates with rules |
| Skills | `agents.py` | Thin tools; decide *what*, not *the numbers* |
| Computation | `finance_engine.py` | All math; **no LLM arithmetic** |
| Data | `mock_data.py` | Mock now; real connectors are the interface's future work |
| Model | `llm.py` + Gemma 4 | Swappable client; 4-bit → fp16 fallback |

---

## 5. Model loading strategy (Kaggle T4 x2)

```mermaid
flowchart TD
    START["_ensure_loaded()"] --> RESET["clear CUDA cache<br/>(drop leaked residue)"]
    RESET --> CHK{"bitsandbytes<br/>healthy?"}
    CHK -->|yes| Q4["4-bit NF4<br/>~7GB · device_map=auto · max_memory"]
    CHK -->|no| FP["fp16 sharded 12/12<br/>across BOTH T4s (~24GB)"]
    Q4 --> OK{"load ok?"}
    OK -->|yes| DONE["load_mode = 4bit"]
    OK -->|no| FP
    FP --> DONE2["load_mode = fp16"]

    DONE --> NOTE["same -it checkpoint<br/>NEVER the base model"]
    DONE2 --> NOTE

    style Q4 fill:#eef2ff,stroke:#6366f1
    style FP fill:#fff7ed,stroke:#d97706
```

---

## 6. Design patterns → paper mapping

Grounded in *Agentic AI in Finance: A Comprehensive Overview* (Luqman et al.):

| Paper concept (§) | This system |
|---|---|
| Reflection (§4.1) | Judge Agent loop |
| Tool Use + Computation (§4.1 / §4.3) | Agents → deterministic `finance_engine` |
| Planning (§4.1) | Orchestrator selecting agents |
| Multi-Agent Collaboration (§4.1) | The whole system |
| Reasoning · Memory · Tools (§4.2) | Gemma 4 · conversation context · agent tools |
| ReAct (§4.1) | Orchestrator's plan→act loop |
| Risk: incorrect transactions (§5.2) | Deterministic math + Judge validation |
