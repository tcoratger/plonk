"""
plonk base module.

This is the principal module of the plonk project.
here you put your main classes and objects.

Be creative! do whatever you want!

If you want to replace this with a Flask application run:

    $ make init

and then choose `flask` as template.
"""

# example constant variable
NAME = "plonk"


from compiler.assembly import eq_to_assembly
from compiler.program import Program


# eq_to_assembly("c <== a * b * 2 * c * 2 + d * d * 65 - Z * Z * 65")
# eq_to_assembly("c <== z - a * b * 2 * c * 2")
# eq_to_assembly("-x === a * b + 2 * a")
# eq_to_assembly("-x + y === a")


# print(Program(["a === 9"], 8).constraints)
# print(Program(["b <== a * c"], 8).constraints)
# print(Program(["d <== a * c - 45 * a + 987"], 8).constraints)

res = Program(["c <== a * b"], 8).make_gate_polynomials()

print(Program(["c <== a * b"], 8).constraints)

print(res[0].values)
print(res[1].values)
print(res[2].values)
print(res[3].values)
print(res[4].values)
