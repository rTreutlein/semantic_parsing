from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator

class ExamplePuzzleGenerator(LogicPuzzleGenerator):
    def generate_puzzle(self):
        return {
            'premises': """John always takes his umbrella when it rains.
This morning, John left his umbrella.""",
            'conclusion': """It wasn't raining this morning.""",
            'common_sense': ""
        }
