import time
import torch
import statistics
import threading
from fastapi import FastAPI
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from peft import PeftModel

# =========================
# CLEAR CAHCE BEFORE STARTING
# =========================
torch.cuda.empty_cache()

# =========================
# GLOBAL LOCK FOR THREAD SAFETY
# =========================
model_lock = threading.Lock()

# =========================
# MODEL & SYSTEM CONFIGURATION
# =========================
BASE_MODEL_ID = "microsoft/Phi-4-mini-instruct"
LORA_ADAPTER_ID = "DannyAI/phi4_african_history_lora_ds2_axolotl"
SYSTEM_PROMPT = "You are a helpful AI assistant specialised in African history which gives concise answers to questions asked."

DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32


# =========================
# TOKENIZER
# =========================
tokeniser = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
if tokeniser.pad_token is None:
    tokeniser.pad_token = tokeniser.eos_token

# =========================
# BASE MODEL + LoRA
# =========================
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    torch_dtype=DTYPE,
    device_map="auto"
)

model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_ID)
model.eval()

# =========================
# FASTAPI
# =========================
app = FastAPI(title="LLM FastAPI Benchmark Server", version="1.0")

# =========================
# TEST PROMPTS
# =========================
TESTING_PROMPTS = [
    "Briefly detail the significance story of the Ogun Yoruba god",
    "Explain the significance of the Great Zimbabwe ruins.",
    "Describe the impact of the Ashanti Empire on West African trade.",
    "What was the role of the Kingdom of Aksum in early Christianity?",
    "Detail the leadership of Queen Amina of Zazzau."
]

# =========================
# DATA SCHEMAS
# =========================
class MetricsStats(BaseModel):
    mean: float
    median: float
    p95: float
    p99: float

class FullBenchmarkReport(BaseModel):
    ttft: MetricsStats # Time to First Token
    itl: MetricsStats # Inter-token Latency
    e2e: MetricsStats # End-to-End Latency
    tpot: MetricsStats # Time Per Output Token
    global_tps: float # Single efficiency value per batch size

class BenchmarkRequest(BaseModel):
    input_tokens: int
    generated_tokens: int
    num_prompts: int
    batch_size: int
    warmup_counts: int = 10

# =========================
#  MEASUREMENT ENGINE/UTILS
# =========================
# Define function for calculating 
# distribution metrics (mean, median, p95, p99)
def _calculate_distribution(values):
    """Calculate mean, median, p95, p99 for a list of values.
    Args:
    values (list[float]): List of latency values in milliseconds."""
    # Calculate mean, median, p95, p99
    if not values:
        return MetricsStats(mean=0, median=0, p95=0, p99=0)
    # Sort values for percentile calculations
    values = sorted(values)
    n = len(values)
    return MetricsStats(
        mean=round(statistics.mean(values), 3),
        median=round(statistics.median(values), 3),
        p95=round(values[int(0.95*n)-1],3),
        p99=round(values[int(0.99*n)-1],3)
    )

# =========================
# SAFE STREAMER
# =========================
# Set up the streamer to capture generated tokens and their timestamps
class SafeStreamer(TextIteratorStreamer):
    def put(self, next_tokens):
        # clamp token IDs to valid range
        next_tokens = next_tokens.clamp(0, self.tokenizer.vocab_size - 1)
        super().put(next_tokens)

# =========================
# SINGLE RUN MEASURE
# =========================
def _measure_once(input_tokens: int, generated_tokens: int, idx: int = 0):
    # Prepare prompt using modulus to cycle through testing prompts
    # 0-4 for 5 prompts, idx is incremented 
    # in the main loop to ensure variety in prompts across measurements
    # Example 0 % 5 = 0 -> prompt 0, 1 % 5 = 1 -> 
    # prompt 1, ..., 5 % 5 = 0 -> prompt 0 again
    base_q = TESTING_PROMPTS[idx % len(TESTING_PROMPTS)]
    # numeric padding
    input_ids = tokeniser(base_q, return_tensors="pt").input_ids
    pad_count = max(0, input_tokens - input_ids.shape[1])
    if pad_count > 0:
        pad_ids = torch.full((1, pad_count), tokeniser.pad_token_id, dtype=torch.long)
        input_ids = torch.cat([input_ids, pad_ids], dim=1)
    inputs = {"input_ids": input_ids.to(model.device)}

    # Set up the streamer to capture generated tokens and their timestamps
    streamer = SafeStreamer(tokeniser, skip_prompt=True, skip_special_tokens=True)

    gen_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=generated_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        top_k=50,
        repetition_penalty=1.1,
        use_cache=True
        # use_cache=False
    )
    # Synchronize CUDA before starting the timer 
    # to ensure accurate measurement
    if torch.cuda.is_available(): torch.cuda.synchronize()
    start_req = time.perf_counter()

    first_token_time = None
    token_times = []

    # thread-safe generation
    def run_generation():
        with model_lock:
            with torch.no_grad():
                model.generate(**gen_kwargs)

    thread = threading.Thread(target=run_generation)
    thread.start()

    # Capture the time when each token is generated
    for _ in streamer:
        now = time.perf_counter()
        # Record the time of the first token to calculate TTFT
        if first_token_time is None: first_token_time = now
        # Record the time of each generated token for 
        # ITL and E2E calculations
        token_times.append(now)

    # Ensure generation thread has completed before stopping the timer
    thread.join()
    if torch.cuda.is_available(): torch.cuda.synchronize()
    end_req = time.perf_counter()

    actual_tokens = len(token_times)
    total_sec = end_req - start_req
    # if the first_token_time is None, it means no tokens were generated,
    # but if tokens were generated, we calculate TTFT as the time
    # from request start to first token generation
    ttft_ms = (first_token_time - start_req) * 1000 if first_token_time else 0
    # E2E is calculated as the total time from 
    # request start to the generation of the last token
    e2e_ms = (total_sec) * 1000
    # TPOT is calculated as the average time per token after the first token
    # TPOT = (total generation time - TTFT) / (tokens - 1)
    tpot_ms = (e2e_ms - ttft_ms) / (actual_tokens - 1) if actual_tokens > 0 else 0
    # ITL is calculated as the time between each token generation
    itl_ms = [(token_times[i] - token_times[i-1])*1000 for i in range(1, len(token_times))] if len(token_times)>1 else [0]

    return ttft_ms, itl_ms, e2e_ms, tpot_ms, actual_tokens

# =========================
# BENCHMARK ENDPOINT
# =========================
@app.post("/benchmarks", response_model=FullBenchmarkReport)
def measure_endpoint(req: BenchmarkRequest):
    # Warm up the model with a few generations
    #  to ensure more stable measurements
    for i in range(req.warmup_counts):
        _measure_once(req.input_tokens, min(32, req.generated_tokens), i)

    # Lists to store metrics for all prompts
    all_ttft, all_itl, all_e2e, all_tpot = [], [], [], []
    total_tokens_generated = 0
    
    # Start global timer for TPS calculation
    if torch.cuda.is_available(): torch.cuda.synchronize()
    bench_start_time = time.perf_counter()

    num_batches = (req.num_prompts + req.batch_size - 1) // req.batch_size
    remaining = req.num_prompts

    # Process prompts in batches to simulate 
    # real-world usage and measure efficiency
    for _ in range(num_batches):
        current_bs = min(req.batch_size, remaining)
        # We use ThreadPoolExecutor to run multiple generation tasks in parallel
        # Example: if batch_size is 4, we will run 4 generation tasks 
        # simultaneously, each with potentially different prompts 
        # due to the cycling mechanism in _measure_once
        with ThreadPoolExecutor(max_workers=current_bs) as executor:
            futures = [
                executor.submit(_measure_once, req.input_tokens, req.generated_tokens, i)
                for i in range(current_bs)
            ]
            for f in futures:
                # Wait for each task to complete and collect metrics
                ttft, itl, e2e, tpot, token_count = f.result()
                all_ttft.append(ttft)
                all_itl.extend(itl)
                all_e2e.append(e2e)
                all_tpot.append(tpot)
                total_tokens_generated += token_count
        # Update remaining prompts after processing the batch
        # Example: if num_prompts is 10 and batch_size is 4, after the first batch,
        # we will have 6 remaining prompts to process in the next batch
        remaining -= current_bs

    # End global timer after all batches are processed
    if torch.cuda.is_available(): torch.cuda.synchronize()
    bench_end_time = time.perf_counter()

    # Global TPS is calculated as 
    # total tokens generated divided by total time taken for all batches
    total_wall_time = bench_end_time - bench_start_time
    global_tps = total_tokens_generated / total_wall_time if total_wall_time > 0 else 0

    # Calculate distribution metrics 
    # for TTFT, ITL, E2E, TPS, and TPOT using the helper function
    return FullBenchmarkReport(
        ttft=_calculate_distribution(all_ttft),
        itl=_calculate_distribution(all_itl),
        e2e=_calculate_distribution(all_e2e),
        tpot=_calculate_distribution(all_tpot),
        global_tps=round(global_tps,2)  # Just the float, no distribution needed
    )

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    import uvicorn
    print("--- STARTING BENCHMARK SERVER ON PORT 7860 ---")
    uvicorn.run(app, host="0.0.0.0", port=7860)