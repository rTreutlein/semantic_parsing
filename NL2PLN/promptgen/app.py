import os
from flask import Flask
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
    
    return flask_app

def create_directories():
    """Create required directories"""
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("samples", exist_ok=True)

def run_optimization():
    """Run the optimization script in a separate thread."""
    global optimization_running
    try:
        subprocess.run([sys.executable, "promptgen.py"], check=True)
        optimization_running = False
    except Exception as e:
        print(f"Error running optimization: {e}")
        optimization_running = False

def run_evaluation():
    """Run the evaluation script and return the results."""
    global evaluation_results
    try:
        # Run the evaluation script
        output = subprocess.check_output([sys.executable, "evaluate.py"], 
                                         text=True, 
                                         stderr=subprocess.STDOUT)
        
        # Parse the evaluation results from the output
        # This is a simplistic parsing that could be improved
        lines = output.splitlines()
        summary_start = None
        summary_end = None
        
        for i, line in enumerate(lines):
            if "=== Evaluation Summary ===" in line:
                summary_start = i
            elif summary_start is not None and "=== Detailed Results ===" in line:
                summary_end = i
                break
        
        if summary_start is not None and summary_end is not None:
            summary_lines = lines[summary_start:summary_end]
            
            # Extract metrics
            metrics = {}
            for line in summary_lines:
                if "|" in line and not line.startswith("+"):
                    parts = line.split("|")
                    if len(parts) >= 4:
                        metric_name = parts[1].strip()
                        metric_value = parts[3].strip()
                        metrics[metric_name] = metric_value
            
            # Store the evaluation results
            evaluation_results = {
                "metrics": metrics,
                "full_output": output
            }
            
            return evaluation_results
        else:
            return {"error": "Could not parse evaluation results", "output": output}
        
    except subprocess.CalledProcessError as e:
        return {"error": f"Error running evaluation: {e.output}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def load_samples():
    """Load samples from the sample manager"""
    sample_manager = SampleManager()
    return sample_manager.load_samples()

def save_samples(samples):
    """Save samples using the sample manager"""
    sample_manager = SampleManager()
    sample_manager.save_samples(samples)

def get_lm_instance(model_name):
    """Get a language model instance"""
    model_manager = ModelManager()
    return model_manager.get_lm_instance(model_name)

def initialize_model(model_name):
    """Initialize the language model"""
    model_manager = ModelManager()
    return model_manager.initialize_model(model_name)

@app.route('/')
def index():
    """Render the main page."""
    samples = load_samples()
    return render_template('index.html', 
                          samples=samples, 
                          optimization_running=optimization_running,
                          evaluation_results=evaluation_results,
                          models=AVAILABLE_MODELS,
                          current_model=current_model)

@app.route('/samples')
def view_samples():
    """View all samples."""
    samples = load_samples()
    return render_template('samples.html', samples=samples)

@app.route('/sample/<int:sample_id>')
def view_sample(sample_id):
    """View a specific sample."""
    samples = load_samples()
    if 0 <= sample_id < len(samples):
        return render_template('sample.html', sample=samples[sample_id], sample_id=sample_id)
    return redirect(url_for('view_samples'))

@app.route('/sample/<int:sample_id>/edit', methods=['GET', 'POST'])
def edit_sample(sample_id):
    """Edit a specific sample."""
    samples = load_samples()
    
    if request.method == 'POST':
        if 0 <= sample_id < len(samples):
            samples[sample_id]['input'] = request.form.get('input', '')
            samples[sample_id]['types'] = request.form.get('types', '')
            samples[sample_id]['statements'] = request.form.get('statements', '')
            samples[sample_id]['questions'] = request.form.get('questions', '')
            save_samples(samples)
            return redirect(url_for('view_sample', sample_id=sample_id))
    
    if 0 <= sample_id < len(samples):
        return render_template('edit_sample.html', sample=samples[sample_id], sample_id=sample_id)
    return redirect(url_for('view_samples'))

@app.route('/add_sample', methods=['GET', 'POST'])
def add_sample():
    """Add a new sample."""
    if request.method == 'POST':
        new_sample = {
            'input': request.form.get('input', ''),
            'types': request.form.get('types', ''),
            'statements': request.form.get('statements', ''),
            'questions': request.form.get('questions', '')
        }
        samples = load_samples()
        samples.append(new_sample)
        save_samples(samples)
        return redirect(url_for('view_samples'))
    
    return render_template('add_sample.html', models=AVAILABLE_MODELS, current_model=current_model)

@app.route('/generate_sample', methods=['POST'])
def generate_sample():
    """Generate a sample using the LLM."""
    global current_model
    
    # Get the input and model
    input_text = request.form.get('input', '')
    model_name = request.form.get('model', current_model)
    
    # Get a model instance without configuring DSPy
    sample_lm = get_lm_instance(model_name)
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
        try:
            with open("task.json", "r") as f:
                task = json.load(f)["self"]["extended_signature"]["instructions"]
        except Exception:
            task = "Convert English to Logic (MeTTa PLN Light)"
        
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

@app.route('/optimize', methods=['POST'])
def optimize():
    """Start the optimization process with the selected model."""
    global optimization_running, current_model, lm
    
    if not optimization_running:
        # Get the model to use for optimization
        model_name = request.form.get('model', current_model)
        optimization_running = True
        
        # Run optimization in a separate thread
        def run_optimization_with_model():
            global optimization_running
            try:
                # Get a model instance without configuring DSPy globally
                thread_lm = get_lm_instance(model_name)
                if thread_lm is None:
                    print(f"Failed to create model instance for optimization")
                    optimization_running = False
                    return
                
                # Load samples
                samples = load_samples()
                samples_data = [dspy.Prediction(
                    diverse_example_input=d["input"], 
                    diverse_example_output_types=d["types"],
                    diverse_example_output_statements=d["statements"],
                    diverse_example_output_questions=d.get("questions", "")
                ) for d in samples]
                
                # Get task from task.json if it exists
                try:
                    with open("task.json", "r") as f:
                        task_description = json.load(f)["self"]["extended_signature"]["instructions"]
                except Exception:
                    task_description = "Convert English to Logic (MeTTa PLN Light)"
                
                # Create examples for training
                data = [
                    dspy.Example(
                        english=d.diverse_example_input, 
                        pln_types=d.diverse_example_output_types,
                        pln_statements=d.diverse_example_output_statements,
                        pln_questions=d.diverse_example_output_questions
                    ).with_inputs('english') 
                    for d in samples_data
                ]
                
                # Define the task and metric
                task = dspy.ChainOfThought('english -> pln_types: str, pln_statements: str, pln_questions: str')
                
                def metric(example, pred, trace=None):
                    judge = dspy.ChainOfThought('true_types, true_statements, true_questions, pred_types, pred_statements, pred_questions -> similarity: float')
                    return judge(
                        true_types=example.pln_types, 
                        true_statements=example.pln_statements,
                        true_questions=example.pln_questions,
                        pred_types=pred.pln_types,
                        pred_statements=pred.pln_statements,
                        pred_questions=pred.pln_questions
                    ).similarity
                
                # Optimize the task using the thread-specific LM
                with dspy.context(lm=thread_lm):
                    optimized_task = dspy.MIPROv2(metric=metric, auto="light").compile(task, trainset=data, requires_permission_to_run=False)
                
                # Save the optimized task
                os.makedirs("./program/", exist_ok=True)
                optimized_task.save("./program/", save_program=True)
                
                optimization_running = False
            except Exception as e:
                print(f"Error during optimization: {e}")
                optimization_running = False
        
        thread = Thread(target=run_optimization_with_model)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "started"})
    return jsonify({"status": "already_running"})

@app.route('/optimization_status')
def optimization_status():
    """Check the status of the optimization process."""
    return jsonify({"running": optimization_running})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    """Run the evaluation on the optimized model."""
    global lm, current_model
    
    # Get the model to use for evaluation
    model_name = request.form.get('model', current_model)
    
    # Evaluate directly without calling the script
    try:
        # Get a model instance without configuring DSPy globally
        eval_lm = get_lm_instance(model_name)
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
        samples = load_samples()
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
        
        # Store the evaluation results for later retrieval
        global evaluation_results
        evaluation_results = {
            "metrics": metrics,
            "results": results
        }
        
        return jsonify(evaluation_results)
    except Exception as e:
        return jsonify({
            "error": f"Evaluation failed: {str(e)}",
            "metrics": {},
            "full_output": f"Error: {str(e)}"
        })

@app.route('/evaluation_results')
def get_evaluation_results():
    """Get the current evaluation results."""
    return jsonify(evaluation_results)

if __name__ == '__main__':
    # Initialize the default model in the main thread
    initialize_model(current_model)
    app.run(debug=True, host='0.0.0.0', port=5000)
