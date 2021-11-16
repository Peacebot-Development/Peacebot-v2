from enum import Enum


class EmbedColors(int, Enum):
    SUCCESS = 0x00FF00
    ERROR = 0xFF0000
    GENERIC = 0xFFD700
    ALERT = 0xFFA500
    INFO = 0x99CCFF
