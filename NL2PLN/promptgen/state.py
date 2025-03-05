"""
Module for managing application state
"""
import threading

class AppState:
    """Singleton class for managing application state"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppState, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        """Initialize the application state"""
        self.current_model = "anthropic/claude-3-5-sonnet-20241022"
        self.optimization_running = False
        self.evaluation_results = {"metrics": {}, "results": []}
        
        # Available models
        self.AVAILABLE_MODELS = [
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-7-sonnet-20250219",
            "openai/gpt-4-turbo"
        ]
