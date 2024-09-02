import json
import random
import string
from typing import List
from synthesizepy.synthesizer import (
    Atom, Expression, kb, rb, parse_sexpr, print_sexpr, fc
)

class SynthesizerHandler:
    def __init__(self):
        self.kb = kb()
        self.rb = rb()

    @staticmethod
    def generate_random_identifier(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def add_atom_and_run_fc(self, atom: str) -> List[str]:
        identifier = self.generate_random_identifier()
        parsed_atom = parse_sexpr(atom)
        new_expression = Expression(Atom('Symbol', ':'), (Atom('Symbol', identifier), parsed_atom))
        self.kb.append(new_expression)
        
        self.kb = fc(self.kb, self.rb)
        
        return [print_sexpr(elem) for elem in self.kb]

    def store_kb_to_file(self, filename: str):
        kb_content = [print_sexpr(expr) for expr in self.kb]
        with open(filename, 'w') as f:
            json.dump(kb_content, f)

    def load_kb_from_file(self, filename: str):
        with open(filename, 'r') as f:
            kb_content = json.load(f)
        self.kb = [parse_sexpr(expr) for expr in kb_content]

if __name__ == "__main__":
    handler = SynthesizerHandler()
    # Example usage
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode take_care_of) (PredicateNode last_longer))')
    print(result)
    result = handler.add_atom_and_run_fc('(ImplicationLink (PredicateNode last_longer) (AndLink (PredicateNode requires_less_frequent_replacement) (PredicateNode requires_less_frequent_maintenance)))')
    print(result)

    # Example of storing and loading KB
    handler.store_kb_to_file('kb_backup.json')
    handler.load_kb_from_file('kb_backup.json')
