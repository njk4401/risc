def to_int(value: int | str) -> int:
    """Convert value to an integer from decimal, binary (0b...),
    octal (0o...), or hexadecimal (0x...) representation.
    """
    base = 10
    try:
        val_str = str(value).lower()
        if val_str.startswith("0b"):
            base = 2
        elif val_str.startswith("0o"):
            base = 8
        elif val_str.startswith("0x"):
            base = 16
    except AttributeError:
        pass

    return int(val_str, base)


def to_bin(value: int | str, size: int = 8) -> str:
    """Convert value to binary string representation
    with `size` number of bits.
    """
    value = to_int(value)

    if value < 0:
        value = (1 << size) + value

    binary = bin(value)[2:].rjust(size, "0")
    if len(binary) > size:
        raise ValueError(f"{value} exceeds {size} bits")

    return f"0b{binary}"


def to_oct(value: int | str, size: int = 3) -> str:
    """Convert value to octal string representation
    with `size` number of bits.
    """
    value = to_int(value)

    if value < 0:
        value = (1 << (size*3)) + value

    octal = oct(value)[2:].rjust(size, "0")
    if len(octal) > size:
        raise ValueError(f"{value} exceeds {size} bits")

    return f"0o{octal}"


def to_hex(value: int | str, size: int = 4) -> str:
    """Convert value to hexadecimal string representation
    with `size` number of bits.
    """
    value = to_int(value)

    if value < 0:
        value = (1 << (size*4)) + value

    hexadec = hex(value)[2:].rjust(size, "0").upper()
    if len(hexadec) > size:
        raise ValueError(f"{value} exceeds {size} bits")

    return f"0x{hexadec}"
