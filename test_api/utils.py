from typing import Any
import re


def do_nothing(*_: list[Any]) -> None:
    return None


def regexp_replace(text, pattern, replacement, flags=""):
    if text is None:
        return None
    regex_flags = 0
    if "i" in flags.lower():
        regex_flags |= re.IGNORECASE
    return re.sub(pattern, replacement, text, flags=regex_flags)
