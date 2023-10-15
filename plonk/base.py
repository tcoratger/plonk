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


# eq_to_assembly("c <== a * b * 2 * c * 2 + d * d * 65 - Z * Z * 65")
# eq_to_assembly("c <== z - a * b * 2 * c * 2")
# eq_to_assembly("-x === a * b + 2 * a")
# eq_to_assembly("-x + y === a")


eq_to_assembly("a === 9")
eq_to_assembly("b <== a * c")
eq_to_assembly("d <== a * c - 45 * a + 987")
