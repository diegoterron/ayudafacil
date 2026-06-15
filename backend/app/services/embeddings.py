from typing import List
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.provider = settings.PROVIDER.lower()
        
        if self.provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            if not settings.OPENAI_API_KEY:
                raise ValueError("Se seleccionó el proveedor OpenAI pero la API Key no está configurada.")
            self.model = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_EMBED_MODEL
            )
        else:
            from langchain_ollama import OllamaEmbeddings
            self.model = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBED_MODEL
            )

    def get_embedding(self, text: str) -> List[float]:
        cleaned_text = text.replace("\n", " ").strip()
        return self.model.embed_query(cleaned_text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
        return self.model.embed_documents(cleaned_texts)

embedding_service = EmbeddingService()
