from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from threading import Thread
import os
import json
import dspy
from .models import ModelManager
from .samples import SampleManager
from .optimization import Optimizer
from .state import AppState

def create_routes(app_state: AppState, model_manager: ModelManager, sample_manager: SampleManager, optimizer: Optimizer):
    """Create Flask routes blueprint"""
    bp = Blueprint('main', __name__)
    
    @bp.route('/')
    def index():
        samples = sample_manager.load_samples()
        return render_template('index.html', 
                            samples=samples, 
                            optimization_running=optimizer.running,
                            evaluation_results=app_state.evaluation_results,
                            models=app_state.AVAILABLE_MODELS,
                            current_model=app_state.current_model)

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

    @bp.route('/sample/<int:sample_id>/edit', methods=['GET', 'POST'])
    def edit_sample(sample_id):
        """Edit a specific sample."""
        samples = sample_manager.load_samples()
        
        if request.method == 'POST':
            if 0 <= sample_id < len(samples):
                samples[sample_id]['input'] = request.form.get('input', '')
                samples[sample_id]['types'] = request.form.get('types', '')
                samples[sample_id]['statements'] = request.form.get('statements', '')
                samples[sample_id]['questions'] = request.form.get('questions', '')
                sample_manager.save_samples(samples)
                return redirect(url_for('main.view_sample', sample_id=sample_id))
        
        if 0 <= sample_id < len(samples):
            return render_template('edit_sample.html', sample=samples[sample_id], sample_id=sample_id)
        return redirect(url_for('main.view_samples'))

    @bp.route('/add_sample', methods=['GET', 'POST'])
    def add_sample():
        """Add a new sample."""
        if request.method == 'POST':
            new_sample = {
                'input': request.form.get('input', ''),
                'types': request.form.get('types', ''),
                'statements': request.form.get('statements', ''),
                'questions': request.form.get('questions', '')
            }
            samples = sample_manager.load_samples()
            samples.append(new_sample)
            sample_manager.save_samples(samples)
            return redirect(url_for('main.view_samples'))
        
        return render_template('add_sample.html', 
                              models=app_state.AVAILABLE_MODELS, 
                              current_model=app_state.current_model)

    @bp.route('/generate_sample', methods=['POST'])
    def generate_sample():
        """Generate a sample using the LLM."""
        # Get the input and model
        input_text = request.form.get('input', '')
        model_name = request.form.get('model', app_state.current_model)
        
        # Get a model instance without configuring DSPy
        sample_lm = model_manager.get_lm_instance(model_name)
        if sample_lm is None:
            return jsonify({
                "error": f"Failed to initialize model {model_name}",
                "input": input_text,
                "types": "",
                "statements": "",
                "questions": ""
            })
        
        try:
            # Create a basic example generator with the specific LM instance
            gen_example = dspy.ChainOfThought('task: str, input: str -> types: str, statements: str, questions: str')
            
            # Get the task from task.json if it exists
            task = get_task_description()
            
            # Generate the sample using the specific LM instance
            with dspy.context(lm=sample_lm):
                pred = gen_example(task=task, input=input_text)
            
            # Return the generated sample
            return jsonify({
                "input": input_text,
                "types": pred.types,
                "statements": pred.statements,
                "questions": pred.questions
            })
        except Exception as e:
            return jsonify({
                "error": str(e),
                "input": input_text,
                "types": "",
                "statements": "",
                "questions": ""
            })
    
    @bp.route('/optimize', methods=['POST'])
    def optimize():
        if not optimizer.running:
            model_name = request.form.get('model', app_state.current_model)
            # Update the current model in app state
            app_state.current_model = model_name
            Thread(target=optimizer.run_optimization, args=(model_name,)).start()
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})

    @bp.route('/optimization_status')
    def optimization_status():
        return jsonify({"running": optimizer.running})

    @bp.route('/evaluate', methods=['POST'])
    def evaluate():
        """Run the evaluation on the optimized model."""
        # Get the model to use for evaluation
        model_name = request.form.get('model', app_state.current_model)
        # Update the current model in app state
        app_state.current_model = model_name
        
        # Evaluate directly without calling the script
        try:
            # Get a model instance without configuring DSPy globally
            eval_lm = model_manager.get_lm_instance(model_name)
            if eval_lm is None:
                return jsonify({
                    "error": f"Failed to initialize model {model_name}",
                    "metrics": {},
                    "full_output": f"Error initializing model {model_name}"
                })
                
            # Load optimized task
            try:
                optimized_task = dspy.load("./program/")
                print(f"Successfully loaded optimized task: {type(optimized_task)}")
            except Exception as e:
                return jsonify({
                    "error": f"Failed to load optimized task: {e}",
                    "metrics": {},
                    "full_output": f"Error: {str(e)}"
                })
            
            # Load samples
            samples = sample_manager.load_samples()
            if not samples:
                return jsonify({
                    "error": "No samples to evaluate",
                    "metrics": {},
                    "full_output": "Error: No samples found"
                })
                
            # Evaluate model on samples
            results = []
            for i, sample in enumerate(samples):
                try:
                    print(f"Evaluating sample {i+1}/{len(samples)}: {sample['input'][:50]}...")
                    english = sample["input"]
                    expected_types = sample["types"]
                    expected_statements = sample["statements"]
                    expected_questions = sample.get("questions", "")
                    
                    # Run the model on the input with the specific LM instance
                    with dspy.context(lm=eval_lm):
                        prediction = optimized_task(english=english)
                    
                    # Calculate simple similarity metrics
                    types_match = expected_types.strip() == prediction.pln_types.strip()
                    statements_match = expected_statements.strip() == prediction.pln_statements.strip()
                    questions_match = expected_questions.strip() == prediction.pln_questions.strip()
                    
                    # Store the results
                    results.append({
                        "sample_id": i,
                        "input": english,
                        "types_match": types_match,
                        "statements_match": statements_match,
                        "questions_match": questions_match,
                        "expected_types": expected_types,
                        "predicted_types": prediction.pln_types,
                        "expected_statements": expected_statements,
                        "predicted_statements": prediction.pln_statements,
                        "expected_questions": expected_questions,
                        "predicted_questions": prediction.pln_questions
                    })
                except Exception as e:
                    print(f"Error evaluating sample {i+1}: {e}")
                    results.append({
                        "sample_id": i,
                        "input": sample["input"],
                        "types_match": False,
                        "statements_match": False,
                        "questions_match": False,
                        "expected_types": sample["types"],
                        "predicted_types": "ERROR",
                        "expected_statements": sample["statements"],
                        "predicted_statements": "ERROR",
                        "expected_questions": sample.get("questions", ""),
                        "predicted_questions": "ERROR",
                        "error": str(e)
                    })
                    
            # Calculate overall metrics
            total = len(results)
            types_correct = sum(1 for r in results if r.get("types_match", False))
            statements_correct = sum(1 for r in results if r.get("statements_match", False))
            questions_correct = sum(1 for r in results if r.get("questions_match", False))
            all_correct = sum(1 for r in results if r.get("types_match", False) and r.get("statements_match", False) and r.get("questions_match", False))
            errors = sum(1 for r in results if "error" in r)
            
            # Generate metrics
            metrics = {
                "Types Correct": f"{types_correct}/{total} ({types_correct/total:.2%})",
                "Statements Correct": f"{statements_correct}/{total} ({statements_correct/total:.2%})",
                "Questions Correct": f"{questions_correct}/{total} ({questions_correct/total:.2%})",
                "All Components Correct": f"{all_correct}/{total} ({all_correct/total:.2%})",
                "Errors": f"{errors}/{total} ({errors/total:.2%})"
            }
            
            # Store the evaluation results in app state
            app_state.evaluation_results = {
                "metrics": metrics,
                "results": results
            }
            
            # Return the evaluation results
            return jsonify(app_state.evaluation_results)
        except Exception as e:
            return jsonify({
                "error": f"Evaluation failed: {str(e)}",
                "metrics": {},
                "full_output": f"Error: {str(e)}"
            })

    @bp.route('/evaluation_results')
    def get_evaluation_results():
        """Get the current evaluation results."""
        return jsonify(app_state.evaluation_results)

    return bp

def get_task_description():
    """Get task description from file or return default"""
    try:
        with open("task.json", "r") as f:
            return json.load(f)["self"]["extended_signature"]["instructions"]
    except Exception:
        return "Convert English to Logic (MeTTa PLN Light)"
