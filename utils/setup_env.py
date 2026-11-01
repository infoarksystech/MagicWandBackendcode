import os
import nltk
import spacy
import numpy as np
from typing import Any
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Load environment variables
def setup_environment():
    """Set up environment and necessary models"""
    # Download NLTK data if needed
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    # Load spaCy for text processing
    try:
        nlp = spacy.load("en_core_web_md")
    except:
        print("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_md")
        nlp = spacy.load("en_core_web_md")
    
    return nlp

# Retry decorator for API calls
def api_retry():
    """Decorator that provides retry logic for API calls"""
    return retry(
        wait=wait_random_exponential(min=1, max=60), 
        stop=stop_after_attempt(5)
    )

# Function to convert spaCy vectors to match OpenAI dimensions
def adapt_vector_dimension(vector: np.ndarray, target_dimension: int) -> np.ndarray:
    """Adapt a vector to the target dimension by padding or truncating"""
    if len(vector) < target_dimension:
        padded = np.zeros(target_dimension, dtype=np.float32)
        padded[:len(vector)] = vector
        return padded
    else:
        return vector[:target_dimension]
