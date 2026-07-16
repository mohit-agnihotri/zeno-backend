from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

# Using a lightweight, fast model that outputs 384-dimensional vectors.
# Perfect for running locally on RTX 2050 without using much VRAM.
# Model is loaded once when the module starts.
print("Loading Embedding Model for Vector Search...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> List[float]:
    """
    Converts text (resume or job description) into a 384-dimensional vector.
    Returns the vector as a Python list of floats.
    """
    if not text:
        return [0.0] * 384
        
    try:
        # Generate embedding
        vector = model.encode(text)
        
        # Convert numpy array to standard python float list for Supabase
        return vector.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0.0] * 384
