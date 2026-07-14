"""Shared, dependency-free helpers for protecting report math spans."""

import re


MATH_TOKEN = "PAPERWIKIMATH{:04d}TOKEN"
FENCED_CODE_RE = re.compile(r"^```[^\n]*\n.*?^```[ \t]*$", re.M | re.S)
DISPLAY_MATH_RE = re.compile(r"(?<!\\)\$\$(.*?)(?<!\\)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)")


def _protect_math_segment(text: str, formulas: list[str]) -> str:
    """Replace math outside code fences with Markdown-safe placeholders."""
    display_delimiters = re.findall(r"(?<!\\)\$\$", text)
    if len(display_delimiters) % 2:
        raise ValueError("Unpaired math delimiter '$$' in report")

    def replace(match: re.Match) -> str:
        token = MATH_TOKEN.format(len(formulas))
        if token in text:
            raise ValueError(f"Math placeholder collision: {token}")
        formulas.append(match.group(0))
        return token

    text = DISPLAY_MATH_RE.sub(replace, text)
    return INLINE_MATH_RE.sub(replace, text)


def protect_math(text: str) -> tuple[str, list[str]]:
    """Protect LaTeX spans while leaving fenced code blocks untouched."""
    formulas: list[str] = []
    parts = []
    cursor = 0
    for match in FENCED_CODE_RE.finditer(text):
        parts.append(_protect_math_segment(text[cursor : match.start()], formulas))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(_protect_math_segment(text[cursor:], formulas))
    return "".join(parts), formulas
