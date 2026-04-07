import uuid 
import modal
from sse_starlette.sse import EventSourceResponse
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from langsmith import Client
import os
import json 
import re
import copy

# Relevant Links
# https://pypi.org/project/presidio-anonymizer/#description
# https://pypi.org/project/presidio-analyzer/#description
# https://docs.litellm.ai/
# https://docs.litellm.ai/docs/proxy/config_settings

# Regex patterns (fast layer)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3})?[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
# ADDED: Specific patterns for PPSN, Irish Zip codes, and Passport numbers
# PPSN_PATTERN = re.compile(r'\b\d{7}[A-Z]{1,2}\b', re.IGNORECASE)
PPSN_PATTERN = re.compile(r'\b\d{7}[a-z]{1,2}\b', re.IGNORECASE) # a more greedy approach
ZIP_EIR_PATTERN = re.compile(r'\b[A-Z][0-9][0-9W][ ]?[0-9A-Z]{4}\b', re.IGNORECASE)
# Updated Irish Passport Regex (generic approach for passport wasnt't working)
# Different countries have different patterns
PASSPORT_PATTERN = re.compile(r'\b[PL][A-Z]\d{7}\b', re.IGNORECASE)

# Load needed configuration
BASE_MODEL_ID = "microsoft/Phi-4-mini-instruct"
LORA_MODEL_ID = "DannyAI/phi4_african_history_lora_ds2_axolotl"
SYSTEM_PROMPT = "You are a helpful AI assistant specialised in African history which gives concise answers to questions asked."
# Define the Modal app and image with necessary dependencies
app = modal.App(
    "LoRAfrica-Modal-Inference",
    tags={
    "Inference-model":"LoRAfrica-Modal-Inference-testing",
    "base_model": "Phi-4-mini-instruct",
    "lora_model": "phi4_african_history_lora_ds2_axolotl"
    }    
)

# Container Image
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "vllm==0.14.1", 
    "transformers", 
    "sse-starlette",
    "langsmith==0.3.42",
    "presidio-analyzer==2.2.362", # For masking PIIs
    "presidio-anonymizer==2.2.362" # For masking PIIs
# Run needed commands to install Spacy for the masking of PII (Personal Indentifible information for LangSmith Traces)
).run_commands(
    "python -m spacy download en_core_web_sm"
)
# Use a shared volume to cache models across containers
volume = modal.Volume.from_name("llm-models", create_if_missing=True)


@app.cls(
    gpu=["L4","T4:2"],# Use L4 for base model and T4 for LoRA to save costs
    image=image,# Add the vLLM image with necessary dependencies
    volumes={"/models": volume},# Add a shared volume for model caching
    secrets =[modal.Secret.from_name("huggingface-secret"),
              modal.Secret.from_name("langsmith-secret")
              ],# Add your Hugging Face token as a secret
    container_idle_timeout=200, # 300  is 5 minutes
    allow_concurrent_inputs=100, # Allow up to 100 concurrent requests
    max_containers=10, # Limit to 10 containers to control costs
    min_containers=0, # Scale down to 0 when idle
    scaledown_window=10 # Scale down after 10 seconds of idleness
)
class Model:
    @modal.enter()
    def load(self):
        # Load the base model with vLLM and prepare the LoRA request configuration
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine
        from vllm.lora.request import LoRARequest
        from transformers import AutoTokenizer
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine 
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # # Debug (optional – remove later)
        # print("LangSmith tracing:", os.getenv("LANGSMITH_TRACING"))

        # Load the base model with vLLM
        engine_args = AsyncEngineArgs(
            model=BASE_MODEL_ID,
            download_dir="/models",
            gpu_memory_utilization=0.9,
            enable_lora=True,
            max_loras=1, # Only load one LoRA adapter to save GPU memory
            max_lora_rank=64, # Use a smaller rank for the LoRA adapter to save memory
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

        # Prepare the LoRA request configuration
        self.lora_request = LoRARequest(
            lora_name="adapter",
            lora_int_id=1, # Use a fixed integer ID for the LoRA adapter
            lora_path=LORA_MODEL_ID,
        )
        volume.commit()


    
    # Safe helper so tracing NEVER breaks generation
    def _get_run(self):
        try:
            return get_current_run_tree()
        except Exception:
            return None
    
    
    # Regular Expressions for anonymisation
    def regex_anonymize(self,text: str) -> tuple[str, bool]:
        original_text = text
        text = EMAIL_PATTERN.sub("[EMAIL]", text)
        text = PHONE_PATTERN.sub("[PHONE]", text)
        text = CREDIT_CARD_PATTERN.sub("[CREDIT_CARD]", text)
        text = SSN_PATTERN.sub("[SSN]", text)
        # ADDED: Irish/Passport specifics
        text = PPSN_PATTERN.sub("[PPSN]", text)
        text = ZIP_EIR_PATTERN.sub("[ZIPCODE]", text)
        text = PASSPORT_PATTERN.sub("[PASSPORT]", text)
        return text, text != original_text

    # Using NLP approach via entities
    def presidio_anonymize(self,text: str) -> str:
        results = self.analyzer.analyze(text=text, 
                entities=[
                "PERSON", "LOCATION", 
                "ORGANIZATION", "PASSPORT","PPSN", 
                "ADDRESS", "ZIPCODE","EIRCODE"
                ], 
                language="en")
        if not results:
            return text
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text
    
    
    # Anonymisation of inputs
    def hybrid_anonymize_text(self,text: str) -> str:
        """Optimized hybrid anonymization for strings"""
        text, _ = self.regex_anonymize(text)
        # MODIFIED: Always run Presidio to ensure Names/Locations are caught
        text = self.presidio_anonymize(text)
        return text

    # Hybridisation of Data Anonymisation
    def hybrid_anonymize_data(self, data):
        """LangSmith-compatible anonymizer for dict messages"""
        # MODIFIED: Use copy to avoid redacting model inputs in-place
        scrubbed_data = copy.deepcopy(data)
        try:
            message_list = scrubbed_data.get("messages") or [scrubbed_data.get("choices", [{}])[0].get("message")]
            if not message_list:
                return scrubbed_data
            for message in message_list:
                if isinstance(message, dict) and "content" in message:
                    content = message.get("content", "")
                    if content:
                        message["content"] = self.hybrid_anonymize_text(content)
        except Exception as e:
            print(f"Anonymization error: {e}")
        return scrubbed_data

    # Strict-mode helper
    def anonymize_messages(self,messages):
        for msg in messages:
            if "content" in msg:
                msg["content"] = self.hybrid_anonymize_text(msg["content"])
        return messages


    # LangSmith Client for  Controlling Traces and Implementing Customised Redaction
    langsmith_client = Client(
    hide_inputs=hybrid_anonymize_data,
    hide_outputs=hybrid_anonymize_data
    )

    # Normalise input (LiteLLM + legacy support)
    def _normalise_messages(self,request):
        if "messages" in request:
            messages = request["messages"]

            if not messages or messages[0]["role"] != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                })
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request["prompt"]}
            ]

        return messages
    
    # Log Non streaming
    @traceable(
        name="Modal Non-Stream Trace", 
        run_type='llm',
        metadata={"environment":"testing"}, # for testing
        # metadata={"environment":"production"}, # for production
        tags=["Generate-tag"] 
    ) # Tags will we generated when method is called
    async def _generate(
        self,
        messages: list[dict],
        max_tokens: int = 128,
        temperature: float = 0.1,
        use_lora: bool = False,
    ) -> str:
        from vllm import SamplingParams

        # Prepare the prompt using the tokenizer's chat template
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        run = self._get_run() 

        # We log scrubbed data to LangSmith
        anonymized_messages = self.hybrid_anonymize_data({"messages": copy.deepcopy(messages)})["messages"]
        anonymized_prompt = self.hybrid_anonymize_text(prompt)

        # LangSmith Log Inputs with anonymised data
        if run:
            run.inputs = {
                "messages": anonymized_messages,
                "prompt": anonymized_prompt,
                "use_lora": use_lora,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Tags Generated for further logging
            run.tags = run.tags or []
            run.tags.append('lora' if use_lora else "base")
            run.tags.append('long-gen' if max_tokens > 50 else "short-gen")

            # Log max tokens as event
            run.add_event(
                {
                    "name":"max_tokens",
                    "value":max_tokens,
                    "tags": ["config", "generation"]
                }
            )

        request_id = str(uuid.uuid4()) # Request ID 
        # Set up sampling parameters for generation
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            # Optional: Adjust top_p if desired.
            # Might make this available for client side for users or limit it to .80 or .90,
            # while maintaining temperature which is needed for accuracy
            top_p=0.9, 
            seed=42
            # vllm handles this internally, but you can adjust parameters like top_p or stop tokens as needed            
            # stop=[""] # Stop generation when the end-of-sequence token is generated
        )

        # Generate the response using vLLM, applying the LoRA adapter 
        # if requested
        lora_request = self.lora_request if use_lora else None
        results = self.engine.generate(
            prompt,
            sampling_params=sampling_params,
            request_id=request_id,
            # Will use LoRAfrica if lora_request is TRUE
            lora_request=lora_request
        )
        async for result in results:
            final = result

        # Anonymise and the redacted output text from the Model
        output_text = final.outputs[0].text
        redacted_output = self.hybrid_anonymize_text(output_text)
        # Log output
        if run:
            run.outputs = {"response": redacted_output}

        return output_text,prompt
    
    # Log streaming
    @traceable(name="Modal Streaming Trace", 
               run_type='llm',
        metadata={
        "environment":"testing"
    },
    tags=["Generate-stream"]
    )
    async def _generate_stream(
        self,
        messages: list[dict],
        max_tokens: int = 128,
        temperature: float = 0.1,
        use_lora: bool = False
    ):
        from vllm import SamplingParams

        # Prepare the prompt using the tokenizer's chat template
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        run = self._get_run()
        
        # We log scrubbed data to LangSmith
        anonymized_messages = self.hybrid_anonymize_data(
                                {"messages": copy.deepcopy(messages)}
                                )["messages"]
        anonymized_prompt = self.hybrid_anonymize_text(prompt)

        # LangSmith Log Inputs
        if run:
            run.inputs = {
                "messages":anonymized_messages,
                "prompt":anonymized_prompt,
                "use_lora": use_lora
            }

            # Tags
            run.tags = run.tags or []
            run.tags.append('lora' if use_lora else "base")
            run.tags.append('long-gen' if max_tokens > 50 else "short-gen")

            # Log max tokens as event
            run.add_event(
                {
                    "name":"max_tokens",
                    "value":max_tokens,
                    "tags": ["config", "generation"]
                }
            )

        request_id = str(uuid.uuid4()) # Request ID 
        # Set up sampling parameters for generation
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            seed=42,
            # Optional: Adjust top_p if desired.
            # Might make this available for client side for users or limit it to .80 or .90,
            # while maintaining temperature which is needed for accuracy
            top_p=0.9, 
            # vllm handles this internally, but you can adjust parameters like top_p or stop tokens as needed            
            # stop=[""] # Stop generation when the end-of-sequence token is generated
        )

        # Generate the response using vLLM, applying the LoRA adapter if requested
        lora_request = self.lora_request if use_lora else None
        results = self.engine.generate(
            prompt,
            sampling_params=sampling_params,
            request_id=request_id,
            # Will use LoRAfrica if lora_request is TRUE
            lora_request=lora_request
        )

        # Stream the generated tokens as they are produced
        previous_text = ""
        async for result in results:
            current_text = result.outputs[0].text
            new_text = current_text[len(previous_text) :]
            previous_text = current_text
            if new_text:
                # Anonymize chunk for streaming event trace
                scrubbed_chunk = self.hybrid_anonymize_text(new_text)
                if run:
                    run.add_event({"name": "token", "value": scrubbed_chunk})
                
                # Note: We send the real 'new_text' to the user, but LangSmith events see 'scrubbed_chunk'
                yield {"choices":[{"delta":{"content": new_text}, "index": 0}]}
        
        if run:
            # Log scrubbed data
            run.outputs = {"response": self.hybrid_anonymize_text(previous_text)}

    # Main Model endpoint
    @modal.web_endpoint(method="POST", label="v1")
    @traceable(
    name="Chat Endpoint",
    run_type = 'chain',
    metadata={
        "environment":"testing-litellm"
    },
    tags=["Generate-model"]
    )
    async def chat(self, request:dict) -> dict:
    # async def v1_chat_completions(self, request:dict) -> dict:
        messages = self._normalise_messages(request)
        # Only for logging
        max_tokens = request.get("max_tokens", 128)
        temperature = request.get("temperature", 0.1)
        use_lora = request.get("use_lora", True)
        stream = request.get("stream", False)


        # STREAMING RESPONSE
        if stream:
            async def event_generator():
                try:
                    async for chunk in self._generate_stream(
                        messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        use_lora=use_lora,
                    ):
                        yield {"data": json.dumps(chunk)}

                except Exception as e:
                    print(f"Error during generation: {e}")

                finally:
                    yield {"data": "[DONE]"}

            return EventSourceResponse(event_generator())
        
        # NORMAL RESPONSE
        response_text,prompt_text = await self._generate(
            messages, max_tokens=max_tokens, 
            temperature=temperature, 
            use_lora=use_lora
        )


        # Getting the count fo tokens used so the generation
        prompt_tokens = len(self.tokenizer(prompt_text)["input_ids"])
        completion_tokens = len(self.tokenizer(response_text)["input_ids"])
        total_tokens = prompt_tokens + completion_tokens
        # or 
        # prompt_tokens = len(prompt_text.split())
        # completion_tokens = len(response_text.split())
        # total_tokens = prompt_tokens + completion_tokens
        
        # OpenAI response format
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object":"chat.completion",
            "choices":[
                {
                    "index": 0,
                    "message":{
                        "role":"assistant",
                        "content": response_text,
                    },
                    "finish_reason":"stop",
                }
            ],
            "usage":{
                "prompt_tokens":prompt_tokens,
                "completion_tokens":completion_tokens,
                "total_tokens":total_tokens,
            }
        }