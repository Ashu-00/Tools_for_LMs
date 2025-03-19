# Chunking functions

class Chunker:
    def __init__(self, chunk_size, chunk_method = "naive"):
        self.chunk_size = chunk_size
        self.chunk_method = chunk_method

    def chunk_texts(self, texts):
        """chunks the given texts into chunks of the specified size"""
        chunks = []
        for text in texts:
            if self.chunk_method == "naive":
                ptr = 0
                while ptr < len(text):
                    chunks.append(text[:self.chunk_size])
                    ptr += self.chunk_size
            
            else:
                raise ValueError("Invalid chunk method")
        return chunks