#Function(s) to create a vector database
import faiss
from Tools_for_LMs.core.vector_db.embedding import embeddingmodel

class VectorDB:
    def __init__(self, vector_dim, index_type):
        """initializes the vector database"""
        self.vector_dim = vector_dim
        self.index_type = index_type
        self.index = None
        self.embeddingmodel = embeddingmodel()
    
    def create_vector_db(self, chunks):
        """creates a vector database from the given texts"""
        embeddings = self.embeddingmodel.create_embeddings(chunks)
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.index.add(embeddings)
        return self.index
    
    def save_vector_db(self, filename):
        """saves the vector database to a file"""
        faiss.write_index(self.index, "./"+filename)
    
    def load_vector_db(self, filename):
        """loads the vector database from a file"""
        self.index = faiss.read_index(filename)
        
    def search_vector_db(self, query, k):
        """searches the vector database for the given query and returns the top k results"""
        query_embedding = self.embeddingmodel.create_embeddings([query])
        distances, indices = self.index.search(query_embedding, k)
        return distances, indices

    def add_texts_to_vector_db(self, chunks):
        """adds the given texts to the vector database"""
        embeddings = self.embeddingmodel.create_embeddings(chunks)
        self.index.add(embeddings)

           