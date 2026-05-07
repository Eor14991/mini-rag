from abc import ABC, abstractmethod


class LLMInterFace(ABC):

    @abstractmethod
    def get_generation_model(self, model_id: str):
        ...

    @abstractmethod
    def get_embedding_model(self, model_id: str,  embedding_size: int):
        ...

    @abstractmethod
    def generate_text(self, prompt: str, max_output_token: int,
                      temperature: float = None) -> str:
        ...

    @abstractmethod
    def embed_text(self, text: str, document_type: str):
        ...

    def construct_prompt(self, prompt: str, role: str) -> str:
        ...

