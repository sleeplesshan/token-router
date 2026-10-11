"""Indexed ASCII component matching with an exact Unicode regex fallback."""
from __future__ import annotations

import re
from typing import Callable, Iterable


def compile_matcher(terms: Iterable[str]) -> Callable[[str], tuple[int, ...]]:
    """Compile matches equivalent to term_pattern().search for every input term.

    ASCII alphanumeric terms match whole alphanumeric components (underscores
    are boundaries). Complex terms retain individual regexes, preserving overlap.
    Non-ASCII lines use all original regexes because Python IGNORECASE includes
    non-ASCII equivalences such as Kelvin sign and dotted/dotless I.
    """
    terms = tuple(terms)
    patterns = tuple(re.compile(r"(?<![^\W_])" + re.escape(term) + r"(?![^\W_])",
                                re.IGNORECASE) for term in terms)
    indexed: dict[str, list[int]] = {}
    fallback = []
    for i, term in enumerate(terms):
        if term and term.isascii() and term.isalnum():
            indexed.setdefault(term.lower(), []).append(i)
        else:
            fallback.append((i, patterns[i]))
    components = re.compile(r"[a-z0-9]+")

    def matches(line: str) -> tuple[int, ...]:
        if not line.isascii():
            return tuple(i for i, pattern in enumerate(patterns) if pattern.search(line))
        found = set()
        if indexed:
            for component in components.findall(line.lower()):
                found.update(indexed.get(component, ()))
        for i, pattern in fallback:
            if pattern.search(line):
                found.add(i)
        return tuple(sorted(found))

    return matches
