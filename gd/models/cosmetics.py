"""
## .models.icons

The module containing all the classes and methods related to customization and icons.
"""

from dataclasses import dataclass
from .enums import Gamemode
from typing import Union, Dict, List

COLORS_LIST: Dict[int, int] = {
    0: 0x7DFF00, 1: 0x00FF00, 2: 0x00FF7D, 3: 0x00FFFF, 4: 0x007DFF, 5: 0x0000FF, 6: 0x7D00FF, 7: 0xFF00FF, 8: 0xFF007D, 9: 0xFF0000, 10: 0xFF7D00,
    11: 0xFFFF00, 12: 0xFFFFFF, 13: 0xB900FF, 14: 0xFFB900, 15: 0x000000, 16: 0x00C8FF, 17: 0xAFAFAF, 18: 0x5A5A5A, 19: 0xFF7D7D, 20: 0x00AF4B,
    21: 0x007D7D, 22: 0x004BAF, 23: 0x4B00AF, 24: 0x7D007D, 25: 0xAF004B, 26: 0xAF4B00, 27: 0x7D7D00, 28: 0x4BAF00, 29: 0xFF4B00, 30: 0x963200, 
    31: 0x966400, 32: 0x649600, 33: 0x009664, 34: 0x006496, 35: 0x640096, 36: 0x960064, 37: 0x960000, 38: 0x009600, 39: 0x000096, 40: 0x7DFFAF, 
    41: 0x7D7DFF, 42: 0xFFFA7F, 43: 0xFA7FFF, 44: 0x00FFC0, 45: 0x50320E, 46: 0xCDA576, 47: 0xB680FF, 48: 0xFF3A3A, 49: 0x4D4D8F, 50: 0x000A4C, 
    51: 0xFDD4CE, 52: 0xBEB5FF, 53: 0x700000, 54: 0x520200, 55: 0x380106, 56: 0x804F4F, 57: 0x7A3535, 58: 0x512424, 59: 0xA36246, 60: 0x754936,
    61: 0x563528, 62: 0xFFB972, 63: 0xFFA040, 64: 0x66311E, 65: 0x5B2700, 66: 0x472000, 67: 0xA77B4D, 68: 0x6D5339, 69: 0x513E2A, 70: 0xFFFFC0,
    71: 0xFDE0A0, 72: 0xC0FFA0, 73: 0xB1FF6D, 74: 0xC0FFE0, 75: 0x94FFE4, 76: 0x43A18A, 77: 0x316D5F, 78: 0x265449, 79: 0x006000, 80: 0x004000,
    81: 0x006060, 82: 0x004040, 83: 0xA0FFFF, 84: 0x010770, 85: 0x00496D, 86: 0x00324C, 87: 0x002638, 88: 0x5080AD, 89: 0x335375, 90: 0x233C56,
    91: 0xE0E0E0, 92: 0x3D068C, 93: 0x370860, 94: 0x404040, 95: 0x6F49A4, 96: 0x54367F, 97: 0x422A63, 98: 0xFCB5FF, 99: 0xAF57AF, 100: 0x824382,
    101: 0x5E315E, 102: 0x808080, 103: 0x66033E, 104: 0x470134, 105: 0xD2FF32, 106: 0x76BDFF,
}
"""A dictionary mapping all the color ids to their corresponding hex colors.

**Minimum ID:** 0, **Maximum ID:** 106
"""

def color_id_to_hex(color_id: int) -> Union[int, None]:
    """
    Returns the hexadecimal color code for the given color ID. If not found, returns None.

    :param color_id: The ID of the color.
    :type color_id: int
    :return: The hexadecimal color code if found, otherwise None.
    """
    return COLORS_LIST.get(color_id, None)

def hex_to_color_id(hex_color: int) -> Union[int, None]:
    """
    Returns the color ID for the given hexadecimal color code. If not found, returns None.

    :param hex_color: The hex of the color.
    :type hex_color: int
    :return: The ID of the color if found, otherwise None.
    """
    for color_id, color_hex in COLORS_LIST.items():
        if color_hex == hex_color:
            return color_id
    return None

@dataclass
class Icon:
    """
    A **dataclass** representing the icon of a specific gamemode and ID.

    Attributes
    ----------
    id : int
        The ID of the icon
    gamemode : Gamemode
        The gamemode of the icon
    primary_color_id : int
        The primary color ID of the icon
    secondary_color_id : int
        The secondary color ID of the icon
    glow_color_id : Union[int, None]
        The glow color ID of the icon, if doesn't exist then None.
    """
    id: int
    gamemode: Gamemode
    primary_color_id: int
    secondary_color_id: int
    glow_color_id: Union[int, None]

    @property
    def primary_color_hex(self) -> int:
        """
        Returns the primary color ID as a hexadecimal color code.
        """
        return color_id_to_hex(self.primary_color_id)
    
    @property
    def secondary_color_hex(self) -> int:
        """
        Returns the secondary color ID as a hexadecimal color code.
        """
        return color_id_to_hex(self.secondary_color_id)
    
    @property
    def glow_color_hex(self) -> int | None:
        """
        Returns the glow color ID as a hexadecimal color code if it exists, otherwise raise a `ValueError`.
        """
        if self.glow_color_id is None:
            raise ValueError("This icon has no glow color.")
        
        return color_id_to_hex(self.glow_color_id)