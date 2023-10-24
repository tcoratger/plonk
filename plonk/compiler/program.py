# from utils import *

from .utils import *
from poly import Polynomial, Basis
from .assembly import *


@dataclass
class CommonPreprocessedInput:
    """
    Common Preprocessed Input

    It encompasses the main polynomial `f(X)` with specific construction requirements:

    - `f(X)` should be designed to meet two critical criteria:
        - It must not reveal any non-public information to the verifier.
        - It must prevent the prover from altering fixed components of the circuit.

    The structure of `f(X)` is as follows:

    `f(X) = q_L(X) * a(X) + q_R(X) * b(X) + q_0(X) * c(X) + q_M(X) * a(X) * b(X) + q_C(X)`

    Where:
    - `a(X)`, `b(X)`, and `c(X)` are private polynomials constructed by the prover, committed, and sent to the verifier.
    - `q_L(X)`, `q_R(X)`, `q_M(X)`, `q_0(X)`, and `q_C(X)` are public polynomials (selector polynomials) that both the verifier and the prover can construct and commit to if necessary.

    Additionally, copy constraints are employed to enforce equality between variables across gates. These copy constraints are represented as permutation polynomials:
    - `S_σ1(X)`
    - `S_σ2(X)`
    - `S_σ3(X)`
    """

    group_order: int

    QM: Polynomial
    """`q_M(X)` multiplication selector polynomial"""
    QL: Polynomial
    """`q_L(X)` left selector polynomial"""
    QR: Polynomial
    """`q_R(X)` right selector polynomial"""
    QO: Polynomial
    """`q_O(X)` output selector polynomial"""
    QC: Polynomial
    """`q_C(X)` constants selector polynomial"""

    S1: Polynomial
    """`S_σ1(X)` first permutation polynomial"""
    S2: Polynomial
    """`S_σ2(X)` second permutation polynomial"""
    S3: Polynomial
    """`S_σ3(X)` third permutation polynomial"""


class Program:
    """
    Let us take an example with the Pythagorean theorem represented by the equations:
    - `a1 . b1 = c1`
    - `a2 . b2 = c2`
    - `a3 . b3 = c3`
    - `a4 + b4 = c4`

    This gives us four PLONK gates representing our Pythagorean circuit:
    - `0 . a1 + 0 . b1 + (-1) . c1 + 1 . a1b1 + 0 = 0`
    - `0 . a2 + 0 . b2 + (-1) . c2 + 1 . a2b2 + 0 = 0`
    - `0 . a3 + 0 . b3 + (-1) . c3 + 1 . a3b3 + 0 = 0`
    - `1 . a4 + 1 . b4 + (-1) . c4 + 0 . a4b4 + 0 = 0`

    Suppose you want to use these gates to check that `(3, 4, 5)` is a Pythagorean triple:
    - The `ai` (left values) will be `(3, 4, 5, 9)`
    - The `bi` (right values) will be `(3, 4, 5, 16)`
    - The `ci` (output values) will be `(9, 16, 25, 25)`

    Each equation should be satisfied after substituting in these values.

    Let us then collect our gate vectors that condense all the necessary information in a nice way so we don't have to write out those full gate equations.
    These vectors that will constitute our `Program` are called "selectors" and encode the structure of the circuit.
    - `qL = (0, 0, 0, 1)`
    - `qR = (0, 0, 0, 1)`
    - `q0 = (-1, -1, -1, -1)`
    - `qM = (1, 1, 1, 0)`
    - `qC = (0, 0, 0, 0)`
    """

    constraints: list[AssemblyEqn]
    group_order: int

    def __init__(self, constraints: list[str], group_order: int):
        """
        Initialize a Program instance.

        Parameters:
        - constraints (list[str]): A list of constraint strings representing the equations in the program.
        - group_order (int): The order of the group. It should be greater than or equal to the number of constraints.

        Raises:
        - Exception: If the group order is smaller than the number of constraints.
        """
        if len(constraints) > group_order:
            raise Exception("Group order too small")
        assembly = [eq_to_assembly(constraint) for constraint in constraints]
        self.constraints = assembly
        self.group_order = group_order

    def common_preprocessed_input(self) -> CommonPreprocessedInput:
        L, R, M, O, C = self.make_gate_polynomials()
        S = self.make_s_polynomials()
        return CommonPreprocessedInput(
            self.group_order,
            M,
            L,
            R,
            O,
            C,
            S[Column.LEFT],
            S[Column.RIGHT],
            S[Column.OUTPUT],
        )

    def make_s_polynomials(self) -> dict[Column, Polynomial]:
        # For each variable, extract the list of (column, row) positions
        # where that variable is used
        variable_uses: dict[Optional[str], Set[Cell]] = {None: set()}

        # Example:
        # For a list of wire constraints ['a', 'b', 'c'], the resulting 'variable_uses' dictionary would look like this:
        # {
        #     None: set(),
        #     'a': {(0, 1)},
        #     'b': {(0, 2)},
        #     'c': {(0, 3)}
        # }
        #
        # In this example, each variable ('a', 'b', 'c') is associated with the (row, column) positions where it is used in the constraints.
        # The positions are recorded in sets to avoid duplicates. The 'None' key in the dictionary is used to store positions where no variable is used.

        # Iterate through each constraint and identify the positions where each variable is used.
        for row, constraint in enumerate(self.constraints):
            for column, value in zip(Column.variants(), constraint.wires.as_list()):
                if value not in variable_uses:
                    variable_uses[value] = set()
                # Add (row, column) position
                variable_uses[value].add(Cell(column, row))

        # Iterate through rows beyond the constraints and to the group order and mark all cells as unused.
        # This is necessary to ensure that any cells not utilized by constraints are explicitly marked as unused.
        for row in range(len(self.constraints), self.group_order):
            # Iterate through all possible columns (variants) within a row.
            for column in Column.variants():
                # Add the cell (column, row) to the set associated with 'None',
                # indicating that it is not used by any variable.
                variable_uses[None].add(Cell(column, row))

        # Initialize dictionaries to store field elements in S_values for different columns.
        # We use three separate dictionaries for LEFT, RIGHT, and OUTPUT columns.
        S_values = {
            Column.LEFT: [Scalar(0)] * self.group_order,
            Column.RIGHT: [Scalar(0)] * self.group_order,
            Column.OUTPUT: [Scalar(0)] * self.group_order,
        }

        # Iterate through variables and their associated uses.
        for _, uses in variable_uses.items():
            # Sort the list of uses by (row, column) positions, ensuring a consistent order.
            sorted_uses = sorted(uses)

            # For each variable's uses, rotate the positions by one and store field elements in S_values.
            # For each list of positions, rotate by one.
            #
            # For example, let's consider a variable used in positions as follows:
            # (LEFT, 4), (LEFT, 7), and (OUTPUT, 2)
            # After processing, we store the field elements as follows:
            #
            # - at S[LEFT][7], the field element represents the position (LEFT, 4)
            # - at S[OUTPUT][2], the field element represents the position (LEFT, 7)
            # - at S[LEFT][4], the field element represents the position (OUTPUT, 2)
            for i, cell in enumerate(sorted_uses):
                # Determine the next position by taking the next element in the sorted list,
                # cycling back to the first element if needed.
                next_i = (i + 1) % len(sorted_uses)
                next_column = sorted_uses[next_i].column
                next_row = sorted_uses[next_i].row

                # Store the field element in S_values for the next (column, row) position.
                S_values[next_column][next_row] = cell.label(self.group_order)

        return {
            Column.LEFT: Polynomial(S_values[Column.LEFT], Basis.LAGRANGE),
            Column.RIGHT: Polynomial(S_values[Column.RIGHT], Basis.LAGRANGE),
            Column.OUTPUT: Polynomial(S_values[Column.OUTPUT], Basis.LAGRANGE),
        }

    def make_gate_polynomials(
        self,
    ) -> tuple[Polynomial, Polynomial, Polynomial, Polynomial, Polynomial]:
        """
        Generate gate polynomials, specifically L, R, M, O, C, as lists of length `group_order`.

        This function computes gate polynomials for a Plonk constraint system. The gate polynomials represent different
        parts of the constraint system, such as the left (L), right (R), mid (M), output (O), and control (C) sides of the gates.
        """

        # Create empty lists for storing coefficients
        L = [Scalar(0) for _ in range(self.group_order)]  # Left
        R = [Scalar(0) for _ in range(self.group_order)]  # Right
        M = [Scalar(0) for _ in range(self.group_order)]  # Multiplication
        O = [Scalar(0) for _ in range(self.group_order)]  # Output
        C = [Scalar(0) for _ in range(self.group_order)]  # Constant

        # Iterate through each constraint and extract gate coefficients
        for i, constraint in enumerate(self.constraints):
            gate = constraint.gate()
            L[i] = gate.L
            R[i] = gate.R
            M[i] = gate.M
            O[i] = gate.O
            C[i] = gate.C

        # Create Polynomial instances from the coefficient lists
        # using Lagrange basis
        return (
            Polynomial(L, Basis.LAGRANGE),
            Polynomial(R, Basis.LAGRANGE),
            Polynomial(M, Basis.LAGRANGE),
            Polynomial(O, Basis.LAGRANGE),
            Polynomial(C, Basis.LAGRANGE),
        )


Program(["c <== a * b"], 8).common_preprocessed_input()
