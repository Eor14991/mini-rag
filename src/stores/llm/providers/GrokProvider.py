from abc import ABC
from ..LLMInterFace import LLMInterFace
from ..LLMEnums import GrokAIEnums
from openai import OpenAI
import logging
from sentence_transformers import SentenceTransformer


class GrokProvider(LLMInterFace):
    def __init__(self, api_key: str, api_url: str = "https://api.x.ai/v1",
                 default_input_max_characters: int = 2048,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1):

        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_model = None
        self.embedding_size = None

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

        self.logger = logging.getLogger(__name__)

    def get_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def get_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        try:
            self.logger.info(f"Loading local HuggingFace embedding model: {model_id}...")
            self.embedding_model = SentenceTransformer(self.embedding_model_id)
            self.logger.info("Model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load HuggingFace model {model_id}: {str(e)}")

    def generate_text(self, prompt: str, chat_history: list = None, max_output_tokens: int = None,
                      temperature: float = None):

        if chat_history is None:
            chat_history = []

        if not self.client:
            self.logger.error("Grok client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for Grok was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt, role=GrokAIEnums.USER.value)
        )

        try:
            response = self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature
            )

            if not response or not getattr(response, 'choices', None) or not getattr(response.choices[0], 'message',
                                                                                     None):
                self.logger.error("Error while generating text with Grok")
                return None

            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Grok API Error: {str(e)}")
            return None

    def _process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def embed_text(self, text: str, document_type: str = None):
        if not self.embedding_model:
            self.logger.error("Embedding model for HuggingFace was not set or failed to load")
            return None

        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error while embedding text with HuggingFace: {str(e)}")
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self._process_text(prompt)
        }