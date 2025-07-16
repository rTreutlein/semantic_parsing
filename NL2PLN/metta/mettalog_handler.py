import random
import string
import os
import subprocess
import time
import selectors
import re
from typing import List, Tuple

class TimeoutError(RuntimeError):
    """Raised when a mettalog command exceeds the allotted time."""
    pass

class MettalogHandler:                                                          
    def __init__(self, file: str = None, read_only: bool = False):
        self.file = file
        self._read_only = read_only
        self.process = None
        self.kb_ref = None
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.relpath(script_dir, start=os.getcwd())
        
        # Start the mettalog process
        self._start_process()
        
        # Initialize with compiler import and KB initialization
        if not self._read_only:
            path = os.path.join(relative_path, 'compiler')
            self._send_command(f"!(import! &self ./{path})")
            self._init_fresh_kb()

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
            
            # Read initial output until we see the first prompt
            self._wait_for_prompt()
            
        except FileNotFoundError:
            raise RuntimeError("mettalog executable not found. Please ensure it's installed and in PATH.")
    
    def _wait_for_prompt(self):
        """Wait for the mettalog prompt to appear, discarding any initial output"""
        # Use the same timeout mechanism as _send_command
        self._send_command("", timeout=30.0)

    def _send_command(self, command: str, log: bool = False, timeout: float = 180.0) -> str:
        """Send a command to the mettalog process and return the output.
        
        Args:
            command: The command to send
            log: Whether to log the output
            timeout: Maximum time in seconds to wait for completion
            
        Returns:
            The output string
            
        Raises:
            TimeoutError: If the command takes longer than timeout seconds
        """
        if self.process is None or self.process.poll() is not None:
            self._start_process()
        
        # Make stdout non-blocking so we can poll with a timeout
        fd = self.process.stdout.fileno()
        os.set_blocking(fd, False)
        
        sel = selectors.DefaultSelector()
        sel.register(fd, selectors.EVENT_READ)
        
        try:
            if command:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
            
            deadline = time.monotonic() + timeout
            chunks = []
            
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"mettalog command exceeded {timeout}s")
                
                # Wait for data with a small timeout to allow checking the deadline
                for key, _ in sel.select(timeout=min(remaining, 1.0)):
                    data = os.read(key.fd, 8192)
                    if not data:  # EOF
                        break
                    text = data.decode()
                    if log:
                        print(text, end='')
                    chunks.append(text)
                
                # Check if we've seen the prompt
                output = ''.join(chunks)
                if 'metta+>' in output:
                    break
            else:
                raise TimeoutError(f"mettalog command exceeded {timeout}s")
            
            # Remove the prompt and ANSI codes
            output = ''.join(chunks)
            if 'metta+>' in output:
                output = output.rsplit('metta+>', 1)[0]
            output = re.sub(r'\x1b\[[0-9;]*m', '', output).strip()
            return output
            
        finally:
            sel.close()
            os.set_blocking(fd, True)  # restore blocking mode
    
    def _restart_process(self):
        """Restart the mettalog process if it becomes unresponsive"""
        if self.process:
            self.process.terminate()
            self.process.wait()
        self._start_process()
    
    def _init_fresh_kb(self):
        """Initialize a fresh KB and store its reference"""
        kb_output = self._send_command("!(init-kb)")
        
        if not kb_output or not kb_output.strip():
            raise RuntimeError("Failed to initialize KB: no output from !(init-kb)")
        
        kb_output = kb_output.strip()
        if len(kb_output) < 2:
            raise RuntimeError(f"Failed to initialize KB: output too short: {kb_output}")
        
        # Remove first and last characters
        self.kb_ref = kb_output[1:-1]
    
    def create_fresh_environment(self):
        """Create a fresh KB environment without reloading dependencies"""
        if not self._read_only:
            self._init_fresh_kb()
    
    def close(self):
        """Close the process and clean up resources"""
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = None
    
    def __del__(self):
        """Clean up the process when the handler is destroyed"""
        if self.process:
            self.process.terminate()
            self.process.wait()

    @staticmethod
    def clean_variable_names(expr: str) -> str:
        """Remove #numbers from variable names like $var#1234"""
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*?)#\d+', r'$\1', expr)

    @property
    def read_only(self) -> bool:
        return self._read_only

    def add_atom(self, atom: str) -> str:
        if not self._read_only:
            res = self._send_command(f'!(compileAdd {self.kb_ref} {atom})')
            # Also append to file for persistence
            if self.file:
                with open(self.file, 'a') as f:
                    f.write(f'!(compileAdd {self.kb_ref} {atom})\n')
            return res

    def query(self, atom: str, log: bool = False, timeout: float = 300.0) -> Tuple[List[str], bool]:
        """Query the knowledge base and return results
        
        Args:
            atom: The atom to query
            log: Whether to log the output
            timeout: Maximum time in seconds to wait for completion
            
        Returns:
            Tuple of (results_list, proven_boolean)
        """
        output = self._send_command(f'!(query {self.kb_ref} (fromNumber 5) {atom})', log=log, timeout=timeout)
        
        results = self._parse_query_output(output)
        proven = len(results) > 0
        return results, proven

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        return None
        
    def run(self, atom: str, timeout: float = 300.0):
        """Run a command and return the output
        
        Args:
            atom: The command to run
            timeout: Maximum time in seconds to wait for completion
            
        Returns:
            The output string
        """
        return self._send_command(atom, timeout=timeout)

    def run_clean(self, atom: str, timeout: float = 300.0) -> List[str]:
        res = self.run(atom, timeout=timeout)
        return [self.clean_variable_names(str(elem)) for elem in res[0]]
                                                                             
    def store_kb_to_file(self):
        if self.read_only:
            print("Warning: Cannot store KB in read-only mode")
            return

        if not self.file:
            print("Warning: No file specified to store KB to")
            return
        
        # Send command to match and output KB content
        self._send_command(f'!(match {self.kb_ref} $a $a)')
        # Also append to file for persistence
        with open(self.file, 'a') as f:
            f.write(f'!(match {self.kb_ref} $a $a)\n')

    def load_kb_from_file(self):
        if not self.file:
            print("Warning: No file specified to load KB from")
            return

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
        if not self.file:
            print("Warning: No file specified to append to")
            return
        if self.read_only:
            print("Warning: Cannot append to file in read-only mode")
            return
        with open(self.file, 'a') as f:
            f.write(elem)

    def _parse_query_output(self, output: str) -> List[str]:
        """Parse the query output from mettalog format"""
        if not output or output.strip() == "[]":
            return []
        
        results = []
        try:
            # The output format appears to be: [(((: $var expr tv)) |- ((: rule conclusion tv)))]
            # We want to extract the entire elements from the list
            
            # Remove outer brackets and extract the content
            if output.startswith('[') and output.endswith(']'):
                content = output[1:-1].strip()
                
                # If there's content, add the entire element as a single result
                if content:
                    results.append(content)
            
        except Exception as e:
            print(f"Error parsing query output: {e}")
            print(f"Raw output: {output}")
        
        return results

if __name__ == '__main__':
    handler = MettalogHandler('kb_backup.metta', read_only=False)

    print("Testing:")

    print(handler.add_atom("(: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0))"))
    print(handler.add_atom("(: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0))"))

    print(handler.query("(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv)"))
