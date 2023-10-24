from utils import *
from .utils import *
from enum import Enum
from dataclasses import dataclass


class Column(Enum):
    LEFT = 1
    RIGHT = 2
    OUTPUT = 3

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @staticmethod
    def variants():
        return [Column.LEFT, Column.RIGHT, Column.OUTPUT]


@dataclass
class Cell:
    column: Column
    row: int

    def __key(self):
        return (self.row, self.column.value)

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.__key() < other.__key()
        return NotImplemented

    def __repr__(self) -> str:
        return "(" + str(self.row) + ", " + str(self.column.value) + ")"

    def __str__(self) -> str:
        return "(" + str(self.row) + ", " + str(self.column.value) + ")"

    def label(self, group_order: int) -> Scalar:
        """
        Returns the label, an inner-field element, representing a specified (column, row) position.

        The 'section' parameter should be 1 for left, 2 for right, and 3 for output.

        This function relies on the provided 'group_order' for calculating the label.
        """
        assert self.row < group_order  # Ensure that the row is within the valid range.

        # Perform polynomial interpolation
        return Scalar.roots_of_unity(group_order)[self.row] * self.column.value


def get_product_key(key1, key2):
    """
    Get the product key for the coefficients dictionary for the term `key1 * key2`.

    Args:
        key1 (str): The first key, which can be a constant (''), a variable, or a product key.
        key2 (str): The second key, which can be a constant (''), a variable, or a product key.

    Returns:
        str: The product key to use in the coefficients dictionary for the term `key1 * key2`.

    Note:
    Degrees higher than 2 are disallowed in the compiler, but we still allow them in the parser
    in case we find a way to compile them later.
    """
    # Split the keys into elements, removing empty elements
    key1_elements = [elem for elem in (key1 or "").split("*") if elem]
    key2_elements = [elem for elem in (key2 or "").split("*") if elem]

    # Combine and sort the elements from both keys
    combined_elements = sorted(key1_elements + key2_elements)

    # Reconstruct the final product key using '*'
    product_key = "*".join(combined_elements)

    return product_key


def is_valid_variable_name(name: str) -> bool:
    """
    Check if a string is a valid variable name.

    Args:
        name (str): The string to be checked as a variable name.

    Returns:
        bool: True if the string is a valid variable name, False otherwise.

    Conditions:
    1. The string must contain at least one character.
    2. All characters in the string must be alphanumeric, consisting of letters (A-Z or a-z) and numbers (0-9).
    3. The string cannot start with a numeric digit (0-9). It must begin with a letter.
    """
    return len(name) > 0 and name.isalnum() and name[0] not in "0123456789"
