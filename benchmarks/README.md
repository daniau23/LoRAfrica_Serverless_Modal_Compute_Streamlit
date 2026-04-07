## **Benchmark Metrics Utilised**
Kindly refer to naive and vllm folders for summary of results. Below are the metrics used

### **1. TTFT (Time to First Token)**
Measures the latency of the first response.
$$TTFT = (T_{token\_1} - T_{start}) \times 1000$$
*Unit: ms*

---

### **2. ITL (Inter-Token Latency)**
The time elapsed between two consecutive tokens.
$$ITL_{i} = (T_{token\_i} - T_{token_{i-1}}) \times 1000$$
*Unit: ms*

---

### **3. TPOT (Time Per Output Token)**
The average generation time per token, excluding the prefill (TTFT) phase.
$$TPOT = \frac{E2E - TTFT}{N_{tokens} - 1}$$
*Unit: ms*

---

### **4. E2E (End-to-End Latency)**
The total time from request to the final token.
$$E2E = (T_{end} - T_{start}) \times 1000$$
*Unit: ms*

---

### **5. TPS (Tokens Per Second)**
The overall throughput of the inference engine.
$$TPS = \frac{N_{tokens}}{E2E / 1000}$$
*Unit: tokens/sec*

---

### **Summary Table**
| Metric | Focus | LaTeX Logic |
| --- | --- | --- |
| **TTFT** | Responsiveness | $T_{start} \rightarrow T_{1}$ |
| **ITL** | Smoothness | $T_{n} \rightarrow T_{n+1}$ |
| **TPOT** | Speed | $\text{Avg}(ITL)$ |
| **E2E** | Total Time | $T_{start} \rightarrow T_{end}$ |
| **TPS** | Throughput | $N / \text{sec}$ |