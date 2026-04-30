import [$\sigma (X/Y)$](./notes/MACRO_RISKS.md)

import [minimizeIncomeInequaility](/home/jmsbpp/learning/macro-context/INCOME_INEQUALITY.md)


import [context](/home/jmsbpp/learning/macro-context/SAVINGS.md)



$$
\begin{aligned}
    CF_T^{(a)} = \overbrace{I_T^{(a)}\left(\sigma (X/Y)\right)}^{\text{inflow}} - \overbrace{O_T^{(a)}\left(\sigma (X/Y)\right)}^{\text{outflow}} \\
    \\
    \Delta^{(a)} = \frac{\partial}{\partial \sigma (X/Y)} \, CF_T^{(a)} \quad \Gamma^{(a)} = \frac{\partial^2}{\partial \sigma (X/Y)^2} \, CF_T^{(a)} 
    \tag{1}
\end{aligned}
$$

From MiniPay economic enviroment:

We need $(a_s, a_l)$ economic agents (Apps):

$$
\begin{aligned}
    \underbrace{\Delta^{(a_s)} < 0}_{\text{app economically short } \sigma (X/Y)} \\
    \\

    \underbrace{\Delta^{(a_l)} > 0}_{\text{app economically long } \sigma (X/Y)}
\end{aligned}
$$

# Candidates $(a_s, a_l)$

## 1.

### $a_s$: ($X$ Payment reel) :: "Pay Bill in $X$ using MiniPay"

#### **SALES PITCHS**

- *"We guarantee the bill the users pay wont exceed $\$ X USD$ this month"*

### $a_l$ : ($Y$ Yield farmer) :: "US Yield MiniApp"

#### **SALES PITCHS**

- *"Earn stable yield from real payment deemand"*


### Models

#### **Simplest Deterministic**

We proceed by instantiating a $CF_T{(a_l)}$ from integrating $(1)$, this is choosing one admissible function

Consider a USD Vault mini app that $a_l$ earns fees proportional to realized FX movement

$$
\begin{aligned}
    CF_T^{(a_l)} \, = \, \sum_{t=0}^{T} \, r_{(a_l)} \, \mid \, (X/Y)_{t}  - (X/Y)_{t-1}\, \mid
\end{aligned}
$$

Now consider $a_s$ to be a local payment reel that enables the payment of fixed time obligations to its users in local stable coin $X$

For the simplest case of one user with fixed obligation $B$ at time $T, \, B_T$
and deposits at time $t_0 ; \, D_{t_0}^{(Y)}$.

Consider vault:

$$
\begin{aligned}
    (\Upsilon, r)
\end{aligned}
$$

App allocates:

$$
\begin{aligned}
    &\theta\, D_0^{(Y)} &&\text{: Yield vault portion} \\
    &(1 - \theta)\, D_0^{(Y)} &&\text{: Liquid buffer for payments}
\end{aligned}
$$

where $\theta \in [0,1]$.

Where yield vault dynamics are defined as:

$$
\Upsilon_T(r, \theta D_0^{(Y)}, T; \cdot) = \theta D_0^{(Y)} \cdot (1 + rT)
$$

The app must guarantee delivering $B_T$ in $X$, regardless of FX path.

It derives a policy that minimizes the risk of not being able to meet the obligation at a stable and predictable cost. S

$$
\begin{aligned}
    \min_{\{q_t\}_{t=1}^T} \, \sum_{t=1}^{T} \frac{q_t}{(X/Y)_t} \\
    \\
    \text{s.t}
    
    \sum_{t=1}^T \, q_t \, (X/Y)_t = B_T \\
    \\
    q_t > 0 \quad \forall_t
\end{aligned}
$$



The app must source:

$$
\begin{aligned}
    C_T^{(a_s)} = \Big (\frac{B}{(X/Y)} \Big )_T
\end{aligned}
$$

Thus, we have:

$$
\begin{aligned}
    CF_T^{(a_s)} &= \Upsilon_T(r, \theta D_0^{(Y)}, T; \cdot) - \sum_{t=1}^{T} \frac{q_t}{(X/Y)_t}
\end{aligned}
$$


Assume the stationary $\overline{(X/Y)}$ which is the expected value of echange rate.

We define the following minimal deterministic perturbation  path generator for $(X/Y)$:

$$
\begin{aligned}
    \dot{(X/Y)}^{\epsilon , \, \omega } &:= (X/Y)_t \, (\epsilon , \, \omega ) \\
    \\
    &= \Big (1 + \epsilon  \cdot ( \cos^2( \omega \, t)- \frac{1}{2})\Big ) \overline{(X/Y)}; \quad 0 < \epsilon < 1
\end{aligned}
$$

Note the statistical variance as proxying deprication risk:

$$
\begin{aligned}
    \sigma_{T} \Big (\, \dot{(X/Y)} \, \Big) &= \frac{1}{T}\, \sum_{t=0}^{T} \, \Big (\, (X/Y)_t - \overline{(X/Y)}\, \Big)^2
\end{aligned}
$$
From the above, one can prove that:

$$
\begin{aligned}
     (X/Y) \bigg ( \sigma_{T} \Big (\, \dot{(X/Y)} \, \Big) \, , \omega \, \bigg) =  \overline{X/Y} \left( 1 + \epsilon \, (\sigma_T \,) \left( \cos^2(\omega t) - \frac{1}{2} \right) \right ) \\
     \\
     \epsilon \, (\sigma_T \,) = \sqrt{\frac{8\,\sigma_T}{\overline{(X/Y)}^2}}
\end{aligned}
$$


Which allows to take $(\Delta^{a_l} ,\, \Delta^{a_s})$:


As an exercise the actual derivation but the result is:

$$
\begin{aligned}
    \Delta^{(a_l)} &= \frac{4 \, r_{(a_l)}}{\overline{X/Y} \, \epsilon \, (\sigma_T)} \, \sum_{t=1}^T \, \mid \, f_t - f_{t-1}\, \mid > 0\\
    \\
    \Delta^{(a_s)} &= \frac{4}{\overline{(X/Y)} \, \epsilon \, (\sigma_T)} \, \sum_{t=1}^T\,  q_t \, \frac{f_t}{(X/Y)_t^2} < 0
\end{aligned}
$$

Where :

$$
\begin{aligned}
    f_t &:= \cos^2 \, (\omega \, t) - \frac{1}{2}
\end{aligned}
$$

> Note: The verification of $\Delta^{(a_s)} < 0$ is not trivial

Now we aim to introduce a payoff $\Pi \, (\sigma_T \, )$ that makes both delta neutral. This are the **CPO**:

$$
\begin{aligned}
    \Delta^{a_l + \Pi} &= \Delta^{a_l} + \frac{\partial}{\partial \sigma_T} \, \Pi &= 0 \\
    \\

    \Delta^{a_s - \Pi} &= \Delta^{a_s} - \frac{\partial}{\partial \sigma_T} \, \Pi &= 0
\end{aligned}
$$

Note that structurally:

$$
\begin{aligned}
    \frac{\partial}{\partial \sigma_T} \, \Pi \, 
    &= - \Delta^{(a)} \\
    \\
    & \implies \\
    \\
    \Pi \, \Big (\, \sigma_T \,\Big)&= - \int_{0}^{\sigma_T} \, \Delta^{(a)} \, (u) \, du
\end{aligned}
$$

Applying to the demand side $a_l$:

$$
\begin{aligned}
    \Pi^{l} \, \Big (\sigma_T\Big) &= - \int \, \Delta^{(a_l)} \, (\sigma_T) \, d\, \sigma_T \\
    \\
    & \implies \, \Big \langle \, \Delta^{(a_l)} \propto \frac{1}{\sqrt{\sigma_T}}\, \Big \rangle \\
    \\
    & \sim -2 \, C \, \sqrt{\sigma_T} \\
    \\
    & = K_l \, \sqrt{\sigma_T}
\end{aligned}
$$

Then one can show, that for the supply side, it holds:

$$
\begin{aligned}
    \Pi^{s} \, (\sigma_T) &= K_s \, \sqrt{\sigma_T}
\end{aligned}
$$

And equilibria holds iff $K_s = K_l$

Now we need to introduce pricing:

$$
\begin{aligned}
    \hat{\Pi^{s}} &= P_0^{\Pi} - \Pi (K^{\star}\,; \sigma_T) \\
    \\
    \hat{\Pi^{l}} &= \Pi (K^{\star}\,; \sigma_T) - P_0^{\Pi} 
\end{aligned}
$$

To endogenize $K$ we decide to use the Carr-Madan theorem that says that any continuous payoff can be replicated using options. 

In this case, since $\sqrt{\sigma_T}$ is not statistically sreplicable we use $\sigma_T$ and use the log-contract:


$$
\begin{aligned}
    \sqrt{\sigma_T} 
    &\approx \underbrace{\sqrt{\sigma_0} + \frac{1}{2\sqrt{\sigma_0}}\, (\sigma_T - \sigma_0)}_{\text{linearize the payoff}} \\
    \\
    &\implies \left\langle \text{Apply } \Pi \right\rangle \\
    \\
    \Pi\left(\sqrt{\sigma_T}\right) 
    &\approx \underbrace{K^{\star}}_{\text{constant}}\, \sqrt{\sigma_0} + \frac{K^{\star}}{2\,\sqrt{\sigma_0}}\,\sigma_T \\
    \\
    &\implies \left\langle \hat{K} := \frac{K^{\star}}{2\,\sqrt{\sigma_0}} \right\rangle \\
    \\
    &\approx \hat{K}\, \sigma_T \\
    \\
    &\implies \left\langle 
        \text{By Carr-Madan:} \quad
        \sigma_T 
        \sim 
        \int_0^{S_0} \frac{1}{K^2}\, P(K)\, dK 
        + \int_{S_0}^{\infty} \frac{1}{K^2}\, C(K)\, dK 
    \right\rangle \\
    \\
    &= 
    \boxed{
        \hat{K}\,\Big (\, \int_0^{S_0} \frac{1}{K^2}\, P(K)\, dK 
        + \int_{S_0}^{\infty} \frac{1}{K^2}\, C(K)\, dK\, \Big)
    }
\end{aligned}
$$

Since implementation is on discrete space, and to build with Panoptic we have:

$$
\begin{aligned}
    \int \, \text{OTM options} &\sim \, \sum_{j=1}^{N} \, w_j\, \text{IronCondor}_j 
\end{aligned}
$$

For condor $j$:

For condor $j$ we choose strikes $K_1 < K_2 < K_3 < K_4$.

**Choice:**

- Center:
  $$
  K_j \approx S_0 \cdot e^{x_j}
  $$
- Width:
  $$
  \Delta K_j
  $$

**🔥 Weight matching**

From Carr–Madan:
$$
w(K) \propto \frac{1}{K^2}
$$

Assign weights:
$$
w_j \propto \frac{1}{K_j^2}
$$

---

### 🎯 4. Aggregate payoff

Your discrete replication becomes:
$$
\Pi_T \approx \sum_{j=1}^{N} w_j \cdot \text{Condor}_j(S_T)
$$
	​
How many condors ($N$) ?

- 3 regions:
- left tail
- ATM
- right tail

👉 3 condors = 12 legs total (but 4 per position constraint is respected)



- Initialization requires calibration and a history

- What is the optimal rule for $T$ ?
    - Well, $T$ is actually user defined or defined by the demand side subject to its fixed time obligationcs

- prompt

[pre-req: npx skills add celo-org/celopedia-skills]

From @this_document find me a list of ordered ordered by fit likelihood of apps $a_l, a_s$
