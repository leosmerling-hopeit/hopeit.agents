"""Data objects for the example tool."""

from hopeit.dataobjects import dataclass, dataobject


@dataobject
@dataclass
class RandomNumberRequest:
    """Request payload for the random number tool."""

    minimum: int = 0
    maximum: int = 100


@dataobject
@dataclass
class RandomNumberResult:
    """Tool response containing the generated value."""

    value: int
