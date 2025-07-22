from hyperon import MeTTa
import random
import string
import os
from typing import List, Tuple

class MeTTaHandler:                                                          
    def __init__(self, file: str, read_only: bool = False):
        self.metta = MeTTa()
        self.file = file
        self._read_only = read_only
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.relpath(script_dir,start=os.getcwd())
        print(os.getcwd())
        print(script_dir)
        print(relative_path)
        #self.metta.run(f"!(import! &self {os.path.join(script_dir, 'compiler')})")
        if (relative_path.startswith('.')):
            relative_path = relative_path[1:]
        path = os.path.join(relative_path, 'chainer/compiler').replace('/', ':')
        print(path)
        self.metta.run(f"!(import! &self {path})")
        #self.metta.load_module_at_path(os.path.join(script_dir, 'compiler.metta'))
        self.run("!(bind! &kb (init-kb))")
        print(self.run("!(&kb)"))

    @staticmethod
    def clean_variable_names(expr: str) -> str:
        """Remove #numbers from variable names like $var#1234"""
        import re
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*?)#\d+', r'$\1', expr)

    @property
    def read_only(self) -> bool:
        return self._read_only

    def add_atom(self, atom: str) -> None:
        self.metta.run(f'!(compileAdd &kb {atom})')

    def query(self, atom: str) -> Tuple[List[str], bool]:
        results = self.metta.run(f'!(query &kb (fromNumber 5) {atom})')
        # If we got any results back, the conclusion was proven
        proven = len(results[0]) > 0
        return [str(elem) for elem in results[0]], proven

    def add_to_context(self, atom: str) -> str | None:
        """Add atom to context if no conflict exists.
        
        Returns:
            None if atom was added successfully
            The conflicting atom string if a conflict was found
        """
        return None
        #exp = self.metta.parse_single(atom)
        #inctx = self.metta.run("!(match &kb (: " + str(exp.get_children()[1]) + " $a) $a)")[0]

        #
        #if len(inctx) == 0:
        #    self.metta.run("!(add-atom &kb " + atom + ")")
        #    return None

        #unify = self.metta.run("!(unify " + str(exp.get_children()[2]) + " (match &kb (: " + str(exp.get_children()[1]) + " $a) $a)  same diff)")

        #if str(unify[0][0]) == "same":
        #    self.metta.run("!(add-atom &kb " + atom + ")")
        #    return None
        #else:
        #    return inctx

        
    def run(self, atom: str):
        return self.metta.run(atom)

    def run_clean(self, atom: str) -> List[str]:
        res = self.metta.run(atom)
        return [self.clean_variable_names(str(elem)) for elem in res[0]]
                                                                             
    def store_kb_to_file(self):
        if self.read_only:
            print("Warning: Cannot store KB in read-only mode")
            return
        kb_content = self.metta.run('!(match &kb $a $a)')
        with open(self.file, 'w') as f:                                       
            for element in kb_content[0]:
                f.write(str(element) + "\n")
                                                                             
    def load_kb_from_file(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:                                       
                for elment in f:
                    self.metta.run(f'!(add-atom &kb {elment})')
        else:
            print(f"Warning: File {self.file} does not exist. No KB loaded.")

    def append_to_file(self, elem: str):
        if self.read_only:
            print("Warning: Cannot append to file in read-only mode")
            return
        with open(self.file, 'a') as f:
            f.write(elem)

if __name__ == '__main__':
    handler = MeTTaHandler('kb_backup.json', read_only=False)

    print("Adding atoms")

    print(handler.add_atom("(: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0))"))
    print(handler.add_atom("(: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0))"))

    print(handler.run("!(show-cs &kb)"))

    print(handler.query("(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv)"))

    #print(handler.add_atom("(: rule1 (WithTV (Implication (And (Book $book) (CheckoutCount $book $count) (GreaterThan $count 10)) (NeedsInspection $book)) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact1 (WithTV (Book vanishing_key) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact2 (WithTV (SinceLastInspection vanishing_key 15) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact3 (WithTV (CheckoutCount vanishing_key 15) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact4 (WithTV (GreaterThan 15 10) (STV 1.0 1.0)))"))

    #print(handler.query("(: $query (WithTV (NeedsInspection vanishing_key) $tv))"))


    #print(handler.run("!(compile (: rule1 (WithTV (Implication (WonPrize $book) (Or (InAwardsSection $book) (InNewReleasesSection $book))) (STV 1.0 1.0))))"))

    #print(handler.add_atom("(: rule1 (WithTV (Implication (WonPrize $book) (Or (InAwardsSection $book) (InNewReleasesSection $book))) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact1 (WithTV (Book whispers_of_dawn) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact2 (WithTV (WonStellarPrize whispers_of_dawn) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact3 (WithTV (WonPrize whispers_of_dawn) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact4 (WithTV (Not (InNewReleasesSection whispers_of_dawn)) (STV 1.0 1.0)))"))

    
    #print(handler.query("(: $query (WithTV (InAwardsSection whispers_of_dawn) $tv))"))

    #print(handler.add_atom("(: fact1 (WithTV (Book atlas_ancient_civilizations) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact2 (WithTV (ContainsMaterialBefore atlas_ancient_civilizations -500) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: rule1 (WithTV (Implication (And (Book $book) (ContainsMaterialBefore $book -500)) (ReferenceBook $book)) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact1 (WithTV (Book atlas_ancient_civilizations) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact2 (WithTV (ReferenceBook atlas_ancient_civilizations) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: fact3 (WithTV (ContainsHistoricalMaps atlas_ancient_civilizations) (STV 1.0 1.0)))"))
    #print(handler.add_atom("(: rule1 (WithTV (Implication (And (ReferenceBook $book) (ContainsHistoricalMaps $book)) (StoredInWestWing $book)) (STV 1.0 1.0)))"))

    #print(handler.query("(: $query (WithTV (StoredInWestWing atlas_ancient_civilizations) $tv))"))
