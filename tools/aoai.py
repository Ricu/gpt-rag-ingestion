# tools/aoai.py

import os
import time
import logging

import openai
import tiktoken
from azure.identity import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential

class AzureOpenAIClient:
    def __init__(self, document_filename: str = ""):
        # Optional tag for log traceability
        self.document_filename = f"[{document_filename}]" if document_filename else ""

        # Load configuration from environment
        self.endpoint             = os.environ.get("AZURE_OPENAI_ENDPOINT")        # e.g. "https://<your-resource>.openai.azure.com/"
        self.api_version          = os.environ.get("AZURE_OPENAI_API_VERSION")
        self.chat_deployment      = os.environ.get("AZURE_GENERATION_MODEL_DEPLOYMENT")         # deployment name in Azure OpenAI Studio
        self.embedding_deployment = os.environ.get("AZURE_EMBEDDING_MODEL_DEPLOYMENT")

        # Warn if any required var is missing
        for var, val in {
            "AZURE_OPENAI_ENDPOINT": self.endpoint,
            "AZURE_OPENAI_API_VERSION":    self.api_version,
            "AZURE_GENERATION_MODEL_DEPLOYMENT":  self.chat_deployment,
            "AZURE_EMBEDDING_MODEL_DEPLOYMENT": self.embedding_deployment
        }.items():
            if not val:
                logging.warning(f"[aoai]{self.document_filename} {var} is not set")

        # Token limits
        self.max_gpt_tokens       = 128_000
        self.max_embed_tokens     =   8_192

        # Instantiate Azure OpenAI client with AAD token auth
        self.client = openai.AzureOpenAI(
            azure_endpoint          = self.endpoint,
            api_version             = self.api_version,
            api_key                 = os.getenv("AZURE_OPENAI_KEY"),
        )
        logging.debug(f"[aoai]{self.document_filename} AzureOpenAI client initialized with AAD token provider")
        # Token estimator for truncation
        self.token_estimator = GptTokenEstimator()

    def get_completion(
        self,
        prompt: str,
        max_tokens: int = 800,
        retry_after: bool = True
    ) -> str:
        # Truncate prompt if over token limit
        prompt_trunc = self._truncate_input(prompt, self.max_gpt_tokens)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": prompt_trunc}
        ]

        try:
            resp = self.client.chat.completions.create(
                model      = self.chat_deployment,
                messages   = messages,
                max_tokens = max_tokens
            )
            return resp.choices[0].message.content

        except openai.RateLimitError as e:
            # Retry-on-429 if Retry-After header present
            retry_hdr = getattr(e, "headers", {}).get("retry-after")
            if retry_after and retry_hdr:
                try:
                    wait = float(retry_hdr)
                except ValueError:
                    wait = None
                if wait:
                    logging.info(f"[aoai]{self.document_filename} Rate-limited, retrying after {wait}s")
                    time.sleep(wait)
                    return self.get_completion(prompt, max_tokens, retry_after=False)
            logging.error(f"[aoai]{self.document_filename} RateLimitError in get_completion: {e}")
            raise

        except openai.OpenAIError as e:
            logging.error(f"[aoai]{self.document_filename} OpenAIError in get_completion: {e}")
            raise

        except Exception as e:
            logging.error(f"[aoai]{self.document_filename} Unexpected error in get_completion: {e}")
            raise

    def get_embeddings(self, text: str, retry_after: bool = True) -> list:
        text_trunc = self._truncate_input(text, self.max_embed_tokens)

        try:
            resp = self.client.embeddings.create(
                model = self.embedding_deployment,
                input = text_trunc
            )
            return resp.data[0].embedding

        except openai.RateLimitError as e:
            retry_hdr = getattr(e, "headers", {}).get("retry-after")
            if retry_after and retry_hdr:
                try:
                    wait = float(retry_hdr)
                except ValueError:
                    wait = None
                if wait:
                    logging.info(f"[aoai]{self.document_filename} Rate-limited on embeddings, retrying after {wait}s")
                    time.sleep(wait)
                    return self.get_embeddings(text, retry_after=False)
            logging.error(f"[aoai]{self.document_filename} RateLimitError in get_embeddings: {e}")
            raise

        except openai.OpenAIError as e:
            logging.error(f"[aoai]{self.document_filename} OpenAIError in get_embeddings: {e}")
            raise

        except Exception as e:
            logging.error(f"[aoai]{self.document_filename} Unexpected error in get_embeddings: {e}")
            raise

    def _truncate_input(self, text: str, max_tokens: int) -> str:
        count = self.token_estimator.estimate_tokens(text)
        if count <= max_tokens:
            return text

        logging.info(f"[aoai]{self.document_filename} Truncating input from {count} to {max_tokens} tokens")
        step = 1
        truncated = text
        while self.token_estimator.estimate_tokens(truncated) > max_tokens and truncated:
            truncated = truncated[:-step]
            step = min(step * 2, 100)
        return truncated

class GptTokenEstimator:
    """
    Estimates token counts for a specified OpenAI model using tiktoken.
    """
    def __init__(self, model_name: str = "text-embedding-3-large"):
        # encoding_for_model picks the right BPE for the model:
        self.encoding = tiktoken.encoding_for_model(model_name)

    def estimate_tokens(self, text: str) -> int:
        # Exact count of BPE tokens, no fallbacks needed:
        return len(self.encoding.encode(text))