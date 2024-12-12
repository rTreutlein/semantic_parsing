from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator

class ExamplePuzzleGenerator(LogicPuzzleGenerator):
    def generate_puzzle(self):
        return {
            'premises': """John always takes his umbrella when it rains.
This morning, John left his umbrella at home.""",
            'conclusion': """It wasn't raining this morning.""",
            'common_sense': """- If someone always does A when B occurs, and they didn't do A, then B didn't occur
- Morning is a time of day
- People can choose whether to take or leave items
- Umbrellas are items that can be carried"""
        }
