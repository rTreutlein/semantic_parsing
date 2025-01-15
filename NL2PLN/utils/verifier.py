import dspy
from typing import Any, Optional, Callable
from .cache_handler import CacheHandler

class VerifiedPredictor:
    """Generic wrapper for dspy.Module that includes human verification and caching of verified results."""
    
    def __init__(self, 
                 predictor: dspy.Module,
                 verify_func: Callable[[dspy.Prediction, Any], dspy.Prediction],
                 cache_file: str = "verified_predictions_cache.json"):
        """
        Initialize the verifier.
        
        Args:
            predictor: The dspy.Module to wrap
            verify_func: Function that takes (prediction, input) and returns verified prediction
            cache_file: Path to the cache file
        """
        self.predictor = predictor
        self.verify_func = verify_func
        self.cache = CacheHandler(cache_file)
    
    def predict(self, *args, **kwargs) -> dspy.Prediction:
        """
        Get prediction with verification and caching.
        
        All args and kwargs are passed to the predictor's forward method.
        """
        # Create a cache key from all inputs
        cache_key = str({
            "args": args,
            "kwargs": kwargs
        })
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Get initial prediction
        prediction = self.predictor.forward(*args, **kwargs)
        
        # Get verification
        verified_prediction = self.verify_func(prediction, args[0] if args else None)
        
        # Cache the verified result
        self.cache.set(cache_key, verified_prediction)
        
        return verified_prediction
