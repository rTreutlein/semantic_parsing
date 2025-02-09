from hyperon import MeTTa
import random
import string
import os
from typing import List

class MeTTaHandler:                                                          
    def __init__(self, file: str):
        self.metta = MeTTa()
        self.file = file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.run("!(bind! &kb (new-space))")
        self.run_metta_from_file(os.path.join(script_dir, 'chainer.metta'))
        self.run_metta_from_file(os.path.join(script_dir, 'rules.metta'))

    def run_metta_from_file(self, file_path):                                
        with open(file_path, 'r') as file:                                   
            chainerstringhere = file.read()                                  
            self.metta.run(chainerstringhere)                                
                                                                             
    @staticmethod                                                            
    def generate_random_identifier(length=8):                                
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))                                                                   
                                                                             
    def add_atom_and_run_fc(self, atom: str) -> List[str]:
        identifier = self.generate_random_identifier()                       
        self.metta.run(f'!(add-atom &kb {atom})')                  
        res = self.metta.run(f'!(fc &kb {atom})')
        out = [str(elem.get_children()[2]) for elem in res[0]]               
        self.append_to_file(f"(: {identifier} {atom})")
        [self.append_to_file(str(elem)) for elem in res[0]]
        return out

    def bc(self, atom: str) -> List[str]:
        return self.metta.run('!(bc &kb (S (S (S Z))) ' + atom + ')')

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        exp = self.metta.parse_single(atom)
        inctx = self.metta.run("!(match &kb (: " + str(exp.get_children()[1]) + " $a) $a)")
        
        if len(inctx[0]) == 0:
            self.metta.run("!(add-atom &kb " + atom + ")")
            return None
            
        existing_atom = str(inctx[0][0])
        if str(exp.get_children()[2]) == existing_atom:
            return None
        else:
            return existing_atom

        
    def run(self, atom: str):
        return self.metta.run(atom)
                                                                             
    def store_kb_to_file(self):
        kb_content = self.metta.run('!(collapse (kb))')                                  
        kb_str = str(kb_content[0][0])[1:-1]
        with open(self.file, 'w') as f:                                       
            f.write(kb_str)
                                                                             
    def load_kb_from_file(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:                                       
                kb_content = "(" + f.read() + ")"
            self.metta.run("!(match &self (= (kb) $n) (remove-atom &self (= (kb) $n)))")
            self.metta.run(f'(= (kb) (superpose {kb_content}))')
        else:
            print(f"Warning: File {self.file} does not exist. No KB loaded.")

    def append_to_file(self, elem: str):
        with open(self.file, 'a') as f:
            f.write(elem)

                                                                             
if __name__ == "__main__":
    handler = MeTTaHandler('kb_backup.json')
    with open('kb_backup.json', 'w') as f:
        f.write("")

    print("\nTesting add_atom_and_run_fc:")
    
    # Test 1: Adding a new atom and running forward chaining
    atom1 = "(: ab (-> (: $a (PredicateNode A)) (PredicateNode B)))"
    print(f"Adding atom and running fc: {atom1}")
    result = handler.add_atom_and_run_fc(atom1)
    print(f"Forward chaining results: {result}")

    # Test 2: Adding another atom to trigger more inferences
    atom2 = "(: a (PredicateNode A))"
    print(f"\nAdding second atom: {atom2}")
    result = handler.add_atom_and_run_fc(atom2)
    print(f"Forward chaining results: {result}")

    print("\nTesting add_to_context:")
    
    # Test 1: Adding a new atom (should succeed)
    atom3 = "(: test1 (ImplicationLink (PredicateNode X) (PredicateNode Y)))"
    result = handler.add_to_context(atom3)
    print(f"Adding {atom3}")
    print(f"Result: {result}")  # Should print None
    
    # Test 2: Adding conflicting atom (should return existing atom)
    atom4 = "(: test1 (ImplicationLink (PredicateNode X) (PredicateNode Z)))"
    print(f"\nAdding conflicting atom: {atom4}")
    result = handler.add_to_context(atom4)
    print(f"Result: {result}")  # Should print the existing atom
    
    # Verify final context state
    print("\nFinal context state:")
    context = handler.run("!(match &kb (: $a $b) $b)")
    print(context[0])
