import os
import sys
import json
import subprocess
import dspy
from flask import Flask, render_template, request, jsonify, redirect, url_for
from threading import Thread
from .models import ModelManager
from .samples import SampleManager
from .optimization import Optimizer
from .state import AppState

def create_app():
    """Application factory function"""
    flask_app = Flask(__name__)
    
    # Initialize components
    app_state = AppState()
    model_manager = ModelManager()
    sample_manager = SampleManager()
    optimizer = Optimizer(model_manager, sample_manager)
    
    # Create required directories
    @flask_app.before_request
    def setup_dirs():
        create_directories()
    
    # Import routes here to avoid circular imports
    from . import routes
    
    # Register routes
    flask_app.register_blueprint(
        routes.create_routes(app_state, model_manager, sample_manager, optimizer)
    )
    
    # Initialize the model
    model_manager.initialize_model(app_state.current_model)
    
    # Add CLI commands if needed
    @flask_app.cli.command("optimize")
    def optimize_command():
        """Run optimization from command line"""
        from .optimization import Optimizer
        optimizer = Optimizer(model_manager, sample_manager)
        optimizer.run_optimization(app_state.current_model)
    
    return flask_app

def create_directories():
    """Create required directories"""
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("samples", exist_ok=True)

# These functions are no longer needed with the new architecture

# These helper functions are no longer needed with the new architecture

# Routes are now defined in routes.py and registered via blueprint
