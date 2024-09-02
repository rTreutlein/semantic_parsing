from hyperon import MeTTa                                                    
import random                                                                
import string                                                                
import json                                                                  
                                                                             
class MeTTaHandler:                                                          
    def __init__(self):                                                      
        self.metta = MeTTa()                                                 
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
        return out
                                                                             
    def run(self, atom: str) -> List[str]:                                                     
        res = self.metta.run(atom)                                           
        return [str(r) for r in res]                                                           
                                                                             
    def store_kb_to_file(self, filename: str):                                    
        kb_content = self.metta.run('!(collapse (kb))')                                  
        with open(filename, 'w') as f:                                       
            json.dump(str(kb_content[0][0]), f)                                    
                                                                             
    def load_kb_from_file(self, filename: str):                                   
        with open(filename, 'r') as f:                                       
            kb_content = json.load(f)                                        
        self.metta.run(f'(= (kb) (superpose {kb_content}))')                             
                                                                             
if __name__ == "__main__":                                                   
    handler = MeTTaHandler()                                                 
    # Example usage                                                          
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode take_care_of) (PredicateNode last_longer))')                               
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode last_longer) (AndLink (PredicateNode requires_less_frequent_replacement) (PredicateNode requires_less_frequent_maintenance) ) )')
    print(result)                                                            
                                                                             
    # Example of storing and loading KB                                      
    handler.store_kb_to_file('kb_backup.json')                               
    handler.load_kb_from_file('kb_backup.json')
