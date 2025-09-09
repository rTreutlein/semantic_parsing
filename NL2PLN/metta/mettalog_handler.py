import random
import string
import os
import subprocess
import time
import selectors
import re
import time
from typing import List, Tuple

from pympler import tracker

class TimeoutError(RuntimeError):
    """Raised when a mettalog command exceeds the allotted time."""
    pass

class MettalogHandler:                                                          
    def __init__(self):
        self.process = None
        self.kb_ref = None
        
        
        # Start the mettalog process
        self._start_process()
        
        # Initialize with compiler import and KB initialization
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.relpath(script_dir, start=os.getcwd())
        path = os.path.join(relative_path, 'chainer/compiler')
        self._send_command(f"!(import! &self {path})")
        self.init_fresh_kb()

    def _start_process(self):
        """Start the mettalog process with stdin/stdout pipes"""
        try:
            self.process = subprocess.Popen(
                ['mettalog'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
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
        self._send_command("\n", timeout=30.0)

    def _send_command(self, command: str, log: bool = False, timeout: float = 240.0) -> str:
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

        # -------------------------------------------------------------------
        # Flush any bytes left over from the previous command so we start with
        # an empty buffer.  This prevents stale prompts/output from confusing
        # the current read loop and guarantees we always wait for the *new*
        # prompt that will appear after the command we are about to send.
        # -------------------------------------------------------------------
        try:
            while True:
                leftover = os.read(fd, 8192)
                if not leftover:
                    break      # EOF
        except BlockingIOError:
            pass               # no data pending
        
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
                
                # Check if we've seen the prompt (strip ANSI codes first)
                output = re.sub(r'\x1b\[[0-9;]*m', '', ''.join(chunks))
                if 'metta+>' in output:
                    break
            else:
                raise TimeoutError(f"mettalog command exceeded {timeout}s")
            
            # Remove the prompt and ANSI codes
            raw_output = ''.join(chunks)
            clean_output = re.sub(r'\x1b\[[0-9;]*m', '', raw_output)
            if 'metta+>' in clean_output:
                clean_output = clean_output.rsplit('metta+>', 1)[0]
            # Return only the last non-empty line before the prompt
            lines = [ln.strip() for ln in clean_output.splitlines() if ln.strip()]
            last_line = lines[-1] if lines else ''
            return last_line
            
        finally:
            sel.close()
            os.set_blocking(fd, True)  # restore blocking mode
    
    def init_fresh_kb(self):
        """Initialize a fresh KB and store its reference"""
        self.kb_ref = self._send_command("!(init-kb)")[1:-1]
    
    def close(self):
        """Close the process and clean up resources"""
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
        self.process = None

    # ------------------------------------------------------------------
    # Support pickling / deepcopy (e.g. by DSPy) by excluding the
    # non-picklable subprocess handle and recreating it on demand.
    # ------------------------------------------------------------------
    def __getstate__(self):
        """Return a picklable representation for deepcopy/pickling."""
        state = self.__dict__.copy()
        # The subprocess.Popen object cannot be pickled.
        state["process"] = None
        return state

    def __setstate__(self, state):
        """Restore state; restart the mettalog process lazily."""
        self.__dict__.update(state)
        if self.process is None:
            try:
                self._start_process()
            except Exception:
                # If restart fails we leave the object usable so other
                # attributes can still be inspected; commands will raise.
                self.process = None
    
    def __del__(self):
        """Clean up the process when the handler is destroyed"""
        proc = getattr(self, "process", None)
        if proc is not None:
            try:
                proc.terminate()
                proc.wait()
            except Exception:
                # Ignore any errors raised during interpreter shutdown
                pass

    def add_atom(self, atom: str) -> str:
        return self._send_command(f'!(compileAdd {self.kb_ref} {atom})')

    def query(self, atom: str, log: bool = False, timeout: float = 300.0) -> List[str]:
        """Query the knowledge base and return results
        
        Args:
            atom: The atom to query
            log: Whether to log the output
            timeout: Maximum time in seconds to wait for completion
            
        Returns:
            Tuple of (results_list, proven_boolean)
        """
        output = self._send_command(f'!(query {self.kb_ref} (fromNumber 5) {atom})', log=log, timeout=timeout)
        return [item.strip() for item in output[1:-1].split(',') if item.strip()]

if __name__ == '__main__':
    handler = MettalogHandler()

    print("Testing:")

    start = time.time()
    #print(handler.add_atom("(: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0))"))

    #tr = tracker.SummaryTracker()
    #tr.print_diff()
    print(handler._send_command("(print hello)"))
    #tr.print_diff()
    print(handler._send_command("(print hello)"))
    #tr.print_diff()
    end = time.time()
    print("It took", end - start)
    #print(handler.add_atom("(: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0))"))

    #print(handler.query("(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv)"))

    #print(handler.add_atom("(: library_between (WithTV (Between Library Bank PostOffice) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: library_on_main (WithTV (OnStreet Library MainStreet) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: bank_on_main (WithTV (OnStreet Bank MainStreet) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: post_office_on_main (WithTV (OnStreet PostOffice MainStreet) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: bank_left_of_library (WithTV (LeftOf Bank Library North) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: same_side_relation (WithTV (SameSideOf Library Bank PostOffice MainStreet) (STV 1.0 1.0)))"))

    #print(handler.query("(: $query (WithTV (OrderFromLeftToRight $building1 $building2 $building3 North) $tv))"))

    #print(handler.add_atom("(: fact1 (A a1) ntv)"))
    #print(handler.add_atom("(: fact2 (A a2) ntv)"))

    #print(handler.query("(: $query (A $a) ntv)"))
