import py_ecc.bn128 as b
from dataclasses import dataclass
from curve import G1Point, G2Point
from poly import Polynomial, Basis
from compiler.program import CommonPreprocessedInput
from verifier import VerificationKey


# Recover the trusted setup from a file in the format used in
# https://github.com/iden3/snarkjs#7-prepare-phase-2
# Starting position of G1 points in power of tau ceremony file
SETUP_FILE_G1_STARTPOS = 80
# Byte 60 gives you the base-2 log of how many powers there are
SETUP_FILE_POWERS_POS = 60
# Size in bytes of one element in power of tau ceremony file
SETUP_ELEMENT_SIZE = 32

# Curve order: 21888242871839275222246405745257275088548364400416034343698204186575808495617
BN128_FIELD_MODULUS = b.field_modulus
# Generator for curve over FQ
# (FQ(1), FQ(2))
ECC_G1 = b.G1
# Generator for twisted curve over FQ2
# (
#     FQ2([
#         10857046999023057135944570762232829481370756359578518086990519993285655852781,
#         11559732032986387107991004021392285783925812861821192530917403151452391805634,
#     ]),
#     FQ2([
#         8495653923123431417604973247489272438418190587263600148770280649306958101930,
#         4082367875863433681332203403145435568316851327593401208105741076214120093531,
#     ]),
# )
ECC_G2 = b.G2


@dataclass
class Setup(object):
    # ([1]₁, [x]₁, ..., [x^{d-1}]₁)
    # = ( G, xG, ..., x^{d-1}G ), where G is a generator of G_1
    powers_of_tau: list[G1Point]
    # [x]₂ = xH, where H is a generator of G_2
    X2: G2Point

    @classmethod
    def from_file(cls, filename):
        # Read the content of the ptau file into a binary buffer.
        ptau_content = open(filename, "rb").read()
        # Extract the number of powers, which is located at a specific position in the file.
        powers = 2 ** ptau_content[SETUP_FILE_POWERS_POS]
        # Extract G1 points, starting at byte 80 in the file, and convert them to integers.
        values = [
            # Convert arrays of bytes to integers using little-endian byte order
            # by extracting a chunk of bytes from ptau_content and interpreting it as an integer.
            int.from_bytes(ptau_content[i : i + SETUP_ELEMENT_SIZE], "little")
            for i in range(
                # We start at byte 80 in the file, the beginning of G1 points.
                SETUP_FILE_G1_STARTPOS,
                # We go to byte 80 plus (32 bytes * the number of powers * 2)
                # because we need to consider both G1 and G2 points.
                SETUP_FILE_G1_STARTPOS + SETUP_ELEMENT_SIZE * powers * 2,
                # Step corresponds to an element size of 32 bytes,
                # so we move forward by 32 bytes for each iteration.
                SETUP_ELEMENT_SIZE,
            )
        ]
        # Ensure that the maximum value is less than BN128_FIELD_MODULUS.
        assert max(values) < BN128_FIELD_MODULUS

        # The points are encoded in a peculiar format, where all x and y values
        # are scaled by a factor (possibly for Montgomery optimization). We can
        # determine this factor since we know the first point is the generator.
        factor = b.FQ(values[0]) / b.G1[0]
        # Normalize all points by dividing each value by the previously extracted factor.
        values = [b.FQ(x) / factor for x in values]

        # Create (x, y) point pairs from the normalized values for future use.
        powers_of_tau = [(values[i * 2], values[i * 2 + 1]) for i in range(powers)]
        # Print the second (X^1) point from the extracted G1 side.
        print("Extracted G1 side, X^1 point: {}".format(powers_of_tau[1]))

        # Find the position where G2 points start in the 'ptau_content' by searching for 'target.'
        pos_start_g2 = next(
            (
                pos
                for pos, _ in enumerate(
                    # Iterate through the 'ptau_content' starting at the G1 position.
                    ptau_content[SETUP_FILE_G1_STARTPOS:],
                    SETUP_FILE_G1_STARTPOS,
                )
                # Check if the current 32-byte slice, converted to an integer in little-endian order,
                # equals the 'target' value (factor * b.G2[0].coeffs[0]).n.
                if int.from_bytes(
                    ptau_content[pos : pos + SETUP_ELEMENT_SIZE], "little"
                )
                == (factor * ECC_G2[0].coeffs[0]).n
            ),
            # If 'target' is not found, return 'None.'
            None,
        )
        assert pos_start_g2 is not None
        # Print the result if 'pos'
        print("Detected start of G2 side at byte {}.".format(pos_start_g2))

        # Create a pair of X2 points from the normalized values.
        X2 = (
            b.FQ2(
                [
                    # Extract and normalize the first component.
                    b.FQ(
                        int.from_bytes(
                            ptau_content[
                                pos_start_g2
                                + SETUP_ELEMENT_SIZE * 4 : pos_start_g2
                                + SETUP_ELEMENT_SIZE * 5
                            ],
                            "little",
                        )
                    )
                    / factor,
                    # Extract and normalize the second component.
                    b.FQ(
                        int.from_bytes(
                            ptau_content[
                                pos_start_g2
                                + SETUP_ELEMENT_SIZE * 5 : pos_start_g2
                                + SETUP_ELEMENT_SIZE * 6
                            ],
                            "little",
                        )
                    )
                    / factor,
                ]
            ),
            b.FQ2(
                [
                    # Extract and normalize the third component.
                    b.FQ(
                        int.from_bytes(
                            ptau_content[
                                pos_start_g2
                                + SETUP_ELEMENT_SIZE * 6 : pos_start_g2
                                + SETUP_ELEMENT_SIZE * 7
                            ],
                            "little",
                        )
                    )
                    / factor,
                    # Extract and normalize the fourth component.
                    b.FQ(
                        int.from_bytes(
                            ptau_content[
                                pos_start_g2
                                + SETUP_ELEMENT_SIZE * 7 : pos_start_g2
                                + SETUP_ELEMENT_SIZE * 8
                            ],
                            "little",
                        )
                    )
                    / factor,
                ]
            ),
        )
        # Ensure that the created X2 point is on curve 'b.b2.'
        assert b.is_on_curve(X2, b.b2)
        # Print the result to indicate that the X^1 point has been extracted.
        print("Extracted G2 side, X^1 point: {}".format(X2))
        return cls(powers_of_tau, X2)

    # def commit(self, values: Polynomial) -> G1Point:
    #     assert values.basis == Basis.LAGRANGE

    # def verification_key(self, pk: CommonPreprocessedInput) -> VerificationKey:
