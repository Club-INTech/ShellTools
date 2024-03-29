from typing import Any, Dict


class Match:
    """
    Create a pattern matcher

    Following syntaxes are valid :
    .. code-block:: python

        Match(value) & {(patterns : objects)...}
        (Match() & {(patterns : objects)...})(value)

    Patterns can be types or values.

    When trying to match the value against a pattern, the following sequence will be applied :
      - First, an attempt will be made to match by value; in that case, the corresponding object will be called if possible on zero parameters
      - If no match has been found, then an attempt will be made to match by type; in that case, if the corresponding object is callable on the value or no parameters, it will be called (the one parameter call will be choosen if the number of parameters of the functor is non-zero, regardless of whether there are default parameters or not)
      - In both case, if the corresponding object is not callable, it will simply be returned
    """

    def __init__(self, value: Any = None):
        self._value = value

    def __and__(self, patterns: Dict) -> Any:
        if self._value is not None:
            return _match_pattern(patterns, self._value)
        else:
            self._patterns = patterns
            return self

    def __call__(self, value: Any) -> Any:
        return _match_pattern(self._patterns, value)


def _match_pattern(patterns: Dict, value: Any) -> Any:
    # 'value' might not be hashable so we catch any exception that would come from patterns.get()
    object_by_value = None
    try:
        object_by_value = patterns.get(value)
    except:
        pass

    if object_by_value is not None:
        return object_by_value() if callable(object_by_value) else object_by_value

    object_by_type = patterns.get(type(value))
    if object_by_type is not None:
        return object_by_type(value) if callable(object_by_type) else object_by_type

    try:
        repr(value)
    except:
        pass

    raise RuntimeError(
        "Given value "
        + repr(value)
        + " of type "
        + type(value).__name__
        + " did not match any provided pattern"
    )
