# NL2PLN Promptgen Web Frontend

A web-based frontend for generating, viewing, editing, and evaluating NL2PLN (Natural Language to PLN) samples.

## Features

- View and manage samples in the browser
- Add new samples through a web form
- Edit existing samples
- Trigger model optimization
- Run evaluation and view results
- User-friendly interface

## Setup

1. Install the required dependencies:

```bash
pip install flask dspy tabulate
```

2. Run the web application:

```bash
python app.py
```

3. Open your browser and navigate to:

```
http://localhost:5000
```

## Usage

### Dashboard

The dashboard provides an overview of your samples and allows you to:
- Start optimization
- Run evaluation
- View recent samples

### Samples

The samples page shows all available examples with options to:
- View detailed information
- Edit samples
- Add new samples

### Adding Samples

When adding a new sample, provide:
- Input (English text)
- Types (MeTTa PLN Light types)
- Statements (MeTTa PLN Light statements)
- Questions (optional)

### Optimizing the Model

Click the "Start Optimization" button on the dashboard to begin model optimization using the current samples. This process may take a few minutes.

### Evaluating the Model

After optimization, click the "Run Evaluation" button to evaluate the model against the samples. Results will be displayed on the dashboard.

## Files

- `app.py`: The Flask web application
- `promptgen.py`: The optimization script
- `evaluate.py`: The evaluation script
- `samples/generated_samples.json`: The samples database

## Dependencies

- Flask
- DSPy
- Tabulate
- Bootstrap 5 (CDN)
- jQuery (CDN)