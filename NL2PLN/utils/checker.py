import tempfile
import subprocess
import os
import json
from typing import Any
import dspy


def human_verify_prediction(prediction: dspy.Prediction, input_text: str) -> dspy.Prediction:
    while True:
        # Display current state
        print("\nOriginal input:", input_text)
        print("\nCurrent prediction:")
        for field_name, field_value in prediction.items():
            print(f"\n{field_name}:")
            print(field_value)
            
        user_input = input("\nIs this prediction correct? (y/n): ").lower()
        
        if user_input == 'y':
            return prediction
        elif user_input == 'n':
            # Create a temporary file with JSON structure for editing
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                # Convert prediction to editable format
                editable_content = {
                    "input_text": input_text,  # For reference
                    "prediction": {
                        k: v for k, v in prediction.items()
                    }
                }
                
                # Add some helpful comments
                temp_file.write("// Edit the prediction values below.\n")
                temp_file.write("// The input_text field is for reference only.\n")
                temp_file.write(json.dumps(editable_content, indent=2))
                temp_file_path = temp_file.name

            # Open in default text editor
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.call([editor, temp_file_path])

            try:
                # Read and parse the edited content
                with open(temp_file_path, 'r') as temp_file:
                    # Skip comment lines
                    content = ""
                    for line in temp_file:
                        if not line.strip().startswith("//"):
                            content += line
                    
                    edited_content = json.loads(content)
                    
                # Create new prediction with edited values
                corrected_prediction = dspy.Prediction()
                for k, v in edited_content["prediction"].items():
                    corrected_prediction[k] = v
                
                # Clean up
                os.unlink(temp_file_path)
                
                print("\nUpdated prediction:")
                for field_name, field_value in corrected_prediction.items():
                    print(f"\n{field_name}:")
                    print(field_value)
                
                confirm = input("\nSave these changes? (y/n): ").lower()
                if confirm == 'y':
                    return corrected_prediction
                # If not confirmed, loop continues
                
            except json.JSONDecodeError as e:
                print(f"\nError parsing edited content: {e}")
                print("Please ensure the JSON structure remains valid.")
                os.unlink(temp_file_path)
                continue
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                os.unlink(temp_file_path)
                continue
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


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
            return model_output
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
            return human_out
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

