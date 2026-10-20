"""Shared palette. Every sprite draws only with these colours so the game reads as one set."""


def _hex(value: str) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


CLEAR = (0, 0, 0, 0)

OUTLINE = _hex("1b1420")
BLACK = _hex("0e0b14")
WHITE = _hex("f4f4f0")
GREY_L = _hex("c2c7cf")
GREY = _hex("8a8f9c")
GREY_D = _hex("555a69")
SLATE = _hex("343848")

SKIN = _hex("eab890")
SKIN_D = _hex("c48a66")
PALE = _hex("dcd8e8")
PALE_D = _hex("a9a4c2")

HAIR_RED = _hex("c8502a")
HAIR_RED_D = _hex("8e3320")

GREEN_L = _hex("7fc45a")
GREEN = _hex("4a9a48")
GREEN_D = _hex("2c6a3c")
FOREST = _hex("1d4a34")

BROWN_L = _hex("b0835a")
BROWN = _hex("80583a")
BROWN_D = _hex("553626")

SAND = _hex("d9c08a")
GOLD = _hex("f2c744")
GOLD_D = _hex("c08a22")

RED = _hex("d43d3d")
RED_D = _hex("8f2238")
ORANGE = _hex("f28a2e")
YELLOW = _hex("ffe36b")

BLUE_L = _hex("bfe6f5")
BLUE = _hex("6fb6e0")
BLUE_D = _hex("3a6fa8")
NAVY = _hex("22335c")

PURPLE_L = _hex("c79bf0")
PURPLE = _hex("8452c4")
PURPLE_D = _hex("4b2c78")

# The kitten: an orange tabby with cream paws and chest.
GINGER_L = _hex("ffbe6a")
GINGER = _hex("f28a2e")
GINGER_D = _hex("c75a1e")
GINGER_DD = _hex("8a3616")
CREAM = _hex("fff1d6")
CREAM_D = _hex("e9c9a2")
PINK = _hex("f7a3b6")
PINK_D = _hex("c8607e")
# The hero's white muzzle, chest and paw tips (shaded grey-pink), and its red cape.
FUR_WHITE = _hex("fbf7f2")
FUR_WHITE_D = _hex("d9c9c6")
CAPE_L = _hex("ec5a4e")
CAPE = _hex("c8303a")
CAPE_D = _hex("7e1c30")
YARN = _hex("f0609a")
YARN_L = _hex("ff9cc6")
YARN_D = _hex("a8306a")

# Forest
RUST_L = _hex("e0884a")
RUST = _hex("b4542a")
RUST_D = _hex("74311a")
LEAF_L = _hex("b4e46a")
TEAL = _hex("3fa9b8")
MOSS = _hex("2f7d46")

# Frost
ICE_L = _hex("eafaff")
CYAN = _hex("8fe3f2")
ICE_D = _hex("2c5492")

# Haunted
LILAC = _hex("ece4ff")
LILAC_D = _hex("b5a8e6")
VIOLET = _hex("a96cf0")
INDIGO = _hex("2e2160")
NIGHT = _hex("1a1236")
SPIRIT = _hex("8ef0d0")

# Citadel
LAVA_L = _hex("ffd04a")
LAVA = _hex("ff6a1a")
MAROON = _hex("4a1624")
IRON_L = _hex("8d8796")
IRON = _hex("5a5462")
IRON_D = _hex("34303c")
