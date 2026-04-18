# I Let an AI Research Agent Loose on 7,000 Lottery Draws — Here's What It Found

*Can machine learning find patterns in truly random data? I built an autonomous research system to find out.*

---

## The Setup

Everyone wonders: can AI predict the lottery? It's the million-dollar question — literally.

I had access to 41 years of real Australian lottery data from the Lotterywest WA Government API:

| Lottery | Draws | Format | Years |
|---|---|---|---|
| Saturday Lotto | 2,059 | 6 from 45 + 2 supp | 1985–2026 |
| Oz Lotto | 1,070 | 7 from 47 | 1994–2026 |
| Powerball | 418 | 7 from 35 + PB | 1996–2026 |
| Mon/Wed Lotto | 942 | 6 from 45 + 2 supp | 2006–2026 |

That's **7,629 real draws** — no synthetic data, no simulations. The real deal.

## The Approach

Inspired by Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) project (where AI agents autonomously iterate on LLM training), I built an autonomous research loop that tries every reasonable analysis strategy without human intervention:

1. **Frequency analysis** — Are some numbers drawn more than others?
2. **Gap analysis** — Are some numbers "overdue"?
3. **Pair frequency** — Do certain number combinations appear together too often?
4. **Autocorrelation** — Do past draws influence future draws?
5. **Fourier transform** — Is there hidden seasonality or periodicity?
6. **Markov chains** — Does ball X tend to follow ball Y?
7. **LSTM neural network** — Can deep learning learn sequential patterns?
8. **Transformer attention** — Can attention mechanisms spot what LSTMs miss?
9. **Anomaly detection** — Are some draws statistically "impossible"?
10. **Ensemble consensus** — Do multiple models agree on anything?
11. **Jackpot-weighted analysis** — Do big jackpots correlate with patterns?
12. **Number clustering** — Are there hidden groups of numbers?

The agent ran all 12 strategies, measured confidence scores and statistical significance, and reported only genuine anomalies.

## The Results

Spoiler: **every single strategy found the same thing. Nothing.**

### Statistical Tests — All Green

| Lottery | Chi² p-value | Ljung-Box p | Max Z-score | Verdict |
|---|---|---|---|---|
| Saturday Lotto | 0.29 | 0.24 | 2.38 | ✅ Random |
| Oz Lotto | 0.86* | 0.77 | 1.92 | ✅ Random |
| Powerball | 0.94 | 0.07 | 1.79 | ✅ Random |
| Mon/Wed Lotto | 0.60 | 0.07 | 2.53 | ✅ Random |

*Oz Lotto showed p=0.00 initially, but this was a **format change artifact** — the pool expanded from 45 to 47 in March 2026 (just 4 draws ago). Balls 46 and 47 barely existed. Controlling for the pool-45 era: p=0.86, perfectly uniform.*

### ML Models — No Better Than Guessing

| Model | Saturday Lotto | Random Baseline | Edge |
|---|---|---|---|
| LSTM (2-layer) | 12.91% | 13.28% | **-0.37%** |
| Transformer (attention) | ~13% | ~13% | **~0%** |
| Markov chain | N/A | N/A | **No signal** |
| Fourier analysis | N/A | N/A | **No periodicity** |
| Ensemble consensus | N/A | N/A | **No agreement** |

For Saturday Lotto (6 from 45), random chance gives you ~13.3% accuracy. Every ML model converged to exactly this baseline — or slightly below it.

### The "Interesting" Red Herrings

The system did flag two things worth discussing:

**1. The (3,13) pair** — Appeared 22 times vs expected 16.4 (p=0.003). Sounds significant! But with 990 possible pairs tested, you'd expect ~5 pairs to pass p<0.05 by pure chance. After Bonferroni correction (p < 0.00005 required): **not significant.** Classic multiple testing trap.

**2. Oz Lotto format change** — Chi² p=0.00 with max Z-score of 10.49. Alarming at first glance! But balls 46 and 47 were only added 4 draws ago. This wasn't a pattern — it was a **rule change.** Once properly controlled for: p=0.86.

Both are excellent examples of why you need domain knowledge alongside statistical tools.

### One Actually Useful Finding

There's a weak negative correlation (r=-0.098, p=0.024) between the **sum of drawn numbers** and the **Division 1 prize pool**. Translation: when more people play (big jackpots), winning tickets tend to have lower-number sums.

Why? Because **humans pick birthdays** — numbers 1-31 are over-represented in player selections. When a low-number draw comes up, more people win, and the prize splits more ways. So if you're going to play (which you shouldn't, statistically), picking numbers above 31 gives you slightly better expected value — not because they're drawn more often, but because you'll share the prize with fewer people.

## The Honest Answer

**No AI, ML, statistical method, or pattern recognition technique can predict lottery numbers.** Not today, not with more data, not with bigger models.

The Australian Saturday Lotto uses a physical ball machine with independently verified draws. Each draw is genuinely random — by design. The entire point of a lottery is that it *cannot* be predicted.

What this experiment *does* demonstrate is the power of the scientific method:

- **Null results are valuable.** Confirming randomness with 12 independent methods is genuinely useful — it rules out equipment malfunction, tampering, and format artifacts.
- **Autonomous research loops work.** The same pattern Karpathy uses for LLM training can be applied to any iterative analysis task.
- **Domain knowledge matters.** The Oz Lotto "anomaly" would have fooled a purely statistical analysis. Knowing the format history turned a false positive into a controlled observation.

## The Code

The full analysis pipeline with all 12 strategies, the autoresearch loop runner, and visualizations is available at:
**github.com/bowen31337/aus-lottery-ml** (private repo)

Data source: [Lotterywest WA Government API](https://www.lotterywest.wa.gov.au/api/games/5127/results-csv)

## Methodology Notes

- All statistical tests use α = 0.05
- Multiple testing corrected via Bonferroni where applicable
- LSTM: 2-layer, 64 hidden units, 20-draw sequence, 80/20 train/test split
- Transformer: 4-head attention, 64-dim, same split
- Anomaly detection: Isolation Forest with 5% contamination
- Code: Python 3.11, PyTorch, scikit-learn, scipy, statsmodels

---

*If this kind of autonomous research interests you, check out [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) for the LLM training version. And if you're still playing the lottery — at least pick numbers above 31.*
