from utils import *
from .utils import *
from typing import Optional
from dataclasses import dataclass

# from plonk.curve import Scalar
# from plonk.curve import Scalar


@dataclass
class GateWires:
    """
    `GateWires` Class

    In the context of PLONK (and similar protocols), a central concept is the transformation of a problem, where the goal is to find a value that satisfies a specific computation given as input, into a problem of finding a set of values that satisfy a set of mathematical equations.

    This transformation is achieved by representing the original problem, denoted as `P`, as a circuit composed of logical gates for addition and multiplication operations. This circuit is then converted into a system of equations, with the variables representing the values on the wires. Each gate corresponds to an equation, which encapsulates the mathematical relationship associated with that gate.

    These circuits, when expressed in PLONK, are typically represented as polynomials. The complexity of these polynomials depends on the number of gates in the circuit; more gates lead to higher-degree polynomials.

    It`s essential to note that each gate, also known as a constraint in SNARK circuits, is an equation that can express a limited amount of arithmetic. In both PLONK and rank-one constraint systems (R1CS), each gate can include only one multiplication of variables. While R1CS allows for an unlimited number of additions in a single gate, PLONK restricts this to just one.

    The `GateWires` class is responsible for managing the variable names associated with the left, right, and output wires of these gates or constraints.
    """

    L: Optional[str]
    R: Optional[str]
    O: Optional[str]

    def as_list(self) -> list[Optional[str]]:
        return [self.L, self.R, self.O]


@dataclass
class Gate:
    """Gate polynomial"""

    L: Scalar
    R: Scalar
    M: Scalar
    O: Scalar
    C: Scalar


@dataclass
class AssemblyEqn:
    """
    AssemblyEqn Class

    This class represents an assembly equation that maps wires to coefficients in the context of a cryptographic protocol like PLONK.

    An `AssemblyEqn` links the variables specified by `wires` to their respective coefficients in the form of `coeffs`.
    """

    wires: GateWires
    """An instance of the `GateWires` class that specifies variable names for left, right, and output wires."""
    coeffs: dict[Optional[str], int]
    """A dictionary that associates optional variable names with integer coefficients. These coefficients are used to express the mathematical relationships between the wires in the equation. The keys in the dictionary can be optional variable names, or they can be None to represent constants, and the corresponding values are integer coefficients."""

    def L(self) -> Scalar:
        return Scalar(-self.coeffs.get(self.wires.L, 0))

    def R(self) -> Scalar:
        if self.wires.R != self.wires.L:
            return Scalar(-self.coeffs.get(self.wires.R, 0))
        return Scalar(0)

    def C(self) -> Scalar:
        return Scalar(-self.coeffs.get("", 0))

    def O(self) -> Scalar:
        return Scalar(self.coeffs.get("$output_coeff", 1))

    def M(self) -> Scalar:
        if None not in self.wires.as_list():
            return Scalar(
                -self.coeffs.get(get_product_key(self.wires.L, self.wires.R), 0)
            )
        return Scalar(0)

    def gate(self) -> Gate:
        return Gate(self.L(), self.R(), self.M(), self.O(), self.C())


def evaluate(exprs: list[str], first_is_negative=False) -> dict[Optional[str], int]:
    """Evaluate an arithmetic expression and return a mapping of terms to coefficients"""

    # If the expression contains '+', split it into left and right parts
    # For example `a + b` gives {'a': 1, 'b': 1}
    if "+" in exprs:
        L = evaluate(exprs[: exprs.index("+")], first_is_negative)
        R = evaluate(exprs[exprs.index("+") + 1 :], False)

        # Merge the results for left and right expressions
        return L | R

    # If the expression contains '-', split it into left and right parts
    # For example `a - b` gives {'a': 1, 'b': -1}
    elif "-" in exprs:
        L = evaluate(exprs[: exprs.index("-")], first_is_negative)
        R = evaluate(exprs[exprs.index("-") + 1 :], True)

        # Merge the results for left and right expressions
        return L | R

    # If the expression contains '*', split it into left and right parts
    # For example `a * b * 2 * c * 2` gives {'a*b*c': 4}
    elif "*" in exprs:
        L = evaluate(exprs[: exprs.index("*")], first_is_negative)
        R = evaluate(exprs[exprs.index("*") + 1 :], first_is_negative)
        output = {}

        # Calculate the product of terms from left and right expressions
        for k1 in L.keys():
            for k2 in R.keys():
                output[get_product_key(k1, k2)] = L[k1] * R[k2]

        return output

    # If the expression contains more than one token, raise an exception
    # For example `a b` is not allowed
    elif len(exprs) > 1:
        raise Exception(
            "No operators found; expected sub-expression to be a unit: {}".format(
                exprs[1]
            )
        )

    # If the first token has a negative sign, remove it and toggle the first_is_negative flag
    elif exprs[0][0] == "-":
        return evaluate([exprs[0][1:]], not first_is_negative)

    # If the first token is a numeric value, convert it to an integer
    # For example `['2']` gives `{'': 2}` if not first_is_negative and `{'': -2}` if first_is_negative
    elif exprs[0].isnumeric():
        # Create a dictionary with an empty string as the key and the coefficient (-1 or 1) based on `first_is_negative`
        return {"": int(exprs[0]) * (-1 if first_is_negative else 1)}

    # If the first token is a valid variable name, set its coefficient based on the flag
    # For example `['a']` gives `{'a': 1}` if not first_is_negative and `{'a': 1}` if first_is_negative
    elif is_valid_variable_name(exprs[0]):
        # Create a dictionary with the variable name as the key and the coefficient (-1 or 1) based on `first_is_negative`
        return {exprs[0]: -1 if first_is_negative else 1}

    # If none of the above conditions match, raise an exception
    else:
        raise Exception("Unknown token: {}".format(exprs[0]))


def eq_to_assembly(eq: str) -> AssemblyEqn:
    """
    Converts an equation to a mapping of terms to coefficients, validates operations, and constructs an Assembly Equation.

    Args:
        eq (str): The equation in string format.

    Returns:
        AssemblyEqn: An Assembly Equation representing the input equation.

    This function takes an equation string and converts it into an Assembly Equation. It supports assignment (e.g., `x <== a * b`) and equality (e.g., `x === a * b`) operations. It also handles cases where the output variable may have a minus sign (e.g., `-x === a * b`).

    The process involves:
    - Extracting the output variable.
    - Converting the equation to a mapping of terms to coefficients.
    - Validating variable names and operations in the equation.
    - Constructing the gate structure.
    - Ensuring only allowed coefficients are present in the coefficient map.

    Additionally, this function verifies the equation's validity by checking the operation and variable constraints. It supports a maximum multiplicative degree of 2. If the equation defines a public variable, it creates an AssemblyEqn with the corresponding information. If the operation is unsupported, it raises an exception.

    Examples:
    - `a === 9` returns `([None, None, 'a'], {'': 9})`
    - `b <== a * c` returns `(['a', 'c', 'b'], {'a*c': 1})`
    - `d <== a * c - 45 * a + 987` returns `(['a', 'c', 'd'], {'a*c': 1, 'a': -45, '': 987})`

    Examples of invalid equations:
    - `7 === 7`  # Can't assign to non-variable
    - `a <== b * * c`  # Two times signs in a row
    - `e <== a + b * c * d`  # Multiplicative degree > 2
    """

    # Split the equation string into tokens based on spaces
    tokens = eq.rstrip("\n").split(" ")

    # Check if the equation type is assignment or equality
    if tokens[1] in ("<==", "==="):
        # Extract the output variable which is the first token
        out = tokens[0]

        # Convert the expression to coefficient map form
        coeffs = evaluate(tokens[2:])

        # Handle the special case where output variable starts with a minus sign
        # for example "-x === a * b"
        if out[0] == "-":
            # Remove the minus sign
            out = out[1:]
            # Set the output coefficient to -1
            coeffs["$output_coeff"] = -1

        # Check the validity of the output variable name
        if not is_valid_variable_name(out):
            raise Exception("Invalid out variable name: {}".format(out))

        # Gather list of variables used in the expression
        # Create an empty list to store the variables found in the expression
        variables = []
        # Iterate through the tokens starting from the third token (index 2)
        for t in tokens[2:]:
            # Remove a possible leading "-" sign to get the variable name
            var = t.lstrip("-")
            # Check if the variable name is valid and it hasn't been added to the list
            if is_valid_variable_name(var) and var not in variables:
                # If valid and not already in the list, add it to the variables list
                variables.append(var)

        # Construct the list of allowed coefficients
        allowed_coeffs = variables + ["", "$output_coeff"]
        if len(variables) == 0:
            pass
        elif len(variables) == 1:
            # If there's only one variable, duplicate it and add the corresponding coefficient
            variables.append(variables[0])
            allowed_coeffs.append(get_product_key(*variables))
        elif len(variables) == 2:
            # If there are two variables, add the corresponding coefficient
            allowed_coeffs.append(get_product_key(*variables))
        else:
            # If more than two variables are found, raise an exception since only two are allowed
            raise Exception(
                "Only up to 2 variables are allowed, but found {} variables.".format(
                    len(variables)
                )
            )

        # Check that only allowed coefficients are in the coefficient map
        # Check each coefficient key in the map for validity
        for key in coeffs.keys():
            if key not in allowed_coeffs:
                raise Exception(
                    "Invalid multiplication coefficient: '{}' is not allowed.".format(
                        key
                    )
                )
        # Create a list of wires to define the gate structure
        wires = variables + [None] * (2 - len(variables)) + [out]

        # Return the resulting Assembly Equation
        return AssemblyEqn(GateWires(wires[0], wires[1], wires[2]), coeffs)
    elif tokens[1] == "public":
        # Handle the case when the operation is to define a public variable.
        # Create an AssemblyEqn with the public variable information.
        return AssemblyEqn(
            GateWires(tokens[0], None, None),
            {tokens[0]: -1, "$output_coeff": 0, "$public": True},
        )
    else:
        # Handle the case when the operation is unsupported
        # For example `-x + y === a` is not supported due to the `+` on the lhs
        raise Exception("Unsupported operation: '{}'".format(tokens[1]))
