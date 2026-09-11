# ADK orchestration and output validation

## Purpose and model choice

The agent's useful task is bounded investigation: decide which available evidence history or declared scenario needs inspection and organize a review packet. Numeric integration, deadline arithmetic, financial math, authorization and policy remain deterministic. Do not generate decorative agent traces from a scripted animation.

Use Google ADK Python with its LiteLLM connector and Groq model ID `groq/openai/gpt-oss-20b`. The raw Groq model ID is `openai/gpt-oss-20b`; the first groq/ prefix belongs to LiteLLM routing. The server reads GROQ_API_KEY from its secret environment. Verify the model in the owner's account and run a real tool-call/schema spike before locking the provider adapter. The earlier Finora Llama default is not assumed available to a new free account. [^09-S07][^09-S08][^09-S09][^09-S10]

Groq is selected for remote inference without the team's own GPU and documented function/schema capabilities; local latency and account quotas still need measurement. Current Groq documentation lists tool use and strict structured output for the selected model, with those features used in separate calls. The selected model does not require parallel model tool calls: deterministic batch execution provides the numerical parallelism. No built-in web search, code execution, remote MCP or provider-managed actions are enabled. [^09-S08][^09-S09][^09-S10]

The supplied ADK lecture is the component reference, not a mandate to use every component. Use LlmAgent, FunctionTool/custom deterministic tools, SequentialAgent or a small custom BaseAgent workflow, typed output, callbacks and versioned state. No A2A, general long-term memory or multimodal model is needed. Its warning about mixing tools and schema is addressed by separate stages. The supplied deck and a text extraction are included under reference/.

## Roles and orchestration

The overall CaseReviewWorkflow is deterministic. It verifies the assessment snapshot and executes the required calculations before invoking any LLM. Domain roles EvidenceAudit, FleetComparison, ConsequenceAnalysis and ReentryExposure are explicit deterministic services/tools. Only Investigator and PacketFormatter invoke the model. This is a multi-role system, not six independent language models.

Investigator receives a compact record of the current assessment, source identifiers and available scenario IDs. It may call at most three allowlisted tools in total: inspect_event_history, inspect_evidence_finding, evaluate_allowed_scenario or read_candidate_comparison. Tool arguments are only existing IDs, never a new orbit, probability, cost or arbitrary URL. Bound each result to 4 KiB of selected fields; full artifacts remain in the ledger.

Use at most two tool-response rounds followed by one formatter request. Maximum normal provider requests: three, plus one retry shared across the entire run, never a retry per agent/tool. If no further tool is appropriate, proceed directly to formatting. Budget at most 1,200 input tokens per provider request and 400 output tokens per call, with an overall 6,000-token reservation including retry. Log actual token use and release unused reservation. These are application defaults to adjust downward for the actual account, not Groq entitlements.

Apply a 30-second total agent wall-time budget including tools and any retry. Each provider request has a timeout of at most 8 seconds or the remaining budget, whichever is smaller. Before dispatch, reserve enough remaining time for host validation and persistence. A fourth call is permitted only if both token and time budgets still allow it. Long scenario computation should already exist as a saved bounded operation; an agent tool must not bypass the numerical chunk limits.

The formatter has no tools. It returns a typed selection: assessment_id, ordered_finding_ids, selected_fact_ids, summary_template_code, request_template_code or null, and question_to_analyst_code or null. All fields are required; nullable values are explicit; additionalProperties=false. Use ADK output_schema if the verified connector forwards the needed schema reliably. If that spike fails, call Groq's strict-schema formatter within an ADK custom stage and validate with the same Pydantic model. Do not silently remove schema validation or report a mocked provider response as live.

## Authoritative text assembly

The initial release accepted packet is rendered by the host from validated template codes and fact records. The model chooses evidence order and permitted templates; it does not write arbitrary factual sentences into the authoritative packet. This closes the gap left by merely checking digits in free text. Numeric facts, next action and urgency are always host-owned.

Allowed summary templates include REVIEW_DUE_TO_RISK, REVIEW_DUE_TO_MISSING_EVIDENCE, REVIEW_DUE_TO_CONFLICT, MONITOR_SUPPORTED and CALCULATION_UNSUPPORTED. Allowed request templates include REQUEST_STATE_COVARIANCE, REQUEST_FRAME_EPOCH, REQUEST_MANEUVER_CONTEXT and REQUEST_DEADLINE. Their availability is computed from findings. A template cannot be selected if its prerequisite finding is absent.

An example accepted packet says: “Review is required because the applicable reports support different classifications. The current review deadline is {deadline_fact}. Request an updated {missing_field_names} with source and epoch before {request_deadline_fact}.” Placeholders come from host records. If a fact is unavailable, select the corresponding missing-data template rather than inventing a value.

An optional free-text “AI wording draft” is outside initial release. Do not add it as a shortcut around these requirements. The product still demonstrates agentic choice through different allowed investigation sequences and evidence selection; evaluate whether that choice is useful against fixed routing.

## Guardrails and failure handling

Before any tool call, verify run/workspace identity, expected input digest, allowed tool name, schema, argument IDs and remaining budget. Report comments, names and imported notes are untrusted text. They cannot change tool policy, trigger network calls or become system instructions. Mask contact information from model inputs by default; public data is synthetic.

After each tool result, verify provenance and status. Before publishing, ensure every cited finding/fact exists in the same snapshot, selected templates match facts, and no required finding is omitted. The deterministic required-finding list is included even if the model fails to select it. A schema-valid but wrong selection is rejected. New source data marks the run stale, and its packet is not displayed as current.

On malformed response, forbidden tool, invalid reference, provider 429, timeout or missing key, return the deterministic packet with generation_mode=template_fallback and a plain explanation. Retry only if it fits the single retry and remaining time/token budget. Respect Retry-After; if waiting would exceed budget, stop. Never switch to a paid provider or claim the fallback is Groq output.

## Quotas and observability

Account limits are shared across organization requests and tokens; inspect actual values rather than copying a fixed public table. Maintain atomic database reservations for the chosen model and account. Default global active model runs=1, one concurrent run per user, three investigate runs/minute/user, ten runs/day/anonymous user and fifty runs/day/persistent user. Provider request counts are separately bounded within each run. Global spend remains disabled. Administrator limits cannot exceed the verified provider allowance. Seed-page views and ordinary calculations make no model calls. [^09-S09]

Record model ID, provider, prompt version, accepted tool names/arguments, source record IDs, stage durations, tokens, retry cause and validation outcome. Do not store hidden chain-of-thought, API keys or full provider headers. Show “what ran and what it returned,” not claims about the model's internal thoughts.

Dependency note: official ADK documentation identifies LiteLLM 1.82.7 and 1.82.8 as compromised. Exclude these releases, choose a currently patched compatible version and lock it in M0. This is a dependency-selection requirement for the build, not evidence that this workspace has installed those versions. [^09-S07]

## Source notes

[^09-S07]: Google ADK, [LiteLLM integration](https://adk.dev/agents/models/litellm/).

[^09-S08]: Groq, [Supported models](https://console.groq.com/docs/models).

[^09-S09]: Groq, [Rate limits](https://console.groq.com/docs/rate-limits).

[^09-S10]: Groq, [Tool use](https://console.groq.com/docs/tool-use/overview) and [Structured outputs](https://console.groq.com/docs/structured-outputs).
