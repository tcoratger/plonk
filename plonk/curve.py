import py_ecc.bn128 as b
from typing import NewType
from py_ecc.fields.field_elements import FQ as Field

G1Point = NewType("G1Point", tuple[b.FQ, b.FQ])
G2Point = NewType("G2Point", tuple[b.FQ2, b.FQ2])


class Scalar(Field):
    """
    Represents a scalar value over the finite field `𝔽p` where `p` is the order of the specified curve.

    In this context, a finite field is a set of elements with a finite number of members. In cryptography, it's often
    a finite field of integers modulo `p`, where `p` is a prime number. This is represented as `GF(p)` or `𝔽p`.

    For instance:
    - `𝔽2` or `GF(2)` consists of `[0, 1]`
    - `𝔽11` or `GF(11)` consists of `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`
    - `𝔽23` or `GF(23)` consists of `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, ... 22]`

    Any mathematical operation performed on instances of this class will yield a value
    that is reduced modulo the order of the curve. This is a crucial property in elliptic curve cryptography,
    ensuring scalar values stay within a valid range.
    """

    field_modulus = b.curve_order
