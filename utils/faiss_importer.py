import json
import os
import csv
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import datetime
from tqdm import tqdm

from utils import setup_environment
from faiss_database import FAISSDatabase

class FAISSImporter:
    """Utility for importing data into FAISS vector database"""
    
    def __init__(self, db: FAISSDatabase):
        self.db = db
    
    def import_from_json(self, file_path: str, prompt_key: str = "prompt", 
                        metadata_keys: Optional[List[str]] = None) -> int:
        """
        Import prompts from a JSON file
        
        Args:
            file_path: Path to the JSON file
            prompt_key: The key in each JSON object that contains the prompt text
            metadata_keys: List of keys to extract as metadata (if None, all keys except prompt_key)
            
        Returns:
            Number of imported prompts
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return 0
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                # If the JSON is a single object with a list inside
                if isinstance(data, dict) and any(isinstance(data.get(k), list) for k in data):
                    # Find the first list in the JSON object
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0:
                            data = v
                            print(f"Using list found at key '{k}' with {len(data)} items")
                            break
                else:
                    # Convert single object to list
                    data = [data]
            
            count = 0
            for item in tqdm(data, desc="Importing prompts"):
                if prompt_key not in item:
                    print(f"Warning: Item missing prompt key '{prompt_key}', skipping")
                    continue
                    
                prompt_text = item[prompt_key]
                
                # Extract metadata
                if metadata_keys is None:
                    # Use all keys except the prompt key
                    metadata = {k: v for k, v in item.items() if k != prompt_key}
                else:
                    # Use only specified keys
                    metadata = {k: item.get(k) for k in metadata_keys if k in item}
                
                # Add timestamp if not present
                if "timestamp" not in metadata:
                    metadata["timestamp"] = datetime.datetime.now().isoformat()
                
                # Add to database
                self.db.add_prompt(prompt_text, metadata)
                count += 1
                
            print(f"Successfully imported {count} prompts from {file_path}")
            return count
            
        except Exception as e:
            print(f"Error importing from JSON: {str(e)}")
            return 0
    
    def import_from_csv(self, file_path: str, prompt_column: str, 
                       metadata_columns: Optional[List[str]] = None,
                       delimiter: str = ',') -> int:
        """
        Import prompts from a CSV file
        
        Args:
            file_path: Path to the CSV file
            prompt_column: The column name that contains the prompt text
            metadata_columns: List of column names to extract as metadata (if None, all columns except prompt_column)
            delimiter: CSV delimiter character
            
        Returns:
            Number of imported prompts
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return 0
            
        try:
            # Read CSV file
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            if prompt_column not in df.columns:
                print(f"Prompt column '{prompt_column}' not found in CSV")
                return 0
            
            # Determine metadata columns
            if metadata_columns is None:
                metadata_columns = [col for col in df.columns if col != prompt_column]
            else:
                # Verify columns exist
                for col in metadata_columns:
                    if col not in df.columns:
                        print(f"Warning: Metadata column '{col}' not found in CSV")
                        metadata_columns.remove(col)
            
            count = 0
            for _, row in tqdm(df.iterrows(), total=len(df), desc="Importing prompts"):
                prompt_text = row[prompt_column]
                
                # Skip empty prompts
                if pd.isna(prompt_text) or prompt_text == "":
                    continue
                
                # Extract metadata
                metadata = {}
                for col in metadata_columns:
                    if not pd.isna(row[col]):
                        metadata[col] = row[col]
                
                # Add timestamp if not present
                if "timestamp" not in metadata:
                    metadata["timestamp"] = datetime.datetime.now().isoformat()
                
                # Add to database
                self.db.add_prompt(prompt_text, metadata)
                count += 1
            
            print(f"Successfully imported {count} prompts from {file_path}")
            return count
            
        except Exception as e:
            print(f"Error importing from CSV: {str(e)}")
            return 0
    
    def import_from_text_file(self, file_path: str, delimiter: Optional[str] = None, 
                             metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Import prompts from a plain text file, one prompt per line
        
        Args:
            file_path: Path to the text file
            delimiter: Optional delimiter to split line into prompt and metadata
            metadata: Default metadata to apply to all prompts
            
        Returns:
            Number of imported prompts
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return 0
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            count = 0
            for line in tqdm(lines, desc="Importing prompts"):
                line = line.strip()
                if not line:
                    continue
                
                # Process line based on delimiter
                if delimiter and delimiter in line:
                    parts = line.split(delimiter, 1)
                    prompt_text = parts[0].strip()
                    prompt_metadata = parts[1].strip()
                    
                    # Try to parse metadata as JSON
                    try:
                        line_metadata = json.loads(prompt_metadata)
                    except:
                        # If not valid JSON, use as a simple string
                        line_metadata = {"additional_info": prompt_metadata}
                else:
                    prompt_text = line
                    line_metadata = {}
                
                # Combine with default metadata
                final_metadata = metadata.copy() if metadata else {}
                final_metadata.update(line_metadata)
                
                # Add timestamp if not present
                if "timestamp" not in final_metadata:
                    final_metadata["timestamp"] = datetime.datetime.now().isoformat()
                
                # Add to database
                self.db.add_prompt(prompt_text, final_metadata)
                count += 1
            
            print(f"Successfully imported {count} prompts from {file_path}")
            return count
            
        except Exception as e:
            print(f"Error importing from text file: {str(e)}")
            return 0
    
    def import_from_directory(self, directory_path: str, file_types: List[str] = None) -> Dict[str, int]:
        """
        Import prompts from all compatible files in a directory
        
        Args:
            directory_path: Path to the directory containing data files
            file_types: List of file extensions to import (default: ['.json', '.csv', '.txt'])
            
        Returns:
            Dictionary with file types and count of imported prompts
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print(f"Directory not found: {directory_path}")
            return {}
        
        if file_types is None:
            file_types = ['.json', '.csv', '.txt']
            
        results = {}
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext not in file_types:
                    continue
                
                print(f"Importing file: {file}")
                
                if file_ext == '.json':
                    count = self.import_from_json(file_path)
                elif file_ext == '.csv':
                    # Auto-detect prompt column from common names
                    df = pd.read_csv(file_path, nrows=0)  # Read header only
                    for col_name in ['prompt', 'text', 'content', 'description']:
                        if col_name in df.columns:
                            prompt_column = col_name
                            break
                    else:
                        # Use first column if no known column names found
                        prompt_column = df.columns[0]
                        
                    count = self.import_from_csv(file_path, prompt_column)
                elif file_ext == '.txt':
                    count = self.import_from_text_file(file_path)
                else:
                    count = 0
                
                if file_ext in results:
                    results[file_ext] += count
                else:
                    results[file_ext] = count
                    
        print(f"Import summary: {results}")
        total = sum(results.values())
        print(f"Total prompts imported: {total}")
        return results
