# Spec Review: Completeness and Clarity -- Rev 2
# Angstrom x Panoptic Vault Architecture Design (2026-04-09)

Reviewer: Mama Bear (Sonnet 4.6)
Date: 2026-04-09
Scope: Verification of Rev 1 findings resolution and overall Rev 2 quality

---

## 1. Code Leakage Check

Rev 1 flagged six Solidity identifiers used as architectural concepts rather than prose descriptions. The
requirement is a 100% code-agnostic spec.

**Result: PARTIALLY RESOLVED -- three residual instances remain.**

Residual instances found:

- Section 4.4, paragraph "Observable:" -- `growthInside(tL,tU)` appears as a function-call expression
  embedded in a sentence describing what ct0 tracks. This should read "the cumulative reward growth
  within a configured tick range" without the parenthesized argument syntax.

- Section 3 (Architecture Diagram), ct0 box -- `totalAssets driven by growthInside(tL,tU)` uses the
  same function-call form. ASCII diagrams that are purely illustrative can stretch this rule, but the
  parenthesized argument form is specifically what Rev 1 flagged as "code leakage". The ct0 box
  elsewhere already uses human-readable text so this is inconsistent.

- Section 5 (Phased Rollout table), Phase 2 exit criteria column -- `growthInside` appears without
  argument syntax and in a clearly technical context. This one is borderline acceptable (it is a
  well-established concept name used as a noun), but it is still an identifier. For a code-agnostic
  spec it should read "range-specific reward growth".

Instances that were in Rev 1 and are now clean:

- `poolRewards[poolId].globalGrowth` -- replaced throughout with plain prose descriptions.
- `poolRewards[poolId].getGrowthInside(tL,tU)` -- replaced, except residual above.
- `TokenId` -- no longer appears as an architectural concept outside Section 11's code inventory table,
  where file-and-type names are appropriate.
- `Q128.128` -- appears in Section 2.2 and Section 4.2 as a unit description. These are now used
  explanatorily ("Q128.128 units of asset0 per unit of liquidity") and immediately explained in
  Section 2.2. Acceptable in the denomination context -- these are not function calls.

Net: three residual instances, two of which are direct function-call expressions the Rev 1 reviewer
explicitly flagged. Not clean.

---

## 2. Missing Sections Check

### Deployment Strategy
Section 4.6 (Custom Factory) and Section 4.7 (Bootstrapping) together cover deployment responsibilities
and sequencing. Section 8 (Upgrade Governance) covers post-deploy upgrade path. Section 7 risk table
adds a factory misconfiguration row with mitigation.

Assessment: A dedicated "Deployment Strategy" section was not added, but the material is distributed
across 4.6, 4.7, and 7. For an architectural spec (not an operational runbook), this coverage is
sufficient. The factory section explicitly names the deployment sequence (V_B, ct0, ct1, PanopticPool)
and the bootstrapping section addresses initial liquidity. ADDRESSED adequately.

### Testing Strategy
Section 5 now states: "Each phase gets its own implementation spec that defines the detailed task
breakdown, test plan, and acceptance criteria." Phase exit criteria in the table reference test outcomes
(e.g., "Playground test passing", "Short put on a range earns theta").

Assessment: There is no standalone testing strategy section. The deferral to per-phase implementation
specs is a reasonable architectural choice -- testing strategy at this level would be premature. The
Phase 0 exit criterion explicitly references the existing playground test. ADDRESSED at appropriate
level of abstraction for an architecture spec. Acceptable.

### Phase Exit Criteria
Section 5 now includes a three-column table (Phase, What, Exit Criteria). Each phase has a concrete,
observable exit criterion.

- Phase 0: Playground test passing, short put lifecycle end-to-end.
- Phase 1: V_B share price appreciation verified, depositors can enter/exit, pool pair live.
- Phase 2: Options accrue streaming premium from Angstrom rewards; short put earns theta, long put
  pays for protection. Labeled as minimum viable product.
- Phase 3: Multiple ranges priced simultaneously, different legs reference different exposures.

Assessment: FULLY ADDRESSED. Exit criteria are specific and testable.

### Upgrade Governance
Section 8 added. Covers timelock (minimum 24h suggested), upgrade key ownership (protocol multisig
initially), scope of upgrades (yield-function logic only, immutable args cannot change).

Assessment: ADDRESSED. The section is intentionally brief -- exact timelock duration and governance
path are deferred to implementation. For an architecture spec this is appropriate. One gap: Section 8
does not state who has the authority to call the upgrade function or whether there is an emergency
pause path. These could be flagged for implementation-phase resolution.

### ct0 Range Configuration Lifecycle
Section 4.4 now contains a dedicated paragraph titled "Range configuration lifecycle" that explains:
- Range is set by the proxy's owner/admin at configuration time
- Before it is set, ct0 behaves as vanilla CT
- Changing the range after setting affects future accrual only
- Entry snapshots of existing depositors remain valid
- Implications of range changes on existing positions flagged for implementation analysis

Assessment: FULLY ADDRESSED. The lifecycle is described clearly and the open question is explicitly
surfaced.

---

## 3. New Sections Quality Assessment

### Section 2.2 (Denomination Resolution)
Clear. The problem (both accumulators in asset0 but Panoptic needs two distinct tokens) and the
resolution (V_B shares as token1) are stated in plain English. The three-bullet consequence list
(ct0 direct, ct1 near-vanilla, no price oracle) is well-structured. The final note about ct1 not
needing a custom totalAssets override is a useful negative statement that prevents over-engineering.

One clarity gap: "near-vanilla CollateralTracker wrapping an ERC-20" -- the word "near-vanilla" is
used but its deviation from vanilla is not defined here. It is defined later in Section 4.3. Forward
references should be explicit ("near-vanilla, as defined in Section 4.3") or the terminology should
be consistent. Minor.

### Section 2.6 (Hybrid Clone-Proxy Pattern)
Clear. The problem (Clone reads config from bytecode; standard UUPS/diamond proxies lack these
immutable args) is stated before the solution. The solution (proxy deployed with immutable args in
bytecode, business logic delegates to upgradeable implementation) follows logically. The two invariants
at the end (config never changes, yield logic can evolve) correctly bound the scope.

Gap: The section does not name or reference any existing implementation of the hybrid clone-proxy
pattern. Is this a known pattern with a reference implementation, or a novel design? A new reader
would benefit from knowing whether this is established or must be invented. Flagged -- not a blocker
for architecture review, but important for Phase 1 implementation planning.

### Section 2.7 (SFPM Accumulator Adapter)
Clear and well-argued. The problem (no natural swap demand on V_B_shares pair means native Uniswap
fee growth is near zero, so options would have zero streaming theta) is correctly identified and
motivated. The resolution (conditional read path in SFPM checking pool type) is minimal and the
scope is precisely bounded ("only modification to the SFPM"). Moving this to Phase 2 rather than
deferring it is justified by the MVP argument.

One clarity issue: "both are Q128.128 growth-per-unit-liquidity" -- Q128.128 is still used as a
format identifier here. Acceptable in this context (it describes data format parity between two
sources), but inconsistent with the code-agnostic intent.

### Section 4.5 (SFPM Accumulator Adapter)
Clear. Describes role, what changes, and what stays unchanged. The reentrancy note is important and
correctly placed. The direct storage read avoidance of callbacks is correctly identified as the
safety mechanism.

Gap: The section says the adapter "checks whether the pool is Angstrom-backed." The mechanism for
this check is not described. How does the SFPM know? Is there a registry, a flag on the pool key, or
a factory-maintained mapping? This is a meaningful architectural decision left unresolved. Should
either be decided here or explicitly deferred with a placeholder.

### Section 4.7 (Bootstrapping)
Clear. The bootstrapping problem (no natural swap demand, so initial liquidity must be seeded) is
identified. The strategy (protocol team seeds at deployment) is practical. The incentive structure
for subsequent LPs (option writers must deposit into CT, indirectly providing liquidity) is a
useful insight.

Gap: "One-time cost" is stated without a magnitude estimate or a reference to how this will be
funded. For an architectural spec this may be acceptable, but implementation teams will need a
concrete number. Flagged as an implementation-phase item.

### Section 8 (Upgrade Governance)
Adequate but thin. The three bullets cover the essential decisions. The "minimum 24h" suggestion is
appropriately hedged as a suggestion rather than a constraint. The path to key burn is noted as
future work.

Gaps already noted: no emergency pause path, no specification of who can propose vs. execute an
upgrade (single key vs. multisig threshold). For an architecture spec these are acceptable gaps to
flag forward.

### Section 10 (QA Review Log)
Clear as a historical record. The three-reviewer table accurately maps findings to resolution
locations. The log correctly identifies which critical findings (C1, C2, C3) are resolved and where.

One clarity issue: Findings I7 and S3 are mentioned in the Completeness row but their resolution
status is not stated in the table. The reader must infer they are resolved by reading Rev 2. A
"Resolved in Rev 2" column or a resolution note per row would close this loop.

---

## 4. Architecture Diagram Assessment

The diagram (Section 3) was substantially updated. Checking against the two Rev 1 gaps:

**V_B vault as standalone with V_B_shares flowing to ct1:**
The diagram now shows V_B vault as an independent block with its own box labeled "standalone
ERC-4626". The arrow from V_B block to ct1 is implicit -- the diagram shows `ct1 (near-vanilla CT)
Holds: V_B_shares` and the V_B box above it is labeled "Mints: V_B_shares". The flow V_B -> ct1 is
readable, though not explicitly arrow-connected. A direct arrow from V_B to ct1 labeled
"V_B_shares = token1" would make the relationship unambiguous. Minor clarity gap.

**Factory present in diagram:**
The factory is now present as a box at the bottom of the diagram labeled "Custom Factory" listing
all four deployed components. ADDRESSED.

**ct0 label:**
The diagram ct0 box reads "ct0 (hybrid clone-proxy)" which is consistent with the spec terminology.
Correct.

**One new inconsistency:** The diagram shows ct0 box reading "totalAssets driven by
growthInside(tL,tU)" -- this is the code-leakage instance noted in Section 1. In the diagram it is
also architecturally ambiguous: does this mean Phase 2 behavior or Phase 1? The diagram should note
phase sensitivity or use a non-phase-specific description.

---

## 5. Internal Consistency Check

Cross-referencing all 11 sections for alignment:

**Section 2.2 vs Section 4.2:** Section 2.2 says ct1 "does not need a custom totalAssets override".
Section 4.2 (V_B Vault) says "conversion factor k maps Q128.128 accumulator units to asset0
denomination." Section 4.3 confirms ct1 is standard CT. These three are consistent.

**Section 2.5 vs Section 4.2:** Both describe conversion factor k for V_B. They are consistent.
However, k is described as "maps Q128.128 accumulator units to asset0 denomination" (Section 2.5)
and the same phrase appears in Section 4.2. The value or formula for k is not given in either
location. This was a Rev 1 finding ("Conversion factor k undefined") -- see Section 6 below.

**Section 2.6 vs Section 4.4:** The hybrid clone-proxy pattern is introduced in 2.6 and applied to
ct0 in 4.4. Section 4.4 says ct0 uses hybrid clone-proxy; the diagram says "(hybrid clone-proxy)";
Section 4.6 says the factory deploys "ct0 as hybrid clone-proxy". Consistent throughout.

**Section 2.7 vs Section 4.5 vs Section 5:** SFPM adapter is introduced in 2.7 (Phase 2 decision),
described in 4.5 (component), and placed in Phase 2 exit criteria in Section 5. Consistent.

**Section 4.8 vs Section 5:** Section 4.8 says "Multi-period RAN = roll of single-period positions
across epoch boundaries ... The component responsible for epoch boundary management and roll logic
must be defined during Phase 2 implementation." Section 5 Phase 2 exit criteria does not mention
roll logic or epoch boundary management. This is a cross-reference gap: Phase 2 exit criteria should
either include epoch roll logic or explicitly defer it. As written, a reader of Section 5 would not
know epoch boundary management is a Phase 2 concern.

**Section 6.2 vs Section 4.2 and 4.4:** Invariant 6.2 (Withdrawal Solvency) states that
accumulator-sourced value that has not been converted to actual tokens is not withdrawable. Section
4.2 says the vault "accepts asset0 deposits" and V_B_shares are minted. The mechanism by which
accumulator-sourced value becomes actual tokens (i.e., the reward harvest/sweep process) is not
described anywhere in the spec. This is a meaningful architectural gap -- solvency depends on it.
Flagged.

**Section 7 risk table vs Sections 6 and 8:** Section 7 references Invariant 6.2 for phantom asset
inflation mitigation. Section 7 references timelock for upgrade risk. Both cross-references resolve
correctly.

**Section 11 (Existing Code Inventory) vs Section 3 (Architecture Diagram):** Section 11 lists
`AngstromRANOracleAdapter` at `contracts/src/ran.sol`. Code investigation finds this file does not
exist at that path -- the actual adapter is at
`contracts/src/_adapters/LpRevenueAngstromOracleAdapter` (no .sol extension, different contract
name). The import in AccrualManagerMod.sol uses `"core/src/ran.sol"` (a remapping alias), suggesting
`ran.sol` exists in a referenced library or a separate path not under `contracts/src/`. The Section
11 path is incorrect or at minimum misleading. This is a factual error in the code inventory.

**Section 3 (Diagram) label accuracy:** The diagram says `poolRewards[poolId].globalGrowth
(pool-wide)` and `poolRewards[poolId].getGrowthInside(tL,tU) (per-range)` in the Angstrom Layer
box. These are verbatim Solidity accessor expressions -- code leakage in the diagram. The diagram
should use descriptive labels, not code.

---

## 6. Previously Undefined Terms

### Q128.128
Section 2.2 now introduces Q128.128 with the description "Q128.128 units of asset0 per unit of
liquidity." This explains what the number represents but does not define the format itself (128 bits
integer part, 128 bits fractional part, value = raw_uint256 / 2^128). A new reader unfamiliar with
fixed-point formats would still be confused. The spec should either add a one-sentence definition or
reference a glossary. Partially addressed.

### Growth-outside accumulators
Section 4.4 uses "growth-outside accumulators" as a term and Section 6.6 refers to "growth-outside
accumulator math." Neither section defines what growth-outside means or how it differs from
growthInside. A new reader cannot understand why growthInside is always <= globalGrowth from the
spec alone. Section 4.4 describes this as "the observable" but does not explain the accumulator
mechanics. The PoolRewards.sol code (confirmed in review) shows the three-case logic
(below/above/spanning range), but the spec does not describe this. Inadequately addressed.

### TokenId
Section 4.8 references "standard TokenId" and Section 11 lists "TokenId encoding." In Section 4.8
the term appears as "Options written via standard TokenId" (diagram) and "TokenId encoding -- legs,
strikes, widths, risk partners" (Section 4.8). These are used as proper nouns identifying a Panoptic
encoding scheme. Acceptable in an architectural spec that explicitly identifies Panoptic as a
dependency -- a reader would look this up in Panoptic docs. However, a one-line definition (e.g.,
"Panoptic's packed option descriptor encoding legs, strikes, and risk partners") would help. Minor.

### Conversion factor k
Section 2.5: "The conversion factor k maps Q128.128 accumulator units to asset0 denomination."
Section 4.2 repeats the same phrase. k is undefined in both. The formula
`totalAssets = k * globalGrowth` (or some variant) is not given. A reader cannot understand whether
k is a deployment parameter, a computed value, or a fixed constant. This was a Rev 1 finding and
remains unresolved. FLAG.

### Capponi's first-passage-time
Section 7 risk table mentions "First-passage-time risk" for the frozen range risk row. This term no
longer appears as "Capponi's first-passage-time" (the Rev 1 form that required a citation). It now
appears generically as a risk descriptor in a table cell. Acceptable. ADDRESSED by rephrasing.

---

## 7. Summary of Findings

| Finding | Category | Status | Severity |
|---|---|---|---|
| Residual code leakage: `growthInside(tL,tU)` in Section 4.4 | Code leakage | NOT RESOLVED | Minor |
| Residual code leakage: `growthInside(tL,tU)` in diagram ct0 box | Code leakage | NOT RESOLVED | Minor |
| Residual code leakage: `growthInside` in Phase 2 exit criteria | Code leakage | BORDERLINE | Minor |
| Residual code leakage in diagram Angstrom Layer box (accessor expressions) | Code leakage | NEW | Minor |
| Deployment strategy | Missing section | RESOLVED (distributed) | -- |
| Testing strategy | Missing section | RESOLVED (deferred to phase specs) | -- |
| Phase exit criteria | Missing section | RESOLVED | -- |
| Upgrade governance (Section 8) | Missing section | RESOLVED | -- |
| ct0 range configuration lifecycle | Missing section | RESOLVED | -- |
| Phase 3 diamond dispatch | Underspecified | DEFERRED (noted as Phase 3 implementation spec) | Minor |
| Conversion factor k undefined | Undefined term | NOT RESOLVED | Moderate |
| Growth-outside accumulators undefined | Undefined term | NOT RESOLVED | Minor |
| Q128.128 format partially explained but not defined | Undefined term | PARTIALLY RESOLVED | Minor |
| Section 11: `ran.sol` path incorrect (does not exist at listed path) | Factual error | NEW | Moderate |
| SFPM adapter pool-type detection mechanism unspecified | Architectural gap | NEW | Moderate |
| Reward harvest/sweep process for withdrawal solvency (Inv 6.2) not described | Architectural gap | NEW | Moderate |
| Epoch roll logic (Section 4.8) absent from Phase 2 exit criteria | Cross-reference gap | NEW | Minor |
| V_B to ct1 flow not arrow-connected in diagram | Diagram clarity | PARTIAL | Minor |
| Hybrid clone-proxy: no reference implementation or prior art | Clarity gap | NEW | Minor |
| Section 10 QA log: I7/S3 resolution status not stated | Clarity gap | NEW | Trivial |
| Section 2.2: "near-vanilla" forward reference not explicit | Clarity gap | NEW | Trivial |
| Upgrade governance: emergency pause path absent | Governance gap | NEW | Minor |
| Phase 2 exit criteria: epoch roll not mentioned | Cross-reference | NEW | Minor |

---

## 8. Verdict

**FLAG**

Rev 2 successfully resolves the five major missing sections and the three critical findings (C1, C2,
C3) from the QA review log. The document is substantially better than Rev 1. A new reader can
understand the system architecture, the denomination split, the two-vault design, and the phased
rollout.

However, three items prevent a PASS:

1. **Conversion factor k remains undefined.** This was a Rev 1 finding and is unresolved. k is the
   fundamental parameter connecting Angstrom's accumulator to vault share price. Without at least a
   formula sketch or a statement of whether k is a constructor parameter or a derived value, the
   yield function cannot be implemented correctly.

2. **Section 11 code inventory contains a factual error.** `AngstromRANOracleAdapter` is listed at
   `contracts/src/ran.sol`, but that path does not exist in the repository. The actual adapter is at
   `contracts/src/_adapters/LpRevenueAngstromOracleAdapter`. An implementer following Section 11
   will start from the wrong file.

3. **SFPM adapter pool-type detection mechanism is unspecified.** The adapter checks "whether the
   pool is Angstrom-backed" but the check mechanism is not described. This is a Phase 2
   implementation decision, but it has architectural implications (registry vs. flag vs. factory
   mapping) that should be decided at the design stage, not left to implementation.

These three items require targeted fixes before the spec is ready to hand off to an implementer.
None require a structural revision -- they are scoped additions. A Rev 3 with these three items
addressed, plus cleanup of the remaining code-leakage instances, would pass.
