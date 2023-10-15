from curve import Scalar
from enum import Enum


class Basis(Enum):
    LAGRANGE = 1
    MONOMIAL = 2


class Polynomial:
    values: list[Scalar]
    basis: Basis
