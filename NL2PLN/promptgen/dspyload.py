import dspy

loaded_program = dspy.load("./program/")

loaded_program.save("program.json", save_program=False)

print(type(loaded_program))

#print(loaded_program.predict.signature)
#print(loaded_program.predict.extended_signature)
