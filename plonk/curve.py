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

    @classmethod
    def root_of_unity(cls, group_order: int):
        """
        Gets the first root of unity of a given group order

        To get an 𝑛-th root of unity, you generate a random non-zero 𝑥 in the field. Then:

        (𝑥^((𝑞−1)/𝑛))^𝑛 = 𝑥^(𝑞−1) = 1

        Therefore, 𝑥^((𝑞−1)/𝑛) is an 𝑛-th root of unity. Note that you can end up with any of the 𝑛 𝑛-th roots of unity (including 1 itself), each with probability 1/𝑛.

        """
        return Scalar(5) ** ((cls.field_modulus - 1) // group_order)

    @classmethod
    def roots_of_unity(cls, group_order: int):
        """
        Gets the full list of roots of unity of a given group order.

        In a finite field of size 𝑞, the multiplicative subgroup has order 𝑞−1
        (i.e., all elements are invertible except 0).

        - If 𝑛 is relatively prime to 𝑞−1, then there is only one 𝑛-th root of unity, i.e. 1 itself.
        - If 𝑛 divides 𝑞−1, then there are 𝑛 roots of unity.
        """
        o = [Scalar(1), cls.root_of_unity(group_order)]
        while len(o) < group_order:
            o.append(o[-1] * o[1])
        return o
