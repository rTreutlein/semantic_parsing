from typing import List, Dict, Optional
import dspy
import threading

class ModelManager:
    """Manages language model initialization and configuration"""
    
    AVAILABLE_MODELS = [
        'openrouter/anthropic/claude-3.7-sonnet',
        'deepseek/deepseek-reasoner',
        'anthropic/claude-3-7-sonnet-20250219',
        'anthropic/claude-3-5-sonnet-20240620'
    ]

    def __init__(self):
        self.current_model = 'openrouter/anthropic/claude-3.7-sonnet'
        self.lm = None
        self.lock = threading.Lock()

    def initialize_model(self, model_name: str) -> bool:
        """Initialize the language model with thread safety"""
        try:
            with self.lock:
                self.lm = dspy.LM(model_name)
                dspy.configure(lm=self.lm)
                self.current_model = model_name
            return True
        except Exception as e:
            print(f"Error initializing language model {model_name}: {e}")
            return False

    def get_lm_instance(self, model_name: Optional[str] = None) -> Optional[dspy.LM]:
        """Get a language model instance without global configuration"""
        model_name = model_name or self.current_model
        try:
            return dspy.LM(model_name)
        except Exception as e:
            print(f"Error creating model instance {model_name}: {e}")
            return None
