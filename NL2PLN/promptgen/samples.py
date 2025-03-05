import json
from typing import List, Dict
import os

class SampleManager:
    """Handles loading and saving of sample data"""
    
    def __init__(self, sample_file: str = "samples/generated_samples.json"):
        self.sample_file = sample_file
        os.makedirs(os.path.dirname(sample_file), exist_ok=True)

    def load_samples(self) -> List[Dict]:
        """Load samples from JSON file"""
        try:
            with open(self.sample_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_samples(self, samples: List[Dict]) -> None:
        """Save samples to JSON file"""
        with open(self.sample_file, "w") as f:
            json.dump(samples, f, indent=2)

    def validate_sample(self, sample: Dict) -> bool:
        """Validate sample structure"""
        required_keys = {'input', 'types', 'statements', 'questions'}
        return all(key in sample for key in required_keys)
