from curve import Scalar
from enum import Enum


class Basis(Enum):
    LAGRANGE = 1
    MONOMIAL = 2


class Polynomial:
    values: list[Scalar]
    basis: Basis

    def __init__(self, values: list[Scalar], basis: Basis):
        assert all(isinstance(x, Scalar) for x in values)
        assert isinstance(basis, Basis)
        self.values = values
        self.basis = basis
