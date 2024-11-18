
import tempfile
import subprocess
import os


def check_predicate_logic(pred_logic: str, fix_function=None) -> str|None:
    pred_logic = pred_logic.replace("$", "\\$")
    metta = os.popen(f"plparserexe \"{pred_logic}\"").read().strip()

    if metta.startswith("Error:") and fix_function:
        print("Trying to fix...")
        pred_logic = fix_function(pred_logic, metta)
        if pred_logic is None:
            return None
        pred_logic = pred_logic.replace("$", "\\$")
        metta = os.popen(f"plparserexe \"{pred_logic}\"").read().strip()

    if metta.startswith("Error:"):
        print("Failed to fix...")
        return None

    return metta


def HumanCheck(model_output : str, sentence: str) -> str:
    while True:
        user_input = input(f"Is this output correct? (y/n): ").lower()
        if user_input == 'y':
            break
        elif user_input == 'n':
            # Create a temporary file with the sentence as reference and the LLM output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
                temp_file.write(f"# Sentence: {sentence}\n{model_output}")
                temp_file_path = temp_file.name

            # Open the default text editor for the user to make changes
            editor = os.environ.get('EDITOR', 'nano')  # Default to nano if EDITOR is not set
            subprocess.call([editor, temp_file_path])

            # Read the edited content
            with open(temp_file_path, 'r') as temp_file:
                lines = temp_file.readlines()
                human_out = ''.join(lines[1:]).strip()  # Exclude the first line (sentence reference)

            # Remove the temporary file
            os.unlink(temp_file_path)

            print("--------------------------------------------------------------------------------")
            print(f"Updated OpenCog PLN: {human_out}")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    return model_output

