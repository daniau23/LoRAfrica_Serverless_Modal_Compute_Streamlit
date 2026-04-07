# **Inference Benchmark Results Interpretation vLLM vs Naive FastAPI Approach**

## **Overview**
This benchmark evaluates the performance of the Fine-tuned Model using vLLM compared to a naive FastAPI + HuggingFace approach across batch sizes: 4, 16, 32, and 64. Metrics include:

- Global TPS (Tokens Per Second)
- TTFT (Time To First Token)
- TPOT (Time Per Output Token)
- ITL (Inter-Token Latency)
- E2E (End-to-End Latency)

The comparison highlights efficiency and latency differences between an optimized vLLM backend and a naive HuggingFace server setup.

---

## **1. Global TPS (Tokens Per Second)**
| Batch Size | Naive TPS | vLLM TPS (output_throughput) |
|------------|-----------|----------|
| 4          | 17.18     | 212.42   |
| 16         | 17.14     | 707.30   |
| 32         | 17.15     | 1172.94  |
| 64         | 16.50     | 1804.45  |

**Interpretation:**
- vLLM achieves ~10–100× higher throughput than the naive approach across all batch sizes.
- Naive approach (FastAPI + HuggingFace) TPS saturates at ~17 tokens/sec, indicating GPU underutilization and threading bottlenecks, while vLLM scales efficiently with concurrency and batch size, leveraging optimized scheduling and batching.
- Increasing batch size in the naive approach does not improve throughput, while vLLM shows near-linear gains up to batch 64.

---

## **2. TTFT (Time To First Token, ms)**
| Batch | Naive Mean | vLLM Mean | Naive Median | vLLM Median | Naive P95 | vLLM P95 | Naive P99 | vLLM P99 |
|-------|------------|-----------|--------------|-------------|-----------|-----------|-----------|-----------|
| 4     | 1306.01    | 62.19     | 420.95       | 62.77       | 8533.89   | 67.57     | 8744.09   | 72.30     |
| 16    | 5273.29    | 71.41     | 2646.71      | 65.64       | 17867.76  | 105.55    | 18763.96  | 107.25    |
| 32    | 7396.85    | 92.39     | 5847.75      | 92.25       | 23157.50  | 121.94    | 24690.97  | 125.02    |
| 64    | 22182.49   | 157.05    | 23376.35     | 179.74      | 39222.21  | 210.91    | 59003.12  | 211.92    |

**Interpretation:**
- Naive approach suffers from extreme TTFT at high batch sizes; vLLM maintains low and predictable TTFT.
- Median vs mean in the naive approach shows a long-tail distribution, especially at batch 64.
- vLLM reduces queuing and thread contention delays with its optimized streaming and batching.
- Initial token generation dominates latency in the naive approach, while vLLM delivers almost immediate response.

---

## **3. TPOT (Time Per Output Token, ms)**
| Batch | Naive Mean | vLLM Mean | Naive Median | vLLM Median | Naive P95 | vLLM P95 | Naive P99 | vLLM P99 |
|-------|------------|-----------|--------------|-------------|-----------|-----------|-----------|-----------|
| 4     | 44.43      | 17.76     | 41.87        | 17.78       | 62.21     | 17.95     | 64.18     | 17.98     |
| 16    | 44.19      | 19.03     | 42.10        | 19.14       | 53.61     | 19.37     | 64.61     | 19.45     |
| 32    | 44.77      | 20.25     | 42.31        | 20.39       | 59.11     | 20.83     | 64.68     | 20.98     |
| 64    | 44.87      | 22.50     | 42.40        | 22.65       | 64.81     | 23.39     | 64.99     | 23.60     |

**Interpretation:**
- TPOT is consistently lower for vLLM, showing faster per-token generation.
- Naive FastAPI achieves stable TPOT, but much higher than vLLM, indicating slower token streaming and computation.
- Slight increase at P95 and P99 in vLLM at higher batch sizes.

---

## **4. ITL (Inter-Token Latency, ms)**
| Batch | Naive Mean | vLLM Mean | Naive Median | vLLM Median | Naive P95 | vLLM P95 | Naive P99 | vLLM P99 |
|-------|------------|-----------|--------------|-------------|-----------|-----------|-----------|-----------|
| 4     | 57.90      | 17.77     | 63.02        | 17.49       | 67.26     | 21.83     | 68.25     | 30.03     |
| 16    | 57.39      | 19.04     | 63.37        | 18.33       | 67.44     | 27.55     | 68.69     | 30.81     |
| 32    | 56.40      | 20.23     | 62.87        | 19.63       | 67.73     | 27.67     | 68.74     | 32.58     |
| 64    | 59.42      | 22.43     | 64.13        | 22.21       | 68.10     | 28.87     | 69.01     | 38.08     |

**Interpretation:**
- vLLM shows much lower ITL compared to naive, confirming faster streaming and token delivery.
- Naive approach has stable ITL, but slower and less scalable.
- Confirms naive latency issues are concentrated in TTFT/E2E rather than per-token computation.

---

## **5. E2E (End-to-End Latency, ms)**
| Batch | Naive Mean | vLLM Mean | Naive Median | vLLM Median | Naive P95 | vLLM P95 | Naive P99 | vLLM P99 |
|-------|------------|-----------|--------------|-------------|-----------|-----------|-----------|-----------|
| 4     | 1931.48    | 1536.84   | 551.98       | 1538.78     | 8674.16   | 1557.75   | 9341.98   | 1565.19   |
| 16    | 5817.38    | 1650.05   | 3018.40      | 1653.50     | 18114.21  | 1712.05   | 19265.36  | 1720.17   |
| 32    | 7870.63    | 1806.79   | 6218.77      | 1818.53     | 23466.47  | 1884.95   | 24817.74  | 1901.24   |
| 64    | 22902.15   | 2030.43   | 23502.29     | 2065.39     | 43940.01  | 2157.93   | 59194.26  | 2177.12   |

**Interpretation:**
- vLLM significantly reduces E2E latency compared to naive, especially at high batch sizes.
- Naive approach exhibits huge spikes at P95/P99 due to GPU contention, Python threading overhead, and lack of efficient batching.
- vLLM shows low tail latency, making it much more predictable and scalable.

---

## **Overall Analysis**
- **Throughput:** vLLM outperforms naive FastAPI by ~10–100×, scaling efficiently with batch size and concurrency.
- **Token Generation:** TPOT and ITL are much lower and stable in vLLM.
- **Latency:** TTFT and E2E are dramatically reduced in vLLM; naive FastAPI suffers long-tail spikes.
- **System Behavior:**  
  - Naive approach is bottlenecked by Python threading, HuggingFace generation inefficiencies, and GPU underutilization.  
  - vLLM optimizes scheduling, streaming, and batching for high concurrency.

---

## **Recommendations**
- Use **vLLM** for high-throughput, low-latency inference.
- Optimal naive batch size is probably around **16** if constrained to FastAPI.
- Avoid naive batch size 64: extreme latency, low TPS, and unpredictable performance.

---

## **Conclusion**
- Naive (FastAPI + HuggingFace) works for small-scale experiments but is inefficient and unscalable.
- vLLM delivers high throughput, low latency, and consistent token streaming, suitable for production inference workloads.