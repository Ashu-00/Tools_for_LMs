# Define embedding model and function to create embeddings
from sentence_transformers import SentenceTransformer

class embeddingmodel:
    def __init__(self):
        """initializes the embedding model"""
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_dim  = self.model.get_sentence_embedding_dimension()

    def create_embeddings(self, texts):
        """returns a list of embeddings for the given texts"""
        embeddings = self.model.encode(texts)
        return embeddings
