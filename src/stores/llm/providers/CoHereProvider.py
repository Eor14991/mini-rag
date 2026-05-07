from abc import ABC
import logging
from sentence_transformers import SentenceTransformer

# Assuming these are your base interface and enums
from ..LLMInterFace import LLMInterFace
from ..LLMEnums import CoHereEnums, DocumentTypeEnum


class CoHereProvider(LLMInterFace):
    def __init__(self, api_key: str,
                 default_input_max_characters: int = 2048,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1):

        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        # This will hold the local SentenceTransformer model
        self.local_embedding_model = None

        # client remains for Generation (Command-R)
        import cohere
        self.client = cohere.ClientV2(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    def get_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def get_embedding_model(self, model_id: str, embedding_size: int):
        """
        Loads the local HuggingFace model via sentence-transformers.
        model_id: e.g., "BAAI/bge-m3"
        """
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        try:
            self.logger.info(f"Loading local embedding model: {model_id}...")
            self.local_embedding_model = SentenceTransformer(model_id)
            self.logger.info("Local model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load local model {model_id}: {str(e)}")

    def generate_text(self, prompt: str, chat_history: list = None, max_output_tokens: int = None,
                      temperature: float = None):

        if chat_history is None:
            chat_history = []

        if not self.client:
            self.logger.error("Cohere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt, role=CoHereEnums.USER.value)
        )

        try:
            response = self.client.chat(
                model=self.generation_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature
            )

            if not response or not getattr(response, 'message', None) or not getattr(response.message, 'content', None):
                self.logger.error("Error while generating text")
                return None

            return response.message.content[0].text
        except Exception as e:
            self.logger.error(f"Generation API Error: {str(e)}")
            return None

    def _process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def embed_text(self, text: str, document_type: DocumentTypeEnum = DocumentTypeEnum.DOCUMENT):
        """
        Uses the local sentence-transformers model for embedding.
        """
        if not self.local_embedding_model:
            self.logger.error("Local embedding model is not loaded.")
            return None

        try:
            # Generate embedding locally
            embedding = self.local_embedding_model.encode(text)

            # Convert numpy array to list
            result = embedding.tolist()

            # Enforce size constraints if specified
            if self.embedding_size and len(result) > self.embedding_size:
                result = result[:self.embedding_size]

            return result

        except Exception as e:
            self.logger.error(f"Local Embedding Error: {str(e)}")
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self._process_text(prompt)
        }