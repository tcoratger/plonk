from utils import *
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
    constraints: list[AssemblyEqn]
    group_order: int

    def __init__(self, constraints: list[str], group_order: int):
        if len(constraints) > group_order:
            raise Exception("Group order too small")
        assembly = [eq_to_assembly(constraint) for constraint in constraints]
        self.constraints = assembly
        self.group_order = group_order


Program(["c <== a * b"], 8)
