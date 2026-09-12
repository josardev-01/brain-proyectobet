from __future__ import annotations

from brain_projectbet.providers.base import RateLimitStatus


def quota_block_reason(
    limits: RateLimitStatus,
    *,
    requested: int,
    daily_reserve: int,
    minute_reserve: int = 0,
) -> str | None:
    if requested < 0 or daily_reserve < 0 or minute_reserve < 0:
        raise ValueError("requested y las reservas no pueden ser negativos")
    if (
        limits.daily_remaining is not None
        and limits.daily_remaining - requested < daily_reserve
    ):
        return "daily_reserve"
    if (
        limits.minute_remaining is not None
        and limits.minute_remaining - requested < minute_reserve
    ):
        return "minute_reserve"
    return None
