from .app import create_app

# This allows "flask --app NL2PLN/promptgen run" to work
app = create_app()
