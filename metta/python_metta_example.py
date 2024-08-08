from hyperon import MeTTa
import random
import string

class MeTTaHandler:
    def __init__(self):
        self.metta = MeTTa()
        self.run_metta_from_file('chainer.metta')
        self.metta.run('!(bind! &kb (new-space))')
        self.run_metta_from_file('rules.metta')

    def run_metta_from_file(self, file_path):
        with open(file_path, 'r') as file:
            chainerstringhere = file.read()
            self.metta.run(chainerstringhere)

    @staticmethod
    def generate_random_identifier(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def add_atom_and_run_fc(self, atom):
        identifier = self.generate_random_identifier()
        res = self.metta.run(f'!(add-atom &kb (: {identifier} {atom}))')
        return res
        #res = self.metta.run(f'!(fc &kb (: {identifier} {atom}) (fromNumber 1))')
        #return res

if __name__ == "__main__":
    handler = MeTTaHandler()
    # Example usage
    result = handler.add_atom_and_run_fc("(Concept \"example\")")
    print(result)
