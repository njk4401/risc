"""Implements njkASM parsing, validation, and assembly."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from logging import Logger, getLogger

from .exceptions import AssemblerError
from .typedefs import Pathlike
from .util import to_bin, to_hex, to_int
# Explicitly import all used pieces of the syntax module
from .syntax import (
    Syntax, OP_FIELD, REG_FIELD, IW_FIELD, MEM_SIZE, RF_SIZE,
    Statement, Section, Directive, Constant, Data,
    Instruction, Jump, Label, Operand
)

#==============================================================================
# Per-File Scope Tables
#==============================================================================
@dataclass
class Scope:
    file: str
    symbols: dict[str, str] = field(default_factory=dict)
    constants: dict[str, str] = field(default_factory=dict)
    data: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)

#==============================================================================
# Main Assembler Class
#==============================================================================
class Assembler:
    def __init__(
        self,
        *,
        rf_size: int = None,
        mem_size: int = None,
        logger: Logger = None
    ) -> None:
        """Create new Assembler instance."""
        self.rf_size = rf_size or RF_SIZE
        self.mem_size = mem_size or MEM_SIZE
        self.log = logger or getLogger()

        self.sections: dict[str, dict[str, list[Statement]]] = {}
        self.program: dict[str, tuple[str, str]] = {}

        self.parsed: dict[str, list[Statement]] = {}
        self.program_memory: dict[str, dict[str, tuple[str, str]]] = {}
        self.data_memory: dict[str, dict[str, tuple[str, str]]] = {}

    #==========================================================================
    # Loading and Parsing File
    #==========================================================================
    def load_file(self, file: Pathlike) -> None:
        """Load a new file into the assembler."""
        file = Path(file)

        # Attempt to open and read the file
        try:
            text = file.read_text()
        except Exception:
            raise AssemblerError(
                f"Unable to open {file} for reading",
                file.name
            ) from None

        statements = self._load_statements(text)
        self.log.info(f"Loaded file {file.name!r}")

        # Parse raw text into statements
        parsed, summary = self._parse_statements(statements, file.name)

        self.parsed[file.name] = parsed
        self.log.debug(
            f"[{file.name}] Parsing Summary:\n"
            "\n".join(f"  {item}: {count}" for item, count in summary.items())
        )

    @staticmethod
    def _load_statements(file_content: str) -> list[tuple[int, str]]:
        """Load statements from raw contents of a file."""
        statements: list[tuple[int, str]] = []
        label_buffer: tuple[int, str] | None = None

        for linenum, line in enumerate(file_content.splitlines(), start=1):
            # Replace all whitespace with a single space character
            line = re.sub(r"\s+", " ", line)

            # Filter out comments
            statement = Syntax.COMMENT.sub("", line).strip()

            # Skip if line is empty
            if not statement:
                continue

            # If previous line was only a label, append this one to it
            if label_buffer is not None:
                # Combine into single statement string
                combined = f"{label_buffer[1]} {statement}"
                statements.append((label_buffer[0], combined))
                label_buffer = None
                continue

            # Check if this line is a bare label (e.g. "loop:")
            if Syntax.LABEL.fullmatch(statement):
                # Store for next line
                label_buffer = (linenum, statement)
                continue

            statements.append((linenum, statement))

        # Add any remaining label (even if no corresponding statement)
        if label_buffer:
            statements.append((linenum, statement))

        return statements

    @staticmethod
    def _parse_statements(
        statements: list[tuple[int, str]],
        file_name: str
    ) -> tuple[list[Statement], dict[str, int]]:
        """Parse raw text statements within and
        load the parsed attribute with a tuple of Statement instances.
        """
        parsed: list[Statement] = []
        counts: dict[str, int] = {}

        for linenum, raw in statements:
            # Split the raw statement on whitespace
            words = raw.split()
            raw_head = words[0]
            head = words[0].lower()

            # Split arguments/operands on the delimiter
            args = []
            if argstr := "".join(words[1:]):
                args = argstr.split(Syntax.OP_DELIM)

            #------------------------------------------------------------------
            # Section Declarations
            #------------------------------------------------------------------
            if head in Syntax.SECTION_STARTS or head == Syntax.SECTION_END:
                parsed.append(
                    Section(line=linenum, raw=raw, name=head, args=args)
                )
                continue
            #------------------------------------------------------------------
            # Directives
            #------------------------------------------------------------------
            elif head in Syntax.DIRECTIVE_KW:
                parsed.append(
                    Directive(line=linenum, raw=raw, kw=head, args=args)
                )
            #------------------------------------------------------------------
            # Constants
            #------------------------------------------------------------------
            elif head in Syntax.CONSTANT_KW:
                parsed.append(
                    Constant(line=linenum, raw=raw, kw=head, args=args)
                )
            #------------------------------------------------------------------
            # Data
            #------------------------------------------------------------------
            elif head in Syntax.DATA_KW:
                parsed.append(
                    Data(line=linenum, raw=raw, kw=head, args=args)
                )
            #------------------------------------------------------------------
            # Instructions
            #------------------------------------------------------------------
            elif head in Syntax.JMP_TRANSLATE:
                opcode = Syntax.OPCODES[Syntax.JMP_VALID[0]]
                parsed.append(
                    Jump(
                        line=linenum, raw=raw, opcode=opcode, ops=args,
                        condition_bits=Syntax.JMP_TRANSLATE[head]
                    )
                )
            elif head in Syntax.OPCODES:
                opcode = Syntax.OPCODES[head]
                parsed.append(
                    Instruction(line=linenum, raw=raw, opcode=opcode, ops=args)
                )
            #------------------------------------------------------------------
            # Labels with an Instruction child
            #------------------------------------------------------------------
            elif matched := Syntax.LABEL.match(raw_head):
                label = matched.group(1)

                if len(words) == 1:
                    raise AssemblerError(
                        f"Label {label!r} missing statement",
                        file_name, linenum, raw
                    )

                # Point head to Instruction
                head = words[1].lower()
                # Change args to be after the Instruction
                if argstr := "".join(words[2:]):
                    args = argstr.split(Syntax.OP_DELIM)

                if head in Syntax.JMP_TRANSLATE:
                    opcode = Syntax.OPCODES[Syntax.JMP_VALID[0]]
                    parsed.append(
                        Label(
                            line=linenum, raw=raw, name=label,
                            child=Jump(
                                line=linenum, raw=raw, opcode=opcode, ops=args,
                                condition_bits=Syntax.JMP_TRANSLATE[head]
                            )
                        )
                    )
                elif head in Syntax.OPCODES:
                    opcode = Syntax.OPCODES[head]
                    parsed.append(
                        Label(
                            line=linenum, raw=raw, name=label,
                            child=Instruction(
                                line=linenum, raw=raw, opcode=opcode, ops=args
                            )
                        )
                    )
                else:
                    raise AssemblerError(
                        f"Unknown instruction {head!r}",
                        file_name, linenum, raw
                    )

            #------------------------------------------------------------------
            # Catch anything missed
            #------------------------------------------------------------------
            else:
                raise AssemblerError(
                    f"Unknown statement {head!r}",
                    file_name, linenum, raw
                )

            stmt_type = type(parsed[-1]).__name__
            counts[stmt_type] = counts.get(stmt_type, 0) + 1

        return parsed, counts

    #==========================================================================
    # Syntax and Validation
    #==========================================================================
    def pre_check(self) -> None:
        """Perform syntax validation, symbol uniqueness,
        and load the sections attribute with a dictionary of Statements
        keyed by the section start directive.
        """
        self.log.info("Beginning ASM file pre-check")
        cur_sect = None

        # Hold symbol/label name and line number it first occurs on
        symbols: dict[str, int] = {}
        labels: dict[str, int] = {}

        for file_name, statements in self.parsed.items():
            for stmt in statements:
                #--------------------------------------------------------------
                # Sections
                #--------------------------------------------------------------
                if isinstance(stmt, Section):
                    if stmt.args:
                        raise AssemblerError(
                            f"{stmt.name} does not accept any arguments",
                            file_name, stmt.line, stmt.raw
                        )
                    if stmt.name == Syntax.SECTION_END:
                        # Check if called outside of section
                        if cur_sect is None:
                            raise AssemblerError(
                                f"{Syntax.SECTION_END} called "
                                "outside of section",
                                file_name, stmt.line, stmt.raw
                            )
                        self.log.debug(
                            f"[{file_name}] Ended {cur_sect} section "
                            f"on line {stmt.line}"
                        )
                        cur_sect = None
                    else:
                        # Check if called within another section
                        if cur_sect is not None:
                            raise AssemblerError(
                                f"Cannot enter {stmt.name} "
                                f"section in {cur_sect}",
                                file_name, stmt.line, stmt.raw
                            )
                        cur_sect = stmt.name
                        self.log.debug(
                            f"[{file_name}] Enter {cur_sect} section "
                            f"on line {stmt.line}"
                        )
                #--------------------------------------------------------------
                # Directives
                #--------------------------------------------------------------
                elif isinstance(stmt, Directive):
                    # Check if called outside of directives section
                    if cur_sect != Syntax.DIRECTIVES:
                        raise AssemblerError(
                            f"Directives must declared within "
                            f"{Syntax.DIRECTIVES} section",
                            file_name, stmt.line, stmt.raw
                        )

                    if len(stmt.args) != stmt.ops.count:
                        raise AssemblerError(
                            f"{stmt.kw} requires {stmt.ops.count} arguments",
                            file_name, stmt.line, stmt.raw
                        )

                    symbol_name = stmt.args[0]
                    if not Syntax.SYMBOL.match(symbol_name):
                        raise AssemblerError(
                            f"Invalid symbol {symbol_name!r}\n"
                            "Symbols cannot begin with digits and must contain"
                            " purely alphanumeric characters or underscores",
                            file_name, stmt.line, stmt.raw
                        )
                    if symbol_name.lower() in Syntax.INVALID_SYMBOLS:
                        raise AssemblerError(
                            f"Cannot create symbol with name {symbol_name!r}",
                            file_name, stmt.line, stmt.raw
                        )
                    if symbol_name in symbols:
                        raise AssemblerError(
                            f"{symbol_name!r} previously assigned on "
                            f"line {symbols[symbol_name]}",
                            file_name, stmt.line, stmt.raw
                        )

                    symbols[symbol_name] = stmt.line
                    self.log.debug(
                        f"[{file_name}] Symbol {symbol_name!r} "
                        f"detected on line {stmt.line}"
                    )
                #--------------------------------------------------------------
                # Constants
                #--------------------------------------------------------------
                elif isinstance(stmt, Constant):
                    # Check if called outside of constants section
                    if cur_sect != Syntax.CONSTANTS:
                        raise AssemblerError(
                            f"Constants must be in {Syntax.CONSTANTS} section",
                            file_name, stmt.line, stmt.raw
                        )

                    if len(stmt.args) != stmt.ops.count:
                        raise AssemblerError(
                            f"{stmt.kw} requires {stmt.ops.count} arguments",
                            file_name, stmt.line, stmt.raw
                        )

                    symbol_name = stmt.args[0]
                    if (not Syntax.SYMBOL.match(symbol_name) or
                        symbol_name.lower() in Syntax.INVALID_SYMBOLS):
                        raise AssemblerError(
                            f"Invalid symbol {symbol_name!r}",
                            file_name, stmt.line, stmt.raw
                        )

                    # Check unique
                    if symbol_name in symbols:
                        raise AssemblerError(
                            f"{symbol_name!r} previously assigned on "
                            f"line {symbols[symbol_name]}",
                            file_name, stmt.line, stmt.raw
                        )

                    symbols[symbol_name] = stmt.line
                    self.log.debug(
                        f"[{file_name}] Constant {symbol_name!r} "
                        f"detected on line {stmt.line}"
                    )
                #--------------------------------------------------------------
                # Data
                #--------------------------------------------------------------
                elif isinstance(stmt, Data):
                    # Check if called outside of data section
                    if cur_sect != Syntax.DATA:
                        raise AssemblerError(
                            f"Data must be in {Syntax.DATA} section",
                            file_name, stmt.line, stmt.raw
                        )

                    if len(stmt.args) != stmt.ops.count:
                        raise AssemblerError(
                            f"{stmt.kw} requires {stmt.ops.count} arguments",
                            file_name, stmt.line, stmt.raw
                        )

                    symbol_name = stmt.args[0]
                    if (not Syntax.SYMBOL.match(symbol_name) or
                        symbol_name.lower() in Syntax.INVALID_SYMBOLS):
                        raise AssemblerError(
                            f"Invalid symbol {symbol_name!r}",
                            file_name, stmt.line, stmt.raw
                        )

                    # Check unique
                    if symbol_name in symbols:
                        raise AssemblerError(
                            f"{symbol_name!r} previously assigned on "
                            f"line {symbols[symbol_name]}",
                            file_name, stmt.line, stmt.raw
                        )

                    symbols[symbol_name] = stmt.line
                    self.log.debug(
                        f"[{file_name}] Data {symbol_name!r} "
                        f"detected on line {stmt.line}"
                    )
                #--------------------------------------------------------------
                # Instructions
                #--------------------------------------------------------------
                elif isinstance(stmt, Instruction):
                    # Check if called outside of code section
                    if cur_sect != Syntax.CODE:
                        raise AssemblerError(
                            "Instructions only allowed in "
                            f"{Syntax.CODE} section",
                            file_name, stmt.line, stmt.raw
                        )

                    num_ops = stmt.opcode.ops.count
                    if len(stmt.ops) != num_ops:
                        raise AssemblerError(
                            f"{stmt.opcode.mnemonic} requires "
                            f"{num_ops} operands",
                            file_name, stmt.line, stmt.raw
                        )
                #--------------------------------------------------------------
                # Labels
                #--------------------------------------------------------------
                elif isinstance(stmt, Label):
                    # Check if called outside of code section
                    if cur_sect != Syntax.CODE:
                        raise AssemblerError(
                            f"Labels only allowed in {Syntax.CODE} section",
                            file_name, stmt.line, stmt.raw
                        )

                    # Check unique
                    label = stmt.name
                    if label in labels:
                        raise AssemblerError(
                            f"{label!r} has been previously assigned "
                            f"on line {labels[label]}",
                            file_name, stmt.line, stmt.raw
                        )

                    # Save name
                    labels[label] = stmt.line
                    self.log.debug(
                        f"[{file_name}] Label {label!r} "
                        f"detected on line {stmt.line}"
                    )

                    op = stmt.child.opcode
                    num_ops = op.ops.count
                    if len(stmt.child.ops) != num_ops:
                        raise AssemblerError(
                            f"{op.mnemonic} requires {num_ops} operands",
                            file_name, stmt.line, stmt.raw
                        )

                #--------------------------------------------------------------
                # Save statement under current section
                #--------------------------------------------------------------
                if file_name not in self.sections:
                    self.sections[file_name] = {}
                if cur_sect and cur_sect not in self.sections[file_name]:
                    self.sections[file_name][cur_sect] = []
                if cur_sect and not isinstance(stmt, Section):
                    self.sections[file_name][cur_sect].append(stmt)

        # Check if no final .end
        if cur_sect is not None:
            raise AssemblerError(
                f"{cur_sect} section never closed before reaching end of file",
            )

        self.log.info("Pre-check finished")

    #==========================================================================
    # Evaluate statements / Translate to machine code
    #==========================================================================
    def eval_sections(self) -> None:
        """Evaluate all sections and translate into machine code.

        Loads the program attribute with a dictionary of Statements and their
        corresponding raw source text strings, keyed by a hexadecimal address.
        """
        for i, (file_name, sections) in enumerate(self.sections.items()):
            # Symbol name with its value
            symbols = {}
            # Constant name with its hex value
            constants = {}
            # Data name with its hex memory location in RAM
            data = {}
            # Code address with its binary machine code and raw statement
            code: dict[str, tuple[str, str]] = {}
            # Label name with its hex memory location in ROM
            labels = {}
            # Mapping of hex RAM address to binary value and raw statement
            ram = {}
            #----------------------------------------------------------------------
            # Evaluate Assembler Directives First
            #----------------------------------------------------------------------
            self.log.info(f"[{file_name}] Evaluating Directives")
            for stmt in sections.get(Syntax.DIRECTIVES, []):
                # .equ
                if stmt.kw == Syntax.SYMBOL_DEF:
                    # Assign symbol to value, preserve raw statement
                    name, val = stmt.args

                    if val.lower() in Syntax.INVALID_SYMVAL:
                        raise AssemblerError(
                            f'Invalid symbol value "{val}"', file_name, stmt.line, stmt.raw
                        )

                    symbols[name] = val
                    self.log.debug(f'[{file_name}] Symbol "{name}" assigned to "{val}"')

            self.log.info(f"[{file_name}] Finished Evaluating Directives")
            #----------------------------------------------------------------------
            # Evaluate Constants Section
            #----------------------------------------------------------------------
            dm_address = 4096*i
            self.log.info(f"[{file_name}] Evaluating Constants")
            for stmt in sections.get(Syntax.CONSTANTS, []):
                name, val = stmt.args

                # Replace with .equ equivalent if available
                if name in symbols:
                    name = symbols[name]
                if val in symbols:
                    val = symbols[val]

                # Check value can fit in word
                try:
                    if to_int(val) >= 2**IW_FIELD:
                        raise AssemblerError(
                            f'Value "{val}" too large, '
                            f'max: {to_hex(2**IW_FIELD-1)}',
                            file_name, stmt.line, stmt.raw
                        )
                # If not raise error if not numeric for now
                except ValueError:
                    raise AssemblerError(
                        f'Unable to evaluate "{const}" to a value',
                        file_name, stmt.line, stmt.raw
                    ) from None

                constants[name] = to_hex(dm_address)
                ram[to_hex(dm_address)] = (to_bin(val, size=IW_FIELD)[2:], stmt.raw)
                self.log.debug(
                    f'[{file_name}] Constant "{name}" assigned to {to_hex(val)} '
                    f"at location {to_hex(dm_address)}"
                )

                dm_address += 1

            self.log.info(f"[{file_name}] Finished Evaluating Constants")
            #----------------------------------------------------------------------
            # Evaluate Data Section
            #----------------------------------------------------------------------
            self.log.info(f"[{file_name}] Evaluating Data")
            for stmt in sections.get(Syntax.DATA, []):
                name, num = stmt.args

                # Replace with .equ equivalent if available
                if name in symbols:
                    name = symbols[name]
                if num in symbols:
                    num = symbols[num]

                try:
                    num = to_int(num)
                except ValueError:
                    raise AssemblerError(
                        f'Unable to evaluate "{num}" to a value',
                        file_name, stmt.line, stmt.raw
                    ) from None

                if dm_address + num >= self.mem_size-0xFF:
                    raise AssemblerError(
                        f'Allocated data exceeds the max RAM size: '
                        f'{to_hex(self.mem_size-0xFF-1)}'
                    )


                data[name] = to_hex(dm_address)
                self.log.debug(
                    f'[{file_name}] Data "{name}" has been allocated {num} location'
                    f"{"s" if num > 1 else ""} starting at {to_hex(dm_address)}"
                )

                dm_address += num

            self.log.info(f"[{file_name}] Finished Evaluating Data")
            #----------------------------------------------------------------------
            # Evaluate Code Section
            #----------------------------------------------------------------------
            self.log.info(f"[{file_name}] Evaluating Code")
            pm_address = 4096*i
            # First pass - Gather all label addresses
            for stmt in sections.get(Syntax.CODE, []):
                # Assign label to address
                if isinstance(stmt, Label):
                    labels[stmt.name] = to_hex(pm_address)
                    self.log.debug(f"[{file_name}] "
                        f'Label "{stmt.name}" assigned to '
                        f"address {to_hex(pm_address)}"
                    )

                    if stmt.child.opcode.ops in {Operand.MEM, Operand.REG_MEM}:
                        pm_address = pm_address + 1

                if isinstance(stmt, Instruction):
                    if stmt.opcode.ops in {Operand.MEM, Operand.REG_MEM}:
                        pm_address = pm_address + 1

                pm_address = pm_address + 1

            # Second pass - Generate machine code
            pm_address = 4096*i
            for stmt in sections.get(Syntax.CODE, []):
                if isinstance(stmt, Label):
                    stmt = stmt.child

                op_info = stmt.opcode
                iw1 = None

                #--------------------------------------------------------------
                # Instructions which take 0 operands
                #--------------------------------------------------------------
                if op_info.ops == Operand.NONE:
                    ri_field = to_bin(0, size=REG_FIELD)[2:]
                    rj_field = to_bin(0, size=REG_FIELD)[2:]
                #--------------------------------------------------------------
                # Instructions which take only 1 register operand
                #--------------------------------------------------------------
                elif op_info.ops == Operand.REG:
                    reg = stmt.ops[0]

                    # Replace with .equ equivalent if available
                    if reg in symbols:
                        reg = symbols[reg]

                    if reg.lower() not in Syntax.REG_VALID:
                        raise AssemblerError(
                            f'Unable to evaluate "{reg}" as a register',
                            file_name, stmt.line, stmt.raw
                        )

                    ri_field = Syntax.REG_TRANSLATE[reg.lower()]
                    rj_field = to_bin(0, size=REG_FIELD)[2:]
                #--------------------------------------------------------------
                # Instructions which take only 1 memory operand (CALL/JMP)
                #--------------------------------------------------------------
                elif op_info.ops == Operand.MEM:
                    am = symbols.get(stmt.ops[0], stmt.ops[0])
                    mem, addr = self._eval_mem(am, stmt, symbols, constants, data, labels, file_name)

                    status = to_bin(0, size=REG_FIELD)[2:]
                    if isinstance(stmt, Jump):
                        status = stmt.condition_bits

                    ri_field = mem
                    rj_field = status

                    iw1 = [
                        addr[0:OP_FIELD],
                        addr[OP_FIELD:OP_FIELD+REG_FIELD],
                        addr[OP_FIELD+REG_FIELD:OP_FIELD+2*REG_FIELD]
                    ]
                #--------------------------------------------------------------
                # Instructions which take 2 register operands
                #--------------------------------------------------------------
                elif op_info.ops == Operand.REG_REG:
                    reg1, reg2 = stmt.ops

                    # Replace with .equ equivalent if available
                    if reg1 in symbols:
                        reg1 = symbols[reg1]
                    if reg2 in symbols:
                        reg2 = symbols[reg2]

                    if reg1.lower() not in Syntax.REG_VALID:
                        raise AssemblerError(
                            f'Unable to evaluate "{reg1}" as a register',
                            file_name, stmt.line, stmt.raw
                        )
                    if reg2.lower() not in Syntax.REG_VALID:
                        raise AssemblerError(
                            f'Unable to evaluate "{reg2}" as a register',
                            file_name, stmt.line, stmt.raw
                        )

                    ri_field = Syntax.REG_TRANSLATE[reg1.lower()]
                    rj_field = Syntax.REG_TRANSLATE[reg2.lower()]
                #--------------------------------------------------------------
                # Instructions which take 1 register and 1 constant as operands
                #--------------------------------------------------------------
                elif op_info.ops == Operand.REG_CONST:
                    reg, const = stmt.ops

                    # Replace with .equ equivalent if available
                    if reg in symbols:
                        reg = symbols[reg]
                    if const in symbols:
                        const = symbols[const]

                    if reg.lower() not in Syntax.REG_VALID:
                        raise AssemblerError(
                            f'Unable to evaluate "{reg}" as a register',
                            file_name, stmt.line, stmt.raw
                        )

                    try:
                        to_int(const)
                    except ValueError:
                        raise AssemblerError(
                            f'Unable to evaluate "{const}" to a value',
                            file_name, stmt.line, stmt.raw
                        ) from None

                    if to_int(const) >= 2**REG_FIELD:
                        raise AssemblerError(
                            f'"{const}" too large, max: {to_hex(2**REG_FIELD-1)}',
                            file_name, stmt.line, stmt.raw
                        )

                    ri_field = Syntax.REG_TRANSLATE[reg.lower()]
                    rj_field = to_bin(const, size=REG_FIELD)[2:]
                #--------------------------------------------------------------
                # Instructions which take 1 register and 1 memory as operands
                #--------------------------------------------------------------
                elif op_info.ops == Operand.REG_MEM:
                    reg, am = stmt.ops

                    # Replace with .equ equivalent if available
                    if reg in symbols:
                        reg = symbols[reg]
                    if am in symbols:
                        am = symbols[am]

                    if reg.lower() not in Syntax.REG_VALID:
                        raise AssemblerError(
                            f'Unable to evaluate "{reg}" as a register',
                            file_name, stmt.line, stmt.raw
                        )

                    mem, addr = self._eval_mem(am, stmt, symbols, constants, data, labels, file_name)

                    ri_field = mem
                    rj_field = Syntax.REG_TRANSLATE[reg.lower()]

                    # Match how IW0 is split
                    iw1 = [
                        addr[0:OP_FIELD],
                        addr[OP_FIELD:OP_FIELD+REG_FIELD],
                        addr[OP_FIELD+REG_FIELD:OP_FIELD+2*REG_FIELD]
                    ]

                else:
                    raise AssemblerError(
                        f'Unhandled operand types for {op_info.mnemonic}',
                        file_name, stmt.line, stmt.raw
                    )

                # Put together the instruction word
                iw0 = [op_info.bits, ri_field, rj_field]

                code[to_hex(pm_address)] = (iw0, stmt.raw)

                pm_address += 1

                if iw1 is not None:
                    code[to_hex(pm_address)] = (iw1, 'MEM ADDRESS')
                    pm_address += 1

            self.log.info(f"[{file_name}] Finished Evaluating Code")

            self.program_memory[file_name] = code
            self.data_memory[file_name] = ram

    def _eval_mem(self, op: str, stmt: Statement,
                  symbols: dict[str, str], const: dict[str, str],
                  data: dict[str, str], label: dict[str, str], file_name: str) -> tuple[str, str]:
        """Evaluate an operand to appropriate register-address combination
        based on the addressing mode it accomodates.

        Parameters:
            op (str):
                Operand to evaluate.
            stmt (Statement):
                Current Statement for error context if needed.
            symbols (dict):
                Dictionary of symbols and respective values
                for the scope of the current file.
            const (dict):
                Dictionary of constant symbols and their locations in RAM
                for the scope of the current file.
            data (dict):
                Dictionary of data symbols and their locations in RAM
                for the scope of the current file.

        Returns:
            Formatted Ri field and base memory address as a tuple of strings.

        Raises:
            AssemblerError:
                1. Invalid register passed under indexed addressing mode.
                2. Unrecognized addressing mode syntax.
                3. Base address to large to fit in instruction word.
                4. Symbol used which is not in current scope.
        """
        # Immediate AM -> Ri = 0
        if matched := Syntax.AM_IMMEDIATE.match(op):
            reg = Syntax.REG_VALID[0]
            addr = matched.group(1)
        # PC Relative AM -> Ri = 1
        elif matched := Syntax.AM_PC_REL.match(op):
            reg = Syntax.REG_VALID[1]
            addr = matched.group(1)
        # SP Relative AM -> Ri = 2
        elif matched := Syntax.AM_SP_REL.match(op):
            reg = Syntax.REG_VALID[2]
            addr = matched.group(1)
        # RF Indexed AM -> Ri = R,
        # This will catch the other AM in the form R0[...], this is intended
        elif matched := Syntax.AM_INDEX.match(op):
            addr = matched.group(1)
            reg = matched.group(2)
        else:
            raise AssemblerError(
                f'Unable to discern Addressing Mode from "{op}"',
                file_name, stmt.line, stmt.raw
            )

        # Replace with .equ equivalent if available
        if addr in symbols:
            addr = symbols[addr]
        if reg in symbols:
            reg = symbols[reg]

        if reg.lower() not in Syntax.REG_VALID:
            raise AssemblerError(
                f'Unable to evaluate "{reg}" as a register',
                file_name, stmt.line, stmt.raw
            )

        try:
            if to_int(addr) >= 2**IW_FIELD:
                raise AssemblerError(
                    f'"{addr}" too large, max: {to_hex(2**IW_FIELD-1)}',
                    file_name, stmt.line, stmt.raw
                )
        except ValueError:
            if addr in label:
                self.log.debug(
                    f'[{file_name}] Label "{addr}" replaced with address {label[addr]}'
                )
                addr = label[addr]
            elif addr in data:
                self.log.debug(
                    f'[{file_name}] Data "{addr}" replaced with address {data[addr]}'
                )
                addr = data[addr]
            elif addr in const:
                self.log.debug(
                    f'[{file_name}] Constant "{addr}" replaced with address {const[addr]}')
                addr = const[addr]
            else:
                raise AssemblerError(
                    f'Unable to evaluate "{addr}" to a value',
                    file_name, stmt.line, stmt.raw
                ) from None

        return (
            Syntax.REG_TRANSLATE[reg.lower()],  # Ri
            to_bin(to_int(addr), size=IW_FIELD)[2:]  # Address
        )

    #==========================================================================
    # Writing Output
    #==========================================================================
    def write_mif(self, file: str) -> None:
        """Write the program attribute to a memory initialization file."""
        path, base = os.path.split(file)
        rest, ext = os.path.splitext(base)
        pm_out = os.path.join(path, f"PM_{rest}{ext}")
        dm_out = os.path.join(path, f"DM_{rest}{ext}")

        if not (self.program_memory or self.data_memory):
            raise AssemblerError(
                'Nothing to write, run eval_sections() first'
            )

        ctime = time.ctime()
        mif_header = (
            f'-- Assembled by njk4401_asm on {ctime}\n\n'
            f'WIDTH = {IW_FIELD};\n'
            f'DEPTH = {self.mem_size};\n\n'
            f'ADDRESS_RADIX = HEX;\n'
            f'DATA_RADIX = BIN;\n\n'
            f'CONTENT BEGIN\n'
        )

        # Check if the largest memory location is greater than the ROM/RAM size
        program_size = {k: len(v) for k, v in self.program_memory.items()}
        for file_name, size in program_size.items():
            if size >= self.mem_size:
                raise AssemblerError(
                    f'Program exceeds the max ROM size {to_hex(self.mem_size-1)}', file_name
                )
        data_size = {k: len(v) for k, v in self.data_memory.items()}
        for file_name, size in data_size.items():
            if size >= self.mem_size-0xFF:
                raise AssemblerError(
                    f'Data exceeds the max RAM size {to_hex(self.mem_size-0xFF-1)}', file_name
                )

        try:
            # Open output file for writing
            with open(pm_out, 'w') as f:
                f.write('-- Program Memory Initialization File\n')
                f.write(mif_header)
                f.write(f'  -- A : <OpCo><R_i><R_j>;\n')
                # Insert program instructions
                for i, (file_name, pm) in enumerate(self.program_memory.items()):
                 f.write(f'  -- Source File: "{file_name}"\n')
                 start_location = to_hex(program_size[file_name]+4096*i)[2:]
                 end_location = to_hex(4096*(i+1)-1)[2:]
                 next_location = to_hex(4096*(i+1))[2:]
                 for addr, (iw, raw) in pm.items():
                    # IW is split into OpCode, Ri, and Rj fields
                    f.write(f'  {to_hex(addr)[2:]} : {iw[0]}{iw[1]}{iw[2]}; % {raw} %\n')
                 # Initialize remaining memory locations to 0
                 f.write(f'  [{start_location}..{end_location}] : 0;\n')
                f.write(f'  [{next_location}..{to_hex(self.mem_size-1)[2:]}] : 0;\n')
                f.write('END;\n')
        except OSError as e:
            raise type(e)(
                f'Unable to write to "{pm_out}"'
            ) from None

        try:
            # Open output file for writing
            with open(dm_out, 'w') as f:
                # MIF header
                f.write('-- Data Memory Initialization File\n')
                f.write(mif_header)
                # f.write(f'  -- A : <{"VALUE":-^{IW_FIELD-2}}>;\n')
                # Insert constants
                for i, (file_name, dm) in enumerate(self.data_memory.items()):
                 f.write(f'  -- Source File: "{file_name}"\n')
                 start_location = to_hex(data_size[file_name]+4096*i)[2:]
                 end_location = to_hex(4096*(i+1)-1)[2:]
                 next_location = to_hex(4096*(i+1))[2:]
                 for addr, (const, raw) in dm.items():
                    f.write(f'  {to_hex(addr)[2:]} : {const}; % {raw} %\n')
                 # Initialize remaining memory locations to 0
                 f.write(f"  [{start_location}..{end_location}] : 0;\n")
                f.write(f'  [{next_location}..{to_hex(self.mem_size-1)[2:]}] : 0;\n')
                f.write('END;\n')
        except OSError as e:
            raise type(e)(
                f'Unable to write to "{dm_out}"'
            ) from None

        self.log.info(
            f'Files "{pm_out}" and "{dm_out}" written successfully'
        )


def is_numeric(value) -> bool:
    """Return True if value is numeric otherwise False."""
    try:
        to_int(value)
    except Exception:
        return False

    return True
