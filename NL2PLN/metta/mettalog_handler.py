import random
import string
import os
import subprocess
from typing import List, Tuple

class MettalogHandler:                                                          
    def __init__(self, file: str, read_only: bool = False):
        self.file = file
        self._read_only = read_only
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.relpath(script_dir, start=os.getcwd())
        print(os.getcwd())
        print(script_dir)
        print(relative_path)
        
        # Initialize the file with compiler import and KB initialization
        if not self._read_only:
            with open(self.file, 'w') as f:
                path = os.path.join(relative_path, 'compiler')
                print(path)
                f.write(f"!(import! &self ./{path})\n")
                f.write("!(bind! &kb (init-kb))\n")
                f.write("!(&kb)\n")

    @staticmethod
    def clean_variable_names(expr: str) -> str:
        """Remove #numbers from variable names like $var#1234"""
        import re
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*?)#\d+', r'$\1', expr)

    @property
    def read_only(self) -> bool:
        return self._read_only

    def add_atom(self, atom: str) -> None:
        if not self._read_only:
            with open(self.file, 'a') as f:
                f.write(f'!(compileAdd &kb {atom})\n')

    def query(self, atom: str) -> Tuple[List[str], bool]:
        # Create a temporary file for the query
        temp_file = f"{self.file}.query_temp"
        
        # Copy current file content and add query
        if not self._read_only:
            with open(self.file, 'r') as original:
                content = original.read()
            
            with open(temp_file, 'w') as temp:
                temp.write(content)
                temp.write(f'!(query &kb (fromNumber 5) {atom})\n')
        
        # Execute mettalog on the temporary file
        try:
            result = subprocess.run(['mettalog', temp_file], 
                                  capture_output=True, text=True, check=True)
            output_lines = result.stdout.strip().split('\n')
            
            # Parse the output to extract query results
            # This is a simplified parser - may need adjustment based on actual mettalog output format
            results = []
            for line in output_lines:
                if line.strip() and not line.startswith('!'):
                    results.append(line.strip())
            
            proven = len(results) > 0
            
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return results, proven
            
        except subprocess.CalledProcessError as e:
            print(f"Error running mettalog: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return [], False

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        return None
        
    def run(self, atom: str):
        if not self._read_only:
            with open(self.file, 'a') as f:
                f.write(f"{atom}\n")
        
        # Execute mettalog to get results
        try:
            result = subprocess.run(['mettalog', self.file], 
                                  capture_output=True, text=True, check=True)
            output_lines = result.stdout.strip().split('\n')
            return [output_lines]
        except subprocess.CalledProcessError as e:
            print(f"Error running mettalog: {e}")
            return [[]]

    def run_clean(self, atom: str) -> List[str]:
        res = self.run(atom)
        return [self.clean_variable_names(str(elem)) for elem in res[0]]
                                                                             
    def store_kb_to_file(self):
        if self.read_only:
            print("Warning: Cannot store KB in read-only mode")
            return
        
        # Add command to match and output KB content
        with open(self.file, 'a') as f:
            f.write('!(match &kb $a $a)\n')

    def load_kb_from_file(self):
        if os.path.exists(self.file):
            # File already exists, KB will be loaded when mettalog runs
            pass
        else:
            print(f"Warning: File {self.file} does not exist. No KB loaded.")

    def append_to_file(self, elem: str):
        if self.read_only:
            print("Warning: Cannot append to file in read-only mode")
            return
        with open(self.file, 'a') as f:
            f.write(elem)

if __name__ == '__main__':
    handler = MettalogHandler('kb_backup.metta', read_only=False)

    print("Testing:")

    print(handler.add_atom("(: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0))"))
    print(handler.add_atom("(: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0))"))

    print(handler.run("!(bind! &file (file-open! \"./out.metta\" \"wc\"))"))

    print(handler.run("!(file-write! &file (show-cs &kb)"))

    #print(handler.query("(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv)"))


