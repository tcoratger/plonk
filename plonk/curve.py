import py_ecc.bn128 as b
from typing import NewType
from py_ecc.fields.field_elements import FQ as Field

G1Point = NewType("G1Point", tuple[b.FQ, b.FQ])
G2Point = NewType("G2Point", tuple[b.FQ2, b.FQ2])


class Scalar(Field):
    field_modulus = b.curve_order
