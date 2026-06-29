"""
<Discipline Name> exec CLI — deterministic scripts for mechanical work.

Stages shell out to functions here for anything that does not require AI:
data transformations, format conversions, file I/O, API calls, calculations.

No AI logic in this file. No LLM calls. Pure Python.

Usage from a stage:
    from disciplines._template.lib.exec import your_function
    result = your_function(args)
"""


def example_transform(data: dict) -> dict:
    """
    Replace with your discipline's mechanical operations.
    Examples: parse a CSV, call an external API, format a report, validate a schema.
    """
    raise NotImplementedError("Replace with your discipline's exec functions")
