import dspy

dspy_program = dspy.ChainOfThought("question -> answer")

dspy_program.save("./testprogram/", save_program=True)

loaded_program = dspy.load("./testprogram/")

print(type(loaded_program))
