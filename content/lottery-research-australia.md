# Australian Lotteries — ML/AI Pattern Analysis Research

> **Date:** 2026-04-18
> **Purpose:** Identify the best Australian lottery for a machine learning pattern analysis experiment

---

## Executive Summary

**Recommendation: Saturday Lotto (TattsLotto) as primary, Oz Lotto as secondary.**

Saturday Lotto offers the richest dataset (~2,800+ draws since 1972, weekly), simplest structure (6 from 45), most stable format (6/45 since 1985), and the best odds of finding any statistical signal. Oz Lotto is a strong secondary choice with ~1,680+ draws since 1994 and a richer feature space (7 numbers + 2-3 supplementaries).

---

## All Australian Lotteries — Comparison Table

| Lottery | Format | Draw Frequency | Since | Est. Total Draws | Div 1 Odds | Min Jackpot | Max Jackpot | Data Quality |
|---------|--------|---------------|-------|-----------------|------------|-------------|-------------|-------------|
| **Saturday Lotto** | 6 from 45 (+ 2 supp) | Weekly (Sat) | 1972 | ~2,800+ | 1 in 8,145,060 | $4M (shared) | $30M+ Megadraw | ⭐⭐⭐⭐⭐ |
| **Weekday Windfall** | 6 from 45 (+ 2 supp) | 3x/week (Mon/Wed/Fri) | 1979 (Mon), 1984 (Wed) | ~5,000+ | 1 in 8,145,060 | $1M (up to 6 winners) | $1M fixed | ⭐⭐⭐⭐⭐ |
| **Oz Lotto** | 7 from 47 (+ 2-3 supp)* | Weekly (Tue) | 1994 | ~1,680+ | 1 in 62,891,499 | $4M | $112M (2012) | ⭐⭐⭐⭐ |
| **Powerball (AU)** | 7 from 35 + 1 PB from 20 | Weekly (Thu) | 1996 | ~1,560+ | 1 in 134,490,400 | $5M | $200M (2024) | ⭐⭐⭐ |
| **Set for Life** | 7 from 44 (+ 2 supp) | Daily | 2013 | ~4,700+ | ~1 in 38,608,020 | $20K/mo for 20yr | $4.8M total | ⭐⭐⭐⭐ |
| **Super 66** | 6-digit sequential | Varies | Discontinued | Limited | Varies | Varies | Varies | ❌ |
| **Lucky Lotteries** | Raffle-style (numbers drawn sequentially) | Super: Mon-Fri, Mega: Tue/Thu | Ongoing | ~1,000+/yr | Varies | $500K/$1M min | $20M+ | ❌ |
| **The Pools** | Based on soccer match results | Weekly | 1960s-2013 | ~2,000+ | Varies | Varies | Varies | ❌ Discontinued |
| **Keno** | 20 from 80, player picks 1-10 | Every 3.5 min | 1990s | Millions | Varies by spot | $1M+ | $10M+ | ❌ Continuous |

\* Oz Lotto changed format: 6/45 (1994-2005) → 7/45 (2005-2022) → 7/47 (2022+). Supplementary numbers: 2 (until 2022), 3 (2022+).

---

## Detailed Lottery Analysis

### 1. Saturday Lotto (TattsLotto / Gold Lotto / X Lotto) ⭐ TOP PICK

**Why it's the best choice:**

- **Longest history:** Running since 24 June 1972 — over **53 years** of data
- **Most draws:** ~2,800+ weekly draws (52 weeks × 53 years)
- **Stable format:** 6 from 45 with 2 supplementary numbers since July 1985 (Draw 413). The earlier 1972-1985 era used 6 from 40 with 1 supplementary — still usable if normalized
- **Simplest structure:** Pure number draw, no powerball, no secondary barrel. Just 6 winning + 2 supplementary from a single pool of 45
- **Clean data:** Each draw = 8 numbers (6 main + 2 supp). Easy to model as a multivariate time series
- **Division structure:** 6 divisions provide rich label data for supervised learning
- **Frequent winners:** Division 1 is won regularly (1 in 8.1M odds), so there's meaningful jackpot rollover data to analyze

**Data characteristics:**
- Numbers range: 1-45
- Main numbers per draw: 6
- Supplementary numbers: 2
- Expected frequency per number (uniform): ~13.3% of draws = ~373 times per 2,800 draws
- Standard deviation of frequency (expected): ~15-18 occurrences across numbers
- **Hot/cold number analysis:** With 2,800 draws × 8 numbers, each number should appear ~498 times. Statistical deviations would be meaningful with this sample size

**Game changes to account for:**
- 1972-1985: 6 from 40, 1 supplementary → ~680 draws
- 1985-present: 6 from 45, 2 supplementary → ~2,130+ draws
- Recommendation: Use 1985+ data only for consistency (still 2,100+ data points)

### 2. Weekday Windfall (formerly Monday & Wednesday Lotto) ⭐ EXCELLENT SECONDARY

**Why it's strong:**

- **Massive dataset:** ~5,000+ draws since 1979 (Mon) / 1984 (Wed) / 2024 (Fri added)
- **Same structure as Saturday Lotto:** 6 from 45, 2 supplementary (since April 2004)
- **3 draws per week:** More data points per year than any other lotto game
- **Fixed Division 1:** $1M for up to 6 winners (no rollover) — eliminates jackpot-size bias in analysis
- **Can be combined with Saturday Lotto** for the same 6/45 analysis, tripling the dataset

**Caveat:** Format changed multiple times (6/40 → 6/44 → 6/45). Only April 2004+ data matches Saturday Lotto format.

**Estimated usable data (2004-2026):** ~3,400+ draws (3/week × 22 years)

### 3. Oz Lotto ⭐ GOOD SECONDARY

**Why it's interesting:**

- **Richer feature space:** 7 numbers from larger pool (47), plus 2-3 supplementary numbers
- **Good history:** ~1,680 draws since February 1994
- **Major format changes** create natural "experiments" — compare patterns pre/post change
  - Phase 1 (1994-2005): 6 from 45 → ~600 draws
  - Phase 2 (2005-2022): 7 from 45 + 2 supp → ~880 draws
  - Phase 3 (2022-present): 7 from 47 + 3 supp → ~200+ draws
- **Higher variance** due to larger number pool and more balls drawn
- **Jackpot rollover dynamics** more interesting (rolls to much larger amounts)

**Best approach:** Focus on Phase 2 data (7/45, 2005-2022) for consistency — 880 draws is still substantial.

### 4. Powerball (Australia)

**Pros:**
- Two-barrel system (7 from 35 + 1 from 20) = interesting dual-dimensional analysis
- 9 divisions = richer prize tier data
- Record $200M jackpot creates interesting jackpot-size dynamics

**Cons:**
- Format changed significantly in April 2018 (6/40 + 1/20 → 7/35 + 1/20)
- Pre-2018: ~1,140 draws in old format
- Post-2018: ~420+ draws in new format
- The two-barrel system makes statistical analysis more complex
- Smaller usable dataset per format

### 5. Set for Life

**Pros:**
- Daily draws since 2013 = ~4,700+ data points (largest raw count!)
- Simple 7 from 44 format with 2 supplementary
- Interesting prize structure ($20K/month for 20 years)

**Cons:**
- Only ~12 years of history (started 2013)
- Relatively new game — less historical depth
- Numbers from 1-44 with 7 drawn + 2 supp = 9 numbers per draw

### 6. Super 66 — Discontinued
Not recommended. Game was discontinued; limited historical data.

### 7. Lucky Lotteries — Not Suitable
Raffle-style game, not pure number draw. Numbers drawn sequentially until jackpot number hit. Not amenable to number-pattern analysis.

### 8. The Pools — Discontinued
Based on soccer match results (converted to numbers). Discontinued around 2013. Not suitable.

### 9. Keno — Not Suitable for Draw Analysis
Continuous draws (every 3.5 minutes), 20 numbers from 80. While the sheer volume of data is enormous, the game structure is fundamentally different — player selects 1-10 numbers and matches against 20 drawn. Not a traditional "pick your numbers" lottery format.

---

## Recommended Approach for ML Experiment

### Primary Recommendation: Saturday Lotto (1985-present)

**Dataset:** ~2,100+ weekly draws, each with 6 main numbers + 2 supplementary from 1-45

**Combined approach:** Merge Saturday Lotto + Weekday Windfall (2004+) for a combined dataset of ~5,500+ draws with identical format (6 from 45, 2 supplementary).

### Secondary Recommendation: Oz Lotto (2005-2022)

**Dataset:** ~880 weekly draws, each with 7 main numbers + 2 supplementary from 1-45

---

## Suggested ML/AI Approaches

### 1. Frequency & Hot/Cold Analysis (Baseline)
- **Method:** Chi-squared tests, z-scores for each number's frequency vs. expected
- **Purpose:** Establish baseline uniformity. Are any numbers statistically "hot" or "cold"?
- **Expected result:** With 2,100+ draws, we'd expect standard deviation of ~17 occurrences per number. Most numbers should be within 2σ. Finding numbers consistently outside this range would be notable.
- **Reality check:** With a fair draw, the Law of Large Numbers says frequencies converge to uniform. Any deviation found would be small and not exploitable after considering ticket cost.

### 2. Gap Analysis (Time Between Appearances)
- **Method:** For each number, calculate the "gap" (draws between appearances). Model as geometric distribution.
- **Purpose:** Do certain numbers cluster or have unusual gap patterns?
- **Expected result:** Gaps should follow a geometric distribution with p ≈ 6/45 = 0.133. Deviations suggest mechanical bias or non-randomness.

### 3. Pair/Triple Frequency Analysis
- **Method:** Count frequency of all C(45,2)=990 pairs and C(45,3)=14,190 triples appearing together
- **Purpose:** Do certain number pairs or triples appear together more than expected?
- **Expected result:** Expected pair frequency = 2,100 × C(6,2)/C(45,2) ≈ 2,100 × 15/990 ≈ 31.8 times. Significant deviations (>2σ ≈ ±11) would be notable.

### 4. LSTM Sequence Prediction
- **Method:** Train LSTM on sequences of past draws to predict next draw
- **Input:** Sequences of past N draws (each draw = 45-dimensional binary vector or 6 number indices)
- **Architecture:** LSTM → Dense → 45-class softmax for each of 6 positions
- **Expected result:** The model should NOT predict better than random — this is the key finding. If it does, that's a significant result worth publishing.
- **Educational value:** Demonstrates that sequence models cannot find patterns in truly random data.

### 5. Anomaly Detection
- **Method:** Isolation Forest, One-Class SVM, or Autoencoder on draw feature vectors
- **Purpose:** Find draws that are statistically anomalous (unusual combinations)
- **Features:** Sum of numbers, range, number of even/odd, number of high/low, consecutive pairs, etc.
- **Expected result:** May find some statistically unusual draws (e.g., all consecutive numbers), which is expected by chance.

### 6. Clustering Analysis
- **Method:** K-Means, DBSCAN on draw feature vectors
- **Purpose:** Do draws cluster into distinct "types"? Are certain draw patterns more common?
- **Expected result:** In uniform random draws, clusters should be roughly equal size with no meaningful structure.

### 7. Autocorrelation & Time Series Analysis
- **Method:** ACF/PACF plots, Ljung-Box test, runs test
- **Purpose:** Test for serial correlation between draws. Does yesterday's draw predict anything about today's?
- **Expected result:** No significant autocorrelation at any lag (each draw is independent).

### 8. Transformer-Based Approach
- **Method:** Self-attention model on sequences of past draws
- **Purpose:** Test whether attention mechanisms can find long-range dependencies in lottery data
- **Architecture:** Embedding → Multi-Head Attention → FFN → Prediction head
- **Expected result:** Should perform no better than random, but the attention patterns could be educational.

---

## Data Sources

### Official Sources
| Source | URL | Data Available |
|--------|-----|---------------|
| The Lott (official) | https://www.thelott.com/tattslotto/results | Recent results, frequency stats |
| Lotterywest (WA) | https://www.lotterywest.wa.gov.au/results | WA results |
| The Lott (Oz Lotto) | https://www.thelott.com/oz-lotto/results | Recent results |
| The Lott (Powerball) | https://www.thelott.com/powerball/results | Recent results |

### Data Collection Strategy
The official sites (thelott.com) are heavily JavaScript-rendered and don't expose historical data via simple web scraping. Options:

1. **Third-party data aggregators:** Sites like lotteryextreme.com, lottoplex, etc. — many are defunct or blocked
2. **Manual CSV compilation:** Use browser automation to scrape historical results from thelott.com page by page
3. **GitHub datasets:** No existing comprehensive Australian lottery datasets found on GitHub/Kaggle
4. **Web scraping approach:** Build a scraper for thelott.com results pages using Playwright/Selenium
5. **API approach:** The Lott may have an undocumented API used by their mobile app — worth investigating

### Recommended Data Collection Method
```python
# Use Playwright to scrape thelott.com results pages
# Saturday Lotto URL pattern:
# https://www.thelott.com/tattslotto/results/[DRAW_NUMBER]
# Or use the results search with date ranges

# Alternative: Build a scraping pipeline for each lottery
# 1. Navigate to results page
# 2. Extract draw number, date, winning numbers, supplementary numbers
# 3. Store as CSV with columns: draw_number, date, n1, n2, n3, n4, n5, n6, supp1, supp2
```

---

## Statistical Feasibility Assessment

### Can ML actually find an edge?

**Short answer: Almost certainly not, and that's the point.**

### Mathematical Reality Check

For Saturday Lotto (6 from 45):
- Total possible combinations: C(45,6) = 8,145,060
- With 2,100 draws in our dataset, we've seen 2,100/8,145,060 ≈ 0.026% of all possible outcomes
- The number space is so large that we're unlikely to see any combination twice
- Each draw is designed to be independent and uniformly random

### What CAN be detected:
1. **Mechanical bias:** If the ball machine has any physical bias (weight differences, temperature effects), frequency analysis could detect it over thousands of draws. This has happened historically in some international lotteries.
2. **Pseudo-random number generator flaws:** If the draw uses PRNG rather than physical balls, mathematical weaknesses could be exploitable.
3. **Operator fraud:** Unusual patterns could indicate manipulation.

### What CANNOT be detected:
1. **Predictive patterns:** Past draws don't influence future draws (independence assumption)
2. **"Due" numbers:** The gambler's fallacy — each number has the same probability every draw
3. **Trends:** No upward/downward trends exist in fair random draws

### The Value of the Experiment
Even though we won't find an exploitable edge, the experiment is valuable because:
1. **Educational:** Demonstrates ML techniques on a well-understood domain
2. **Baseline establishment:** Proves that when data is truly random, ML correctly finds no signal
3. **Method validation:** If your ML pipeline can't beat random on lottery data, that's actually a good validation of the pipeline's integrity
4. **Anomaly detection practice:** Finding the rare statistically unusual draws is a genuine anomaly detection exercise
5. **Publication potential:** "Applying Modern ML to Australian Lottery Data: A Null Result" could be an interesting paper

---

## ROI Analysis (If Patterns Could Be Found)

| Lottery | Cost/Game | Div 1 Prize | Div 1 Odds | Expected Value per $1 |
|---------|-----------|-------------|------------|----------------------|
| Saturday Lotto | $0.96 | $1M (avg share) | 1 in 8.1M | ~$0.12 |
| Weekday Windfall | $0.68 | $1M | 1 in 8.1M | ~$0.18 |
| Oz Lotto | $1.20 | $4M+ (rolls up) | 1 in 62.9M | ~$0.05 |
| Powerball | $1.58 | $5M+ (rolls up) | 1 in 134.5M | ~$0.02 |
| Set for Life | $9.45 (7 days) | $4.8M total | ~1 in 38.6M | ~$0.01 |

**Saturday Lotto has the best expected value** — highest probability of winning relative to ticket cost. If any edge could be found, it would be most exploitable here.

Note: All lotteries have negative expected value (they return ~60% as prizes). No amount of pattern analysis can overcome this house edge without finding a genuine mechanical or algorithmic flaw.

---

## Implementation Roadmap

### Phase 1: Data Collection (1-2 days)
1. Build Playwright scraper for thelott.com
2. Scrape Saturday Lotto results (1985-present, ~2,100 draws)
3. Scrape Weekday Windfall results (2004-present, ~3,400 draws)
4. Store in CSV/SQLite

### Phase 2: Exploratory Analysis (1 day)
1. Frequency analysis + chi-squared tests
2. Gap analysis per number
3. Pair/triple frequency analysis
4. Visualizations (heatmaps, histograms, time series)

### Phase 3: ML Experiments (2-3 days)
1. LSTM sequence prediction (baseline vs. random)
2. Anomaly detection (Isolation Forest, Autoencoder)
3. Clustering (K-Means, DBSCAN)
4. Transformer experiment
5. Autocorrelation analysis

### Phase 4: Analysis & Documentation (1 day)
1. Compare all approaches
2. Document findings (spoiler: all should fail to beat random)
3. Identify any statistically significant anomalies
4. Write up as educational blog post / project

---

## Key Game Format Changes (Critical for Data Normalization)

### Saturday Lotto
| Period | Format | Notes |
|--------|--------|-------|
| 1972-1985 | 6 from 40, 1 supplementary | Original format |
| 1985-present | 6 from 45, 2 supplementary | Current format — **USE THIS** |

### Weekday Windfall (Mon/Wed Lotto)
| Period | Format | Notes |
|--------|--------|-------|
| 1979-1990 | 6 from 40, 1 supplementary | NSW only |
| 1990-2004 | 6 from 44, 2 supplementary | Added 2nd supp |
| 2004-present | 6 from 45, 2 supplementary | Matches Saturday Lotto — **USE THIS** |

### Oz Lotto
| Period | Format | Notes |
|--------|--------|-------|
| 1994-2005 | 6 from 45, 2 supplementary | Same as Saturday Lotto |
| 2005-2022 | 7 from 45, 2 supplementary | Added 7th ball |
| 2022-present | 7 from 47, 3 supplementary | Current format |

### Powerball (Australia)
| Period | Format | Notes |
|--------|--------|-------|
| 1996-2018 | 6 from 40 + 1 from 20 | Original format |
| 2018-present | 7 from 35 + 1 from 20 | Current format |

---

## Conclusion

**Saturday Lotto (1985+) is the clear winner** for ML pattern analysis because:

1. **53 years of history** (1985+ subset is 41 years)
2. **Simplest, most stable format** (6 from 45, unchanged for 41 years)
3. **Largest usable dataset** when combined with Weekday Windfall (~5,500+ draws)
4. **Cleanest data structure** — single barrel, no powerball complexity
5. **Best odds** — most likely to see statistical anomalies with enough data
6. **Best ROI** — if any edge existed, it'd be most exploitable here

The experiment itself is almost certain to produce null results (no exploitable patterns), but that IS the finding. It's a rigorous validation that modern ML techniques correctly identify truly random data as unpredictable.

---

*Research compiled from Wikipedia (Lotteries in Australia), thelott.com, lotterywest.wa.gov.au*
