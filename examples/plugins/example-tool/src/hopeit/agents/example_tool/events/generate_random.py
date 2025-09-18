"""Random number generator tool event."""

import random

from hopeit.app.api import event_api
from hopeit.app.context import EventContext
from hopeit.app.logger import app_extra_logger

from ..models import RandomNumberRequest, RandomNumberResult

__steps__ = ["generate_random"]

__api__ = event_api(
    summary="hopeit.agents example tool: generate random number",
    payload=(RandomNumberRequest, "Random number request"),
    responses={
        200: (RandomNumberResult, "Random number result"),
        400: (str, "Invalid bounds"),
    },
)

logger, extra = app_extra_logger()


async def generate_random(
    payload: RandomNumberRequest,
    context: EventContext,
) -> RandomNumberResult:
    """Return a random integer between minimum and maximum (inclusive)."""
    minimum, maximum = payload.minimum, payload.maximum
    if minimum > maximum:
        minimum, maximum = maximum, minimum
        logger.warning("random_bounds_swapped", extra=extra(minimum=maximum, maximum=minimum))

    value = random.randint(minimum, maximum)
    logger.info("random_generated", extra=extra(value=value, minimum=minimum, maximum=maximum))
    return RandomNumberResult(value=value)
