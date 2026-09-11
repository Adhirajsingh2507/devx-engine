# ORBIT TRUST implementation handoff

Version 2.0, revision game-preservation-1. Prepared 11 September 2026. This revision records the owner's clarification that 3d-game is important for future implementation. This package is a specification and reference-data handoff, not an implemented application. It contains the context needed by an engineer or a new AI chat that has never seen the original conversation.

**Build outcome:** a public hackathon demonstration for satellite conjunction review, evidence auditing, fleet response comparison and financial scenarios, with a separate reentry exposure sandbox. Use Google ADK, Groq, a deterministic Rust calculation library and a simple mission console adapted from the owner's existing projects.

## How to use this package

1. Extract the complete ZIP. Give the new chat this folder, or upload `ORBIT_TRUST_COMPLETE_HANDOFF.md` if it accepts only one text file.
2. Paste `00_BOOTSTRAP_PROMPT.md` as your instruction. It explicitly tells the new chat to build, not merely describe the project.
3. The implementer reads documents 01 through 06 before coding, then follows the milestone sequence in document 13. Documents 07 through 19 resolve the specialist details.
4. Keep `schemas/`, `fixtures/` and `reference/` with the documents. These are specification inputs and expected-output examples, not application source code.
5. Put credentials in the deployment service's secret settings. Never paste keys into a chat or add them to this package.

The complete Markdown includes the numbered documents and machine-readable contract/fixture appendices. The PDF is the human-readable companion; exact machine contracts remain in the ZIP and complete Markdown. A manifest records file hashes so the recipient can detect an incomplete transfer.

## Decisions carried from the owner

- Preserve real mathematical and engineering depth, useful agent tools, a compelling demonstration and a believable business case.
- No team-size, build-time or experience questionnaire. Work is sequenced by dependencies rather than assumed staffing.
- No GPU or paid API credits. **Groq is the chosen AI provider.**
- **A public web demo is required.** A local backup does not replace this requirement.
- Visual direction: dark navigation, light work panels and restrained status colors.
- Lead with fleet review and response. Include terrain analysis as a separate reentry sandbox.
- Reuse the owner's TerraSight, Finora and Sajawat projects selectively. Do not merge their applications wholesale.
- The existing `3d-game/` app in devx-engine is an important future implementation asset. Preserve its source, assets, configuration, history and any existing deployment. Do not delete, overwrite or repurpose it while building ORBIT-TRUST in `orbit-trust/`.
- Do not promise zero hallucinations, certain collisions, optimal real maneuvers, exact crash sites, actual money saved or operational flight readiness.

## Authority and versioning

The owner's latest instructions outrank this package. Within version 2.0, document 02 records decisions; document 05 and `schemas/core.schema.json` define contracts; document 06 defines scientific rules; documents 12 and 17 define acceptance. If these disagree, record the conflict and fix the documentation before changing behavior. Do not silently choose the easiest interpretation.

This package supersedes the earlier 30-page playbook where scope differs. In particular, Groq and a public web release replace local-model-first deployment; supplied fleet candidates and a separate reentry sandbox are now included. Earlier research remains context, not an alternative implementation specification.

All performance targets, prices, mission policy thresholds and fictional scenarios are proposals unless explicitly identified as observations. No ORBIT-TRUST application, live Groq integration, public deployment or operator validation has been completed by preparing this package.

## Deliverables the next implementer must produce

An ORBIT-TRUST application under `orbit-trust/` in the existing `Adhirajsingh2507/devx-engine` repository, working Vercel public URL, persistent Supabase accounts and case data, local reproducible run, meaningful tests, measured benchmark report, dependency lockfiles, data/source notices, a three-minute demo recording, and a release report distinguishing completed work from blocked items. Preserve the important future `3d-game/` app, existing toolkit content and the three source repositories. Future game development or integration is a separate task requiring the owner's direction.

The owner reports that devx-engine is already connected to Vercel for automatic deployment. Confirm the existing project's Root Directory and build settings before publishing. Groq and Supabase secret values and account login remain owner-supplied deployment inputs. Their absence must not block independent implementation or local verification.
