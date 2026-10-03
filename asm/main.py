###############################################################################
# File:.py
# Description: Assemble an ASM file into a MIF file compatible with njkRISC.
# Written: 5 October 2025
###############################################################################

"""This script is only intended to be ran from command line."""

import sys
import logging
from argparse import ArgumentParser, Namespace
from typing import Any, NoReturn

from assembler import Assembler, AssemblerError
from syntax import Syntax


def exit(status: Any, msg: str = None) -> NoReturn:
    """Log msg and exit with status."""
    if msg is not None:
        log.error(msg)

    sys.exit(status)


def parser_error(message: str) -> NoReturn:
    """Override for default argparse error."""
    # Argparse errors are not capitalized
    msg = message[0].upper()+message[1:]
    print(f"{msg}\nPass the -h flag for help")
    exit(1)


def log_setup(verbose: int, quiet: bool, no_log: bool, file: str) -> None:
    global log

    log = logging.getLogger()
    # log_format = logging.Formatter(
        # "[%(filename)s\b\b\b/%(levelname)s] %(message)s"
    # )
    log_format = logging.Formatter("[%(levelname)s] %(message)s")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()

    if not no_log:
        file_handler = logging.FileHandler(file, 'w')
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)
        log.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)
    if verbose >= 2:
        stream_handler.setLevel(logging.DEBUG)
    elif verbose == 1:
        stream_handler.setLevel(logging.INFO)
    elif quiet:
        stream_handler.setLevel(logging.ERROR)
    else:
        stream_handler.setLevel(logging.WARNING)
    log.addHandler(stream_handler)


def parse() -> Namespace:
    """Parse arguments received from command line.

    Returns:
        Namespace object containing parsed arguments.
    """
    parser = ArgumentParser(
        usage="%(prog)s ASM_FILE [options]",
        description=(
            "Assemble ASM instructions into a MIF file specific for njkRISC."
        )
    )
    parser.error = parser_error

    # Required positional arguments
    parser.add_argument("file",
        metavar="ASM_FILE", nargs="+",
        help="path to file to assemble"
    )

    # Optional arguments
    parser.add_argument("-o", "--output",
        dest="out", metavar="FILE",
        help="write output to custom location, "
             "default is the source file basename + _[PD]M.mif"
    )
    parser.add_argument("-m", "--mem-depth",
        dest="mem_size", metavar="NUM_WORDS", type=int,
        help="maximum on-chip memory depth, default = 0x7FFF"
    )

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument("-v", "--verbose",
        dest="verbose", action="count", default=0,
        help="print extra information"
    )
    noise_group.add_argument("-q", "--quiet",
        dest="quiet", action="store_true",
        help="silence all output, including errors"
    )

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("-l", "--log",
        dest="log_file", metavar="FILE", default="njkASM.log",
        help="write log file to custom location, "
             "default is njkASM.log"
    )
    log_group.add_argument("--no-log",
        dest="no_log", action="store_true",
        help="do not write an output log file"
    )

    return parser.parse_args()


def main() -> NoReturn:
    """Assemble an assembly source file into a memory initialization file.

    Parameters:
        Command line arguments parsed by Argparse

    Exit Codes:
        0 - Success
        1 - Error parsing arguments
        2 - Error reading source file
        3 - Error during assembly parsing/evaluation
        4 - Error writing output file
    """
    args = parse()
    log_setup(args.verbose, args.quiet, args.no_log, args.log_file)
    files_in = args.file
    file_out = args.out
    if file_out is None:
        file_out = f"{'.'.join(files_in[0].split('.')[:1])}.mif"

    log.debug(
        "Assembler ran with options:\n" +
        "\n".join(f"  {k} = {v}" for k, v in vars(args).items())
    )

    try:
        asm = Assembler(mem_size=args.mem_size)
        for file in files_in:
            asm.load_file(file)
        # Check file syntax and organize sections
        asm.pre_check()
        # Evaluate each section
        asm.eval_sections()
        # Write to output file
        asm.write_mif(file_out)
    except AssemblerError as e:
        exit(2, str(e))
    except OSError as e:
        exit(3, str(e))

    exit(0)


if __name__ == "__main__":
    main()
