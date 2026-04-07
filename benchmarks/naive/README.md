# **Inference Benchmark Results Interpretation Naive Approach**

## **Overview**
This benchmark evaluates the performance of the Fine-tuned Model across batch sizes: 4, 16, 32, and 64. Metrics include the following;
- Global TPS
- TTFT (Time To First Token)
- TPOT (Time Per Output Token)
- ITL (Inter-Token Latency)
- E2E (End-to-End Latency)

---

## **1. Global TPS (Tokens Per Second)**
| Batch Size | Global TPS |
|------------|-----------|
| 4          | 17.18     |
| 16         | 17.14     |
| 32         | 17.15     |
| 64         | 16.50     |

**Interpretation:**
- Throughput remains nearly constant (~17 tokens/sec) across all batch sizes.
- Slight drop at batch size 64 (16.5 TPS).
- Indicates GPU saturation — increasing batch size does not improve throughput.
- *Under untilization of compute*

---

## **2. TTFT (Time To First Token, ms)**
| Batch | Mean     | Median   | P95      | P99      |
|-------|----------|----------|----------|----------|
| 4     | 1306.01  | 420.95   | 8533.89  | 8744.09  |
| 16    | 5273.29  | 2646.71  | 17867.76 | 18763.96 |
| 32    | 7396.85  | 5847.75  | 23157.50 | 24690.97 |
| 64    | 22182.49 | 23376.35 | 39222.21 | 59003.12 |

**Interpretation:**
- TTFT increases significantly with batch size.
- Median values are lower than mean for smaller batches, indicating skew due to outliers.
- Extremely high P95 and P99 values at *batch 64 indicate severe latency spikes.*
- Larger batches introduce queuing delays and contention for GPU resources.
- System is not optimized for high concurrency.

---

## **3. TPOT (Time Per Output Token, ms)**
| Batch | Mean  | Median | P95   | P99   |
|-------|------|--------|-------|-------|
| 4     | 44.43| 41.87  | 62.21 | 64.18 |
| 16    | 44.19| 42.10  | 53.61 | 64.61 |
| 32    | 44.77| 42.31  | 59.11 | 64.68 |
| 64    | 44.87| 42.40  | 64.81 | 64.99 |

**Interpretation:**
- TPOT remains consistent across all batch sizes.
- Indicates stable per-token generation performance.
- Slight increase in tail latency (P95) at higher batch sizes.
- Once generation starts, token production remains efficient.

---

## **4. ITL (Inter-Token Latency, ms)**
| Batch | Mean  | Median | P95   | P99   |
|-------|-------|--------|-------|-------|
| 4     | 57.90 | 63.02  | 67.26 | 68.25 |
| 16    | 57.39 | 63.37  | 67.44 | 68.69 |
| 32    | 56.40 | 62.87  | 67.73 | 68.74 |
| 64    | 59.42 | 64.13  | 68.10 | 69.01 |

**Interpretation:**
- ITL remains stable across all batch sizes.
- Minimal variation indicates consistent streaming performance.
- Confirms that latency issues are concentrated in TTFT rather than token generation.

---

## 5. E2E (End-to-End Latency, ms)

| Batch | Mean     | Median   | P95      | P99      |
|-------|----------|----------|----------|----------|
| 4     | 1931.48  | 551.98   | 8674.16  | 9341.98  |
| 16    | 5817.38  | 3018.40  | 18114.21 | 19265.36 |
| 32    | 7870.63  | 6218.77  | 23466.47 | 24817.74 |
| 64    | 22902.15 | 23502.29 | 43940.01 | 59194.26 |

**Interpretation:**
- E2E latency increases sharply with batch size.
- *Closely follows TTFT trends, showing initial delay dominates total latency.*
- Large gap between median and mean indicates long-tail latency issues.
- Batch size 64 shows extreme latency spikes, indicating system instability.

---

## Overall Analysis
- **Throughput (TPS):** Saturates at ~17 TPS; increasing batch size does not improve performance. 
- **Token Generation:** TPOT and ITL remain stable, confirming efficient per-token computation.
    - Consistent TPS = predictable throughput
- **Latency:** TTFT and E2E increase significantly with batch size, especially at high percentiles.
  - GPU memory pressure
  - Python threading limitations (Huggingface is not optimised for this)
  - Lack of proper batching/queueing mechanism
- **System Behavior:** Performance degradation at batch size 64 suggests GPU memory pressure, thread contention, and scheduling inefficiencies.

---

## Recommendations
- Optimal batch size: **16–32**
- Avoid batch size 64 due to extreme latency, instability and no throughput gains.
---

## Conclusion
- The system demonstrates stable token generation performance but has scheduling overhead. 
- Increasing batch size does not improve throughput and significantly worsens latency.