
import tempfile
import subprocess
import os


def HumanCheck(pln : str, sentence: str) -> str:
    while True:
        user_input = input("Is this conversion correct? (y/n): ").lower()
        if user_input == 'y':
            break
        elif user_input == 'n':
            # Create a temporary file with the sentence as reference and the LLM output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
                temp_file.write(f"# Sentence: {sentence}\n{pln}")
                temp_file_path = temp_file.name

            # Open the default text editor for the user to make changes
            editor = os.environ.get('EDITOR', 'nano')  # Default to nano if EDITOR is not set
            subprocess.call([editor, temp_file_path])

            # Read the edited content
            with open(temp_file_path, 'r') as temp_file:
                lines = temp_file.readlines()
                pln = ''.join(lines[1:]).strip()  # Exclude the first line (sentence reference)

            # Remove the temporary file
            os.unlink(temp_file_path)

            print("--------------------------------------------------------------------------------")
            print(f"Updated OpenCog PLN: {pln}")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    return pln


