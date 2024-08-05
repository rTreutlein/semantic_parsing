from hyperon import MeTTa
import random
import string

def run_metta_from_file(file_path, metta):
    with open(file_path, 'r') as file:
        chainerstringhere = file.read()
        metta.run(chainerstringhere)

metta = MeTTa()

# Load the chainer.metta file
run_metta_from_file('chainer.metta', metta)

# Create a new knowledge base
metta.run('!(bind! &kb (new-space))')

# Load the rules.metta file into the knowledge base
run_metta_from_file('rules.metta', metta)


def generate_random_identifier(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def add_atom_and_run_fc(atom, metta):
    identifier = generate_random_identifier()
    res = metta.run('!(add-atom &kb (: ' + identifier + ' ' + atom + '))')

    res = metta.run('!(fc &kb (: ' + identifier + ' ' + atom + ') (fromNumber 3))')
    print(res)
