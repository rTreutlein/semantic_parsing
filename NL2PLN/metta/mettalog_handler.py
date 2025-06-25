import random
import string
import os
import subprocess
from typing import List, Tuple

class MettalogHandler:                                                          
    def __init__(self, file: str, read_only: bool = False):
        self.file = file
        self._read_only = read_only
        self.process = None
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.relpath(script_dir, start=os.getcwd())
        print(os.getcwd())
        print(script_dir)
        print(relative_path)
        
        # Start the mettalog process
        self._start_process()
        
        # Initialize with compiler import and KB initialization
        if not self._read_only:
            path = os.path.join(relative_path, 'compiler')
            print(path)
            print("Importing and initalizing")
            print(self._send_command(f"!(import! &self ./{path})"))
            print(self._send_command("!(bind! &kb (init-kb))"))
            print(self._send_command("!(&kb)"))

    def _start_process(self):
        """Start the mettalog process with stdin/stdout pipes"""
        try:
            self.process = subprocess.Popen(
                ['mettalog'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        except FileNotFoundError:
            raise RuntimeError("mettalog executable not found. Please ensure it's installed and in PATH.")
    
    def _send_command(self, command: str) -> List[str]:
        """Send a command to the mettalog process and return the output"""
        if self.process is None or self.process.poll() is not None:
            self._start_process()
        
        try:
            # Send command
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()
            
            # Read output character by character until we see the prompt pattern
            output = ""
            prompt_buffer = ""
            
            while True:
                char = self.process.stdout.read(1)
                if not char:
                    break
                
                output += char
                prompt_buffer += char
                
                # Keep only the last 7 characters in prompt_buffer to check for "metta+>"
                if len(prompt_buffer) > 7:
                    prompt_buffer = prompt_buffer[-7:]
                
                # Check if we've seen the prompt
                if prompt_buffer.endswith('metta+>'):
                    # Remove the prompt from the output
                    output = output[:-7]
                    break
            
            # Split into lines and filter out empty lines
            output_lines = [line.strip() for line in output.split('\n') if line.strip()]
            
            # Return only the last line as it contains the actual output
            return [output_lines[-1]] if output_lines else []
            
        except Exception as e:
            print(f"Error communicating with mettalog process: {e}")
            self._restart_process()
            return []
    
    def _restart_process(self):
        """Restart the mettalog process if it becomes unresponsive"""
        if self.process:
            self.process.terminate()
            self.process.wait()
        self._start_process()
    
    def __del__(self):
        """Clean up the process when the handler is destroyed"""
        if self.process:
            self.process.terminate()
            self.process.wait()

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
            self._send_command(f'!(compileAdd &kb {atom})')
            # Also append to file for persistence
            with open(self.file, 'a') as f:
                f.write(f'!(compileAdd &kb {atom})\n')

    def query(self, atom: str) -> Tuple[List[str], bool]:
        """Query the knowledge base and return results"""
        output_lines = self._send_command(f'!(query &kb (fromNumber 5) {atom})')
        
        # Parse the output to extract query results
        # This is a simplified parser - may need adjustment based on actual mettalog output format
        results = []
        for line in output_lines:
            if line.strip() and not line.startswith('!'):
                results.append(line.strip())
        
        proven = len(results) > 0
        return results, proven

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        return None
        
    def run(self, atom: str):
        """Run a command and return the output"""
        output_lines = self._send_command(atom)
        if not self._read_only:
            # Also append to file for persistence
            with open(self.file, 'a') as f:
                f.write(f"{atom}\n")
        return [output_lines]

    def run_clean(self, atom: str) -> List[str]:
        res = self.run(atom)
        return [self.clean_variable_names(str(elem)) for elem in res[0]]
                                                                             
    def store_kb_to_file(self):
        if self.read_only:
            print("Warning: Cannot store KB in read-only mode")
            return
        
        # Send command to match and output KB content
        self._send_command('!(match &kb $a $a)')
        # Also append to file for persistence
        with open(self.file, 'a') as f:
            f.write('!(match &kb $a $a)\n')

    def load_kb_from_file(self):
        if os.path.exists(self.file):
            # Load existing file content into the running process
            with open(self.file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self._send_command(line)
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

    print(handler.run("!(show-cs &kb)"))

    #print(handler.query("(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv)"))


