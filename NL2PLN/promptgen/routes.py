from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from threading import Thread
from .models import ModelManager
from .samples import SampleManager
from .optimization import Optimizer
import dspy
import json

def create_routes(model_manager: ModelManager, sample_manager: SampleManager, optimizer: Optimizer):
    """Create Flask routes blueprint"""
    bp = Blueprint('main', __name__)
    
    @bp.route('/')
    def index():
        samples = sample_manager.load_samples()
        return render_template('index.html', 
                            samples=samples, 
                            optimization_running=optimizer.running,
                            models=model_manager.AVAILABLE_MODELS,
                            current_model=model_manager.current_model)

    @bp.route('/samples')
    def view_samples():
        samples = sample_manager.load_samples()
        return render_template('samples.html', samples=samples)

    @bp.route('/sample/<int:sample_id>')
    def view_sample(sample_id):
        samples = sample_manager.load_samples()
        if 0 <= sample_id < len(samples):
            return render_template('sample.html', 
                                 sample=samples[sample_id], 
                                 sample_id=sample_id)
        return redirect(url_for('main.view_samples'))

    # Add other routes here following the same pattern...
    
    @bp.route('/optimize', methods=['POST'])
    def optimize():
        if not optimizer.running:
            model_name = request.form.get('model', model_manager.current_model)
            Thread(target=optimizer.run_optimization, args=(model_name,)).start()
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})

    @bp.route('/optimization_status')
    def optimization_status():
        return jsonify({"running": optimizer.running})

    return bp

def get_task_description():
    """Get task description from file or return default"""
    try:
        with open("task.json", "r") as f:
            return json.load(f)["self"]["extended_signature"]["instructions"]
    except Exception:
        return "Convert English to Logic (MeTTa PLN Light)"
