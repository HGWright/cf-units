# Copyright cf-units contributors
#
# This file is part of cf-units and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.

"""
Compiles the UDUNITS-2 grammar using ANTLR4.

You may be interested in running this with entr to watch changes to the
grammar:

    echo udunits2*.g4* | entr -c "python compile.py"

You're welcome ;).

"""

import collections
import re
import subprocess
import urllib.request
from pathlib import Path

try:
    import jinja2
except ImportError:
    raise ImportError("Jinja2 needed to compile the grammar.")


JAR_NAME = "antlr-4.7.2-complete.jar"
JAR_URL = f"https://www.antlr.org/download/{JAR_NAME}"
HERE = Path(__file__).resolve().parent

JAR = HERE / JAR_NAME

LEXER = HERE / "parser" / "udunits2Lexer.g4"
PARSER = HERE / "udunits2Parser.g4"


def expand_lexer(source, target):
    MODE_P = re.compile(r"mode ([A-Z_]+)\;")
    TOKEN_P = re.compile(r"([A-Z_]+) ?\:.*")

    with open(source, "r") as fh:
        content = fh.read()

    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(
        content
    )

    current_mode = "DEFAULT_MODE"

    tokens = collections.defaultdict(list)

    for line in content.split("\n"):
        mode_g = MODE_P.match(line)
        if mode_g:
            current_mode = mode_g.group(1)

        token_g = TOKEN_P.match(line)
        if token_g:
            tokens[current_mode].append(token_g.group(1))

    new_content = template.render(tokens=tokens)
    with open(target, "w") as fh:
        fh.write(new_content)


def main():
    if not JAR.exists():
        print(f"Downloading {JAR_NAME}...")
        urllib.request.urlretrieve(JAR_URL, str(JAR))

    print("Expanding lexer...")
    expand_lexer(LEXER.parent.parent / (LEXER.name + ".jinja"), str(LEXER))

    print("Compiling lexer...")
    subprocess.run(
        [
            "java",
            "-jar",
            str(JAR),
            "-Dlanguage=Python3",
            str(LEXER),
            "-o",
            "parser",
        ],
        check=True,
    )

    print("Compiling parser...")
    subprocess.run(
        [
            "java",
            "-jar",
            str(JAR),
            "-Dlanguage=Python3",
            "-no-listener",
            "-visitor",
            str(PARSER),
            "-o",
            "parser",
        ],
        check=True,
    )

    print("Done.")


if __name__ == "__main__":
    main()
