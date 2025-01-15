import json
import os
from typing import Dict, Any
import dspy

class CacheHandler:
    """Handles caching of results to avoid redundant computations."""
    
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cache from file or return empty dict if file doesn't exist."""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def _save_cache(self):
        """Save current cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _serialize_value(self, value: Any) -> Any:
        """Convert value to JSON-serializable format."""
        if isinstance(value, dspy.Prediction):
            return dict(value.items())
        return value
    
    def _deserialize_value(self, value: Any) -> Any:
        """Convert stored value back to appropriate format."""
        if isinstance(value, dict):
            return dspy.Prediction(**value)
        return value
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        value = self.cache.get(key)
        if value is not None:
            return self._deserialize_value(value)
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache and save to file."""
        self.cache[key] = self._serialize_value(value)
        self._save_cache()
