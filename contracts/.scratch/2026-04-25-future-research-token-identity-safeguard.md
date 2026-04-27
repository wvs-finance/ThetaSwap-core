# Future-Research Safeguard — Token-Identity Triangulation for Mento-Native Scope

**Date:** 2026-04-26.
**Authoring lineage:** Task 11.P.MR-β.1 sub-task 5 dispatch (Technical Writer agent) under Rev-5.3.5 β-rescoped MR-β.1 sub-plan §C sub-task 5 + §I sub-task 5 strengthening.
**Status:** Editorial-only; no sub-task-level review per sub-plan §C-5.
**Body length declaration:** ≤100 lines of markdown body, falsifiable via `wc -l` per TW A4 advisory.
**Purpose:** Process-discipline memo. The registry spec doc §9 carries the registry-internal warning; this memo carries the process detail and is referenceable by future agent dispatch envelopes.

---

## Episode summary

The Mento-native Colombia token attribution flipped twice across Rev-5.3.3 → Rev-5.3.4 → Rev-5.3.5 before converging on the empirically verified address. Two distinct inversion layers were introduced from third-party / forum-style sources and corrected only after explicit user intervention plus on-chain triangulation:

- **Layer 1 — Rev-5.3.3 ticker-level inversion (corrected 2026-04-25).** The Trend Researcher's Finding 3 attributed the Mento-native Colombia token to *cCOP* and the address `0xc92e8fc2947e32f2b574cca9f2f12097a71d5606` to *cCOP* (with COPM cast as Minteo-fintech). The user corrected mid-Rev-5.3.3: *"is COPM not cCOP."* Pre-existing project memory `project_mento_canonical_naming_2026` (COPM as canonical Mento-native ticker) was correct on the ticker layer; the agent's brief Rev-5.3.3 attribution flip was wrong.
- **Layer 2 — Rev-5.3.4 address-level inversion (corrected 2026-04-26).** After Layer 1 was corrected, Rev-5.3.4 carried forward the assumption that `0xc92e8fc2…` *is* the Mento-native COPM address. Empirical disambiguation under Rev-5.3.5 (sub-task 1 inventory + Dune `searchTablesByContractAddress` + Mento V3 deployment docs + Celo Token List, all triangulated under MR-β.1) corrected this: the Mento-native Colombian-peso address is `0x8A567e2aE79CA692Bd748aB832081C45de4041eA` (canonical Mento V2 `StableTokenCOP`, lowercase ticker COPm); `0xc92e8fc2…` is Minteo-fintech "COP Minteo", OUT of Mento-native scope.

The disposition memo at `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md` is the authoritative trail for the Rev-5.3.5 β-disposition; the registry spec doc and the TR research file corrigendum are the durable artifacts that override Finding 3 going forward.

## Lesson

Third-party sources are NOT authoritative for on-chain identity at any grain. Both inversions originated from forum-style / blog-style / community-reported sources (Layer 1 in the TR's literature survey; Layer 2 in the rescoped framing's address claim). Both inversions persisted across multiple plan-rev cycles until on-chain inspection + project-memory cross-check fired. The lesson generalizes:

- Ticker-level attribution from third parties can invert (project A is cCOP / project B is COPM, when the on-chain truth is the opposite).
- Address-level attribution from third parties can invert (the address you think is project A is actually project B's contract).
- Project-name-level attribution from third parties can invert (the entity issuing a token may be misreported entirely).

On-chain inspection (Mento Labs deployment docs + Dune decoded-table catalog + protocol-specific event presence) plus project-memory cross-check is the authoritative path. Project memory `project_mento_canonical_naming_2026` β-corrigendum block (file top) is the project's authoritative ticker-to-address mapping post-Rev-5.3.5; the SUPERSEDED original-content section below it is preserved for audit trail only.

## Process rule — mandatory triangulation procedure

Future Trend Researcher / Reality Checker / any subagent dispatch that encounters token-identity attribution from third-party sources MUST cross-check via the following four-source triangulation, in this order of authority:

1. **Authority 1 (highest) — Mento Labs official deployment docs** at `https://docs.mento.org/mento-v3/build/deployments/addresses.md` (working URL; the prior `https://docs.mento.org/mento/protocol/deployments` URL 404s and is superseded). The `StableTokenCOP` and other `StableToken*` contract addresses are authoritative here. When this source disagrees with Authorities 2-4, this source wins.
2. **Authority 2 — Dune decoded-table catalog** via `mcp__dune__searchTablesByContractAddress`. Project-name and contract-name in the decoded-table catalog is authoritative on which contract is decoded as a Mento `StableTokenV2` versus another contract type. **Mento-protocol-specific governance events on a contract address are dispositive of Mento-protocol-native status:** `evt_exchangeupdated`, `evt_validatorsupdated`, `evt_brokerupdated`, `evt_initialized` presence confirms the contract is Mento-protocol-native; absence of all four is strong evidence the contract is NOT Mento-protocol-native (e.g., Minteo-fintech).
3. **Authority 3 — Celo Token List** at `https://raw.githubusercontent.com/celo-org/celo-token-list/main/celo.tokenlist.json` (chainId 42220 entries). Useful disambiguation evidence (e.g., distinguishing "COP Minteo" from "Mento Colombian Peso" by `name` and `symbol` fields), but NOT authoritative when Authorities 1 and 2 disagree.
4. **Authority 4 — Project memory cross-check** against `project_mento_canonical_naming_2026` β-corrigendum block (NOT the SUPERSEDED original-content section); the β-corrigendum block at the file top is the project's authoritative ticker-to-address mapping post-Rev-5.3.5. Companion memory `project_abrigo_mento_native_only` β-corrigendum extension carries the scope discipline.

If Authorities 1 and 2 agree, the attribution is established. If Authorities 1 and 2 disagree, HALT to user with the discrepancy surfaced; never silently pick one and proceed.

## Process rule — anti-fishing

Failure to cross-check against the registry before propagating a token-identity claim into specs / plans / code / project memory is an anti-fishing-banned shortcut per `feedback_pathological_halt_anti_fishing_checkpoint`. It surfaces as a process violation. The corrective protocol when a discrepancy is encountered:

- **HALT to user** with a brief discrepancy note enumerating the disagreeing sources and the four-authority-triangulation result so far.
- **Never silently override** the registry, project memory, or any prior plan-rev attribution. Silent override is the root-cause pattern that produced both Layer-1 and Layer-2 inversions and is explicitly banned.
- **Document the disposition** under a CORRECTIONS block (sub-plan-level or major-plan-level, whichever is in scope) per the pathological-HALT discipline; user-enumerated pivot path is required before propagation.

The byte-exact-immutability invariant on the address registry (registry spec doc §1.3) means every token-identity-touching artifact downstream of MR-β.1 is responsible for verifying its address attribution against the registry at consumption time; the registry is the single source-of-truth and is the anchor against which third-party claims are checked, never the other way around.

## References

- **Address registry spec doc (sub-task 3 deliverable; authoritative override target):** `contracts/docs/superpowers/specs/2026-04-25-mento-native-address-registry.md` — CR + RC + SD trio convergence at commit `2a0dcf8fe`; RC fix-up re-review PASS at commit `1d30f6fc4`.
- **TR research file with prefix-block corrigendum (sub-task 4 deliverable):** `contracts/.scratch/2026-04-25-mento-userbase-research.md` — corrigendum prefix block authored at commit `c306a286a`.
- **HALT-VERIFY disposition memo (β path):** `contracts/.scratch/2026-04-26-mr-beta-1-1-halt-resolution-beta.md`.
- **MR-β.1 sub-plan source-of-truth:** `contracts/docs/superpowers/sub-plans/2026-04-25-ccop-provenance-audit.md` — §C sub-tasks 1-5, §H CORRECTIONS, §I CORRECTIONS Rev-5.3.5 β-resolution.
- **Major plan anchor:** `contracts/docs/superpowers/plans/2026-04-20-remittance-surprise-implementation.md` — Rev-5.3.5 CORRECTIONS block, Rev-5.3.4 CORRIGENDUM block, Rev-5.3.3 CORRECTIONS block.
- **Project memory β-corrigenda (Authority 4):** `project_mento_canonical_naming_2026` (β-corrigendum block at file top); `project_abrigo_mento_native_only` (β-corrigendum extension).
- **Anti-fishing discipline anchor:** `feedback_pathological_halt_anti_fishing_checkpoint`.

**End of safeguard memo.**
