
## Script (~400 words, ~150 wpm)

### [0:00–1:00] HOOK — The Risk Nobody Hedges (Title slide)

--> SLIDE 1 tittle slide (borrow from presentation.tex)

-- > SLIDE 2 

Adverse competition is one of the risks liquidity providers face.  [Ma-Crapi REF][Capponi J][Aquina][FLAIR]



--> SLIDE 3
- Approximately 7% of LPs capture around 80% of trading fee revenue [Aquilina REF].


--> SLIDE 4

- Further work confirmed this is structural — JIT liquidity creates adverse competition [Capponi, Jia, and Zhu]. 



--> SLIDE 5

- Metrics have been created to capture this [FLAIR REF]. But can you price it? Can you hedge it? We built ThetaSwap to find out — and are presenting phase one today.


--> SLIDE 6


The first step: make the risk observable. Our oracle measures fee concentration in real time — who enters, who earns fees, how fast positions turn over.                                          



### [1:20–2:20] LIVE DEMO (Terminal: `make sol-test-demo`)

make sol-test-demo

1. **[0:00–0:05]** "Let me run the test suite."`make sol-test-demo`

(WHILE COMPILING)


2. **[0:05–0:20]** "Scenarios from the references, simulated and computed off-chain, verified on-chain. If the numbers match, the oracle works."
4. **[0:25–0:60]**
   - "**Equilibrium** — two identical LPs, equal capital. No concentration, no risk."
   - "**JIT Crowd Out PLP** — 9x capital that lives for 2 blocks versus 99 blocks. 
   Consequently fee concentration spikes. This is the adverse regime
   - "**Mild crowding-out** — 1:2 capital ratio. fee concentration is small but positive. The index detects it."


make sol-test-demo

### [2:20–2:40] EVIDENCE + BACKTEST (Results table + Reserve dynamics)

--> SLIDE 7

> "We validated on 600 real ETH/USDC positions: fee concentration flips from protective to adverse at 9% fee dispersion — LPs would pay 10% above hourly fees for protection. The backtest shows around 20% of positions better off hedged, and only 1 day in 41 triggers"                                                          

### [2:40–3:00] ROADMAP


--> SLIDE 8

Three milestones ahead: 
- first, validate across more pools and asset pairs. 

- Second, extend the oracle to other protocols.

- Third, the insurance market — the CFMM to trade this risk on-chain. Thank you."

