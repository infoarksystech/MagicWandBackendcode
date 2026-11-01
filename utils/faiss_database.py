import os
import json
import numpy as np
import faiss
import openai
from typing import List, Dict, Any
import datetime
from app.utils.setup_env import adapt_vector_dimension

class FAISSDatabase:
    """Vector database for storing and retrieving similar prompts"""
    
    def __init__(self, nlp, dimension: int = 1536, index_file: str = "prompts_index.faiss", data_file: str = "prompts_data.json"):
        self.dimension = dimension
        self.index_file = index_file
        self.data_file = data_file
        self.prompts_data = []
        self.nlp = nlp
        
        # Create or load FAISS index
        if os.path.exists(index_file) and os.path.exists(data_file):
            self.index = faiss.read_index(index_file)
            with open(data_file, 'r') as f:
                self.prompts_data = json.load(f)
            print(f"Loaded {len(self.prompts_data)} prompts from database")
        else:
            self.index = faiss.IndexFlatL2(dimension)
            print("Created new FAISS index")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI's embedding API"""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            vector = np.array(response.data[0].embedding, dtype=np.float32)
            return vector
        except Exception as e:
            print(f"Error getting OpenAI embedding, falling back to spaCy: {e}")
            # Fallback to spaCy if OpenAI API fails
            doc = self.nlp(text)
            return adapt_vector_dimension(doc.vector, self.dimension)
    
    def add_prompt(self, prompt_text: str, metadata: Dict[str, Any]) -> None:
        """Add a prompt to the database"""
        vector = self._get_embedding(prompt_text)
        vector = vector.reshape(1, -1).astype('float32')
        
        # Add to FAISS index
        self.index.add(vector)
        
        # Store prompt data
        prompt_data = {
            "text": prompt_text,
            "metadata": metadata,
            "id": len(self.prompts_data)
        }
        self.prompts_data.append(prompt_data)
        
        # Save to disk
        self._save()
    
    def search_similar(self, query_text: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar prompts in the database"""
        if len(self.prompts_data) == 0:
            return []
            
        query_vector = self._get_embedding(query_text)
        query_vector = query_vector.reshape(1, -1).astype('float32')
        
        # Search in FAISS
        distances, indices = self.index.search(query_vector, min(k, len(self.prompts_data)))
        
        # Get results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                result = self.prompts_data[idx].copy()
                result["similarity_score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity
                results.append(result)
        
        return results
    
    def _save(self) -> None:
        """Save the index and data to disk"""
        faiss.write_index(self.index, self.index_file)
        with open(self.data_file, 'w') as f:
            json.dump(self.prompts_data, f)
        print(f"Saved {len(self.prompts_data)} prompts to database")
