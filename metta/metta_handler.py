from hyperon import MeTTa
import random
import string
import json
from typing import List
                                                                             
class MeTTaHandler:                                                          
    def __init__(self, file: str):                                                      
        self.metta = MeTTa()                                                 
        self.file = file
        self.run_metta_from_file('metta/Num.metta')                          
        self.run_metta_from_file('metta/Intersection.metta')                 
        self.run_metta_from_file('metta/sythesize.metta')                    
        self.run_metta_from_file('metta/rules_pln.metta')                    

                                                                             
    def run_metta_from_file(self, file_path):                                
        with open(file_path, 'r') as file:                                   
            chainerstringhere = file.read()                                  
            self.metta.run(chainerstringhere)                                
                                                                             
    @staticmethod                                                            
    def generate_random_identifier(length=8):                                
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))                                                                   
                                                                             
    def add_atom_and_run_fc(self, atom: str) -> List[str]:
        identifier = self.generate_random_identifier()                       
        self.metta.run(f'(= (kb) (: {identifier} {atom}))')                  
        res = self.metta.run('!(fc kb rb)')                                  
        out = [str(elem.get_children()[2]) for elem in res[0]]               
        self.append_to_file(f"(: {identifier} {atom})")
        [self.append_to_file(str(elem)) for elem in res[0]]
        return out
                                                                             
    def run(self, atom: str):
        return self.metta.run(atom)                                           
                                                                             
    def store_kb_to_file(self):
        kb_content = self.metta.run('!(collapse (kb))')                                  
        kb_str = str(kb_content[0][0])[1:-1]
        with open(self.file, 'w') as f:                                       
            f.write(kb_str)
                                                                             
    def load_kb_from_file(self):
        import os
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
    # Example usage                                                          
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode take_care_of) (PredicateNode last_longer))')                               
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode last_longer) (AndLink (PredicateNode requires_less_frequent_replacement) (PredicateNode requires_less_frequent_maintenance) ) )')
    print(result)                                                            
                                                                             
    # Example of storing and loading KB                                      
    handler.load_kb_from_file()
    print(handler.run("!(kb)"))
