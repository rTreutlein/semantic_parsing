from hyperon import MeTTa
import random
import string

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

    def add_atom_and_run_fc(self, atom):
        identifier = self.generate_random_identifier()
        self.metta.run(f'(= (kb) (: {identifier} {atom}))')
        res = self.metta.run('!(fc kb rb)')
        out = [elem.get_children()[2] for elem in res[0]]
        return out

    def run(self,atom):
        res = self.metta.run(atom)
        return res

if __name__ == "__main__":
    handler = MeTTaHandler()
    # Example usage
    result = handler.add_atom_and_run_fc("(ImplicationLink (PredicateNode b) (PredicateNode c))")
    result = handler.add_atom_and_run_fc("(ImplicationLink (PredicateNode a) (PredicateNode b))")
    print(result)
