from dataclasses import dataclass
from curve import *


@dataclass
class VerificationKey:
    """Verification key"""

    group_order: int

    Qm: G1Point
    """`[q_M(x)]₁` (commitment to multiplication selector polynomial)"""
    Ql: G1Point
    """`[q_L(x)]₁` (commitment to left selector polynomial)"""
    Qr: G1Point
    """`[q_R(x)]₁` (commitment to right selector polynomial)"""
    Qo: G1Point
    """`[q_O(x)]₁` (commitment to output selector polynomial)"""
    Qc: G1Point
    """`[q_C(x)]₁` (commitment to constants selector polynomial)"""
    S1: G1Point
    """`[S_σ1(x)]₁` (commitment to the first permutation polynomial `S_σ1(X))`"""
    S2: G1Point
    """`[S_σ2(x)]₁` (commitment to the second permutation polynomial `S_σ2(X))`"""
    S3: G1Point
    """`[S_σ3(x)]₁` (commitment to the third permutation polynomial `S_σ3(X))`"""
    X_2: G2Point
    """`[x]₂ = xH`, where `H` is a generator of `G_2`"""
    w: Scalar
    """`nth` root of unity, where `n` is the program's group order."""
