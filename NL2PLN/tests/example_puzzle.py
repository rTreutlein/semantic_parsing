import dspy
from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator

class ExamplePuzzleGenerator(LogicPuzzleGenerator):
    def generate_puzzle(self, numberOfPremises: int = 3) -> dspy.Prediction:
        return Prediction(reasoning="I'll create a story about a library and its book lending policies. The premises will include complex relationships between borrowers, books, and librarians, with some nested quantifiers about lending permissions. Not all premises will be directly used in reaching the conclusion.",
                          premises=['Every librarian at Central Library must approve any book that gets added to the restricted section',
                                    "James is the only librarian who has not approved the book 'Ancient Mysteries'",
                                    'All books about mythical creatures are required to be in the restricted section',
                                    "'Dragons and Their Habits' is a new book about mythical creatures",
                                    "The library catalogue shows that 'Ancient Mysteries' contains a chapter about dragons"],
                          deduction=[(['Every librarian at Central Library must approve any book that gets added to the restricted section',
                                       'All books about mythical creatures are required to be in the restricted section',
                                       "'Dragons and Their Habits' is a new book about mythical creatures"],
                                      "Dragons and Their Habits requires all librarians' approval"),
                                     (["Dragons and Their Habits requires all librarians' approval",
                                       "James is the only librarian who has not approved the book 'Ancient Mysteries'"],
                                      "'Dragons and Their Habits' cannot be added to the library collection until James approves it")],
                          conclusion="'Dragons and Their Habits' cannot be added to the library collection until James approves it"                                                                                                                                                                                                                                                                             )
