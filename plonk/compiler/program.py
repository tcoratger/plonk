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
