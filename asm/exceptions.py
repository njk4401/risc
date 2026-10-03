class AssemblerError(Exception):
    """Custom Exception class for assembler errors with line context.

    Attributes:
        file:
            The name of the source file that
            rose this exception, if relevant.
        line:
            The line number of the source file that
            rose this exception, if relevant.
        raw:
            The raw line within the source file that
            rose this exception, if relevant.
    """

    def __init__(
        self,
        msg: str,
        file: str = None,
        line: int = None,
        raw: str = None
    ) -> None:
        """Create a new AssemblerError Exception.

        Parameters:
            msg:
                Message to correlate with error.
            file:
                Name of the source file that rose the error.
            line:
                Line number that error occurs on.
            raw:
                Raw text string which caused error.
                Requires `line` to also be passed
                to have any effect on the error message.
        """
        message: list[str] = []
        self.file = file or ""
        self.line = line or 0
        self.raw = raw or ""

        if file is not None:
            message.append(f"[{file}] ")

        if line is not None:
            message.append(f"Line {line}:")
            if raw is not None:
                message.append(f" {raw!r}")
            message.append("\n")
        message.append(msg)

        super().__init__("".join(message))
