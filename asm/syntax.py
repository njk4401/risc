###############################################################################
# File: syntax.py
# Description: Contains njkRISC ISA information and njkASM syntax definitions.
# Written: 8 October 2025
###############################################################################

"""Defines njkASM syntax rules, ISA, and Statement dataclasses."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .typedefs import Pathlike

#==============================================================================
# ISA Constant Definitions
#==============================================================================
OP_FIELD = 6   # Size of OpCode field in bits
REG_FIELD = 5  # Size of Register field in bits
IW_FIELD = 16  # Size of Instruction Word in bits

RF_SIZE = 32      # Number of registers in Register File
MEM_SIZE = 2**16  # Number of locations in memory

#==============================================================================
# Operand Types
#==============================================================================
class Operand(Enum):
    NONE = 0       # Accepts no operands
    REG = 1        # Accepts one register as operand
    CONST = 2      # Acecpts one constant as operand
    MEM = 3        # Accepts one memory location as operand
    REG_REG = 4    # Accepts two registers as operands
    REG_CONST = 5  # Accepts a register and a constant as operands
    REG_MEM = 6    # Accepts a register and a memory location as operands
    SYM_EXPR = 7   # Accepts a symbol and an expression as operands
    SYM_NUM = 8    # Accepts a symbol and number as operands

    @property
    def count(self) -> int:
        """Return the number of expected operands for this operand type."""
        if self in {Operand.NONE}:
            return 0
        if self in {Operand.REG, Operand.CONST, Operand.MEM}:
            return 1
        if self in {
            Operand.REG_REG, Operand.REG_CONST, Operand.REG_MEM,
            Operand.SYM_EXPR, Operand.SYM_NUM
        }:
            return 2

        raise ValueError(
            f"Unknown: {self.name}"
        )

    @property
    def takes_addr(self) -> bool:
        return self in {Operand.MEM, Operand.REG_MEM}


OPERAND_TYPES = {
    "ld": Operand.REG_MEM,
    "st": Operand.REG_MEM,
    "cpy": Operand.REG_REG,
    "swap": Operand.REG_REG,
    "jmp": Operand.MEM,
    "call": Operand.MEM,
    "ret": Operand.NONE,
    "not": Operand.REG,
    "and": Operand.REG_REG,
    "or": Operand.REG_REG,
    "xor": Operand.REG_REG,
    "shra": Operand.REG_CONST,
    "shrl": Operand.REG_CONST,
    "rotr": Operand.REG_CONST,
    "rotl": Operand.REG_CONST,
    "rrc": Operand.REG_CONST,
    "rlc": Operand.REG_CONST,
    "rrn": Operand.REG_CONST,
    "rln": Operand.REG_CONST,
    "rrv": Operand.REG_CONST,
    "rlv": Operand.REG_CONST,
    "rrz": Operand.REG_CONST,
    "rlz": Operand.REG_CONST,
    "add": Operand.REG_REG,
    "sub": Operand.REG_REG,
    "mul": Operand.REG_REG,
    "div": Operand.REG_REG,
    "addc": Operand.REG_CONST,
    "subc": Operand.REG_CONST,
    "addv": Operand.REG_REG,
    "subv": Operand.REG_REG,
    "cmp": Operand.REG_REG,
    "cmpc": Operand.REG_CONST,
    "push": Operand.REG,
    "pop": Operand.REG,
    "ldsp": Operand.MEM,
    "nop": Operand.NONE
}

def load_opcodes(header_path: Pathlike) -> dict[str, OpCode]:
    """Read opcode definitions from a Verilog header."""
    content = Path(header_path).read_text()

    OPCODE_PATTERN = re.compile(r"`define\s+OP_([A-Z0-9_]+)\s+6'b([01]{6})")

    opcodes = {}
    for match in OPCODE_PATTERN.finditer(content):
        mnemonic = match.group(1).lower()
        bits = match.group(2)

        if mnemonic not in OPERAND_TYPES:
            raise ValueError(f"Missing operand definition for '{mnemonic}'")

        opcodes[mnemonic] = OpCode(
            mnemonic, bits, OPERAND_TYPES[mnemonic]
        )

    return opcodes

#==============================================================================
# Statement Dataclasses
#==============================================================================
@dataclass(frozen=True)
class OpCode:
    """Represents a single instruction definition."""
    mnemonic: str  # Assembly language instruction
    bits: str      # Machine code representation
    ops: Operand   # Value of Operand Enum

@dataclass
class Statement:
    """Base statement, holding line number and raw line information."""
    line: int  # Original line number
    raw: str   # Original line text

@dataclass
class Section(Statement):
    """Section statements. (Ex. .directives, .code, etc.)"""
    name: str        # Section name
    args: list[str]  # Section arguments

@dataclass
class Directive(Statement):
    """Directive statements. (Ex. .equ)"""
    kw: str          # Directive keyword
    args: list[str]  # Directive arguments
    ops: Operand = Operand.SYM_EXPR

@dataclass
class Constant(Statement):
    """Constant statements. (Ex. .word)"""
    kw: str          # Constant keyword
    args: list[str]  # Constant arguments
    ops: Operand = Operand.SYM_EXPR

@dataclass
class Data(Statement):
    """Data statements."""
    kw: str          # Data keyword
    args: list[str]  # Data arguments
    ops: Operand = Operand.SYM_NUM

@dataclass
class Instruction(Statement):
    """Instruction statements. (Ex. ADD, CPY, LD, etc)"""
    opcode: OpCode  # Instruction definition
    ops: list[str]  # Instruction operands

@dataclass
class Jump(Instruction):
    """Jump Statements."""
    condition_bits: str

@dataclass
class Label(Statement):
    """Label statements. (Ex. @label)"""
    name: str           # Label name
    child: Instruction  # Label instruction

#==============================================================================
# njkASM Syntax
#==============================================================================
class Syntax:
    """Static container for njkASM syntax rules."""
    #--------------------------------------------------------------------------
    # Misc. Character Denotations
    #--------------------------------------------------------------------------
    # Capturing Group 1: Label Name
    LABEL = re.compile(r'(?i)^([a-z_]\w*):')  # Labels succeeded by ":"

    COMMENT = re.compile(r';.*$')   # Comments denoted by ";" until end of line
    OP_DELIM = ','  # Character used to delimit statement args/ops

    #--------------------------------------------------------------------------
    # Memory Addressing Modes
    #--------------------------------------------------------------------------
    # Capturing Group 1: Address or Data Symbol
    # Immediate addressing denoted by #addr
    AM_IMMEDIATE = re.compile(r'(?i)#(0x[a-f\d]+|0b[10]+|\d+|[a-z_][\w]*)$')
    # PC-Relative addressing denoted by &addr
    AM_PC_REL = re.compile(r'(?i)&(0x[a-f\d]+|0b[10]+|\d+|[a-z_][\w]*)$')
    # SP-Relative addressing denoted by $addr
    AM_SP_REL = re.compile(r'(?i)\$(0x[a-f\d]+|0b[10]+|\d+|[a-z_][\w]*)$')

    # Capturing Group 1: Address or Data Symbol
    # Capturing Group 2: Register
    # Indexed addressing denoted by addr[register]
    AM_INDEX = re.compile(r'(?i)(0x[a-f\d]+|0b[10]+|\d+|[a-z_][\w]*)\[(.+)\]$')

    #--------------------------------------------------------------------------
    # Section Syntax
    #--------------------------------------------------------------------------
    DIRECTIVES = '.directives'  # Keyword for entering directives section
    CONSTANTS = '.constants'    # Keyword for entering constants section
    DATA = '.data'  # Keyword for entering data section
    CODE = '.code'  # Keyword for entering code section
    SECTION_END = '.end'  # Keyword for ending a section
    SECTION_STARTS = (DIRECTIVES, CONSTANTS, DATA, CODE)

    #--------------------------------------------------------------------------
    # Assembly Directive Keywords
    #--------------------------------------------------------------------------
    SYMBOL_DEF = '.equ'  # Symbol definitions
    DIRECTIVE_KW = (SYMBOL_DEF,)

    #--------------------------------------------------------------------------
    # Constant Keywords
    #--------------------------------------------------------------------------
    CONST_WORD = '.word'    # Word declarations
    CONST_ARRAY = '.array'  # Array declarations
    CONSTANT_KW = (CONST_WORD, CONST_ARRAY)

    #--------------------------------------------------------------------------
    # Data Keywords
    #--------------------------------------------------------------------------
    DATA_ALLOCATE = '.alloc'  # Allocate spot(s) in RAM
    DATA_KW = (DATA_ALLOCATE,)

    #--------------------------------------------------------------------------
    # OpCode Definitions
    #--------------------------------------------------------------------------
    # Key: ASM Mnemonic
    # Value: OpCode Dataclass holding the ASM mnemonic and binary translation
    OPCODES = load_opcodes("../include/opcodes.vh")

    # Jump Conditions
    JMP_VALID = ('jmp', 'jc', 'jn', 'jv', 'jz', 'jnc', 'jnn', 'jnv', 'jnz')
    JMP_BITS = tuple(format(i, f'0{4}b')+'0' for i in range(len(JMP_VALID)))
    JMP_TRANSLATE = dict(zip(JMP_VALID, JMP_BITS))
    JMP_ALIAS = dict(jeq='jz', jne='jnz', jl='jn', jge='jnn')
    for alias, original in JMP_ALIAS.items():
        JMP_TRANSLATE[alias] = JMP_TRANSLATE[original]

    #--------------------------------------------------------------------------
    # Register Field Mnemonic
    #--------------------------------------------------------------------------
    REG_VALID = tuple(f'r{i}' for i in range(RF_SIZE))
    REG_BITS = tuple(format(i, f'0{REG_FIELD}b') for i in range(RF_SIZE))
    REG_TRANSLATE = dict(zip(REG_VALID, REG_BITS))

    #--------------------------------------------------------------------------
    # Symbol Names
    #--------------------------------------------------------------------------
    SYMBOL = re.compile(r'(?i)^[a-z_][\w]*')
    INVALID_SYMBOLS = set(
        SECTION_STARTS + (SECTION_END,) + DIRECTIVE_KW + CONSTANT_KW +
        tuple(OPCODES.keys()) + tuple(JMP_TRANSLATE.keys()) + REG_VALID
    )
    INVALID_SYMVAL = set(
        SECTION_STARTS + (SECTION_END,) + DIRECTIVE_KW + CONSTANT_KW +
        tuple(OPCODES.keys()) + tuple(JMP_TRANSLATE.keys())
    )
