from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping, Sequence

from brain_projectbet.domain.models import MatchSnapshot


_CLOCK = re.compile(r"^(\d+)(?:\+(\d+))?")
_STATUS_MAP = {
    "half time": "HT",
    "int.": "HT",
    "finished": "FT",
    "after extra time": "AET",
    "after penalties": "PEN",
    "postponed": "PST",
    "cancelled": "CANC",
    "abandoned": "ABD",
}


def _number(value: Any) -> int | float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str) and value.endswith("%"):
        value = value[:-1]
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _clock(value: Any) -> tuple[int | None, int | None, str]:
    raw = str(value or "").strip()
    match = _CLOCK.match(raw)
    if match:
        minute = int(match.group(1))
        extra = int(match.group(2)) if match.group(2) else None
        return minute, extra, "1H" if minute < 45 else "2H"
    return None, None, _STATUS_MAP.get(raw.casefold(), "UNKNOWN")


def _statistics(items: Sequence[Mapping[str, Any]]) -> dict[str, tuple[Any, Any]]:
    return {
        str(item.get("type", "")).casefold(): (item.get("home"), item.get("away"))
        for item in items
    }


def normalize_snapshot(
    fixture: Mapping[str, Any],
    *,
    captured_at: datetime,
    canonical_provider: str = "apifootball-com",
    canonical_match_id: str | None = None,
) -> MatchSnapshot:
    """Normaliza un evento de APIFootball, conservando el ID de origen en metadata."""
    stats = _statistics(fixture.get("statistics", []))
    minute, minute_extra, status = _clock(fixture.get("match_status"))
    on_target = stats.get("on target", (None, None))
    off_target = stats.get("off target", (None, None))
    shots_home = None
    shots_away = None
    if _number(on_target[0]) is not None and _number(off_target[0]) is not None:
        shots_home = int(_number(on_target[0]) + _number(off_target[0]))
    if _number(on_target[1]) is not None and _number(off_target[1]) is not None:
        shots_away = int(_number(on_target[1]) + _number(off_target[1]))

    source_match_id = str(fixture.get("match_id", ""))
    home_name = str(fixture.get("match_hometeam_name", ""))
    away_name = str(fixture.get("match_awayteam_name", ""))
    return MatchSnapshot(
        provider=canonical_provider,
        provider_match_id=canonical_match_id or source_match_id,
        captured_at=captured_at,
        minute=minute,
        minute_extra=minute_extra,
        status=status,
        home_team_id=str(fixture.get("match_hometeam_id", "")) or None,
        away_team_id=str(fixture.get("match_awayteam_id", "")) or None,
        score_home=_number(fixture.get("match_hometeam_score")),
        score_away=_number(fixture.get("match_awayteam_score")),
        shots_home=shots_home,
        shots_away=shots_away,
        shots_on_target_home=_number(on_target[0]),
        shots_on_target_away=_number(on_target[1]),
        dangerous_attacks_home=_number(stats.get("dangerous attacks", (None, None))[0]),
        dangerous_attacks_away=_number(stats.get("dangerous attacks", (None, None))[1]),
        corners_home=_number(stats.get("corners", (None, None))[0]),
        corners_away=_number(stats.get("corners", (None, None))[1]),
        possession_home=_number(stats.get("ball possession", (None, None))[0]),
        possession_away=_number(stats.get("ball possession", (None, None))[1]),
        raw_metadata={
            "source_provider": "apifootball-com",
            "source_match_id": source_match_id,
            "shots_derived_from": "on_target_plus_off_target",
            "league": {
                "name": fixture.get("league_name"),
                "country": fixture.get("country_name"),
            },
            "team_names": {
                "home": {"name": home_name},
                "away": {"name": away_name},
            },
        },
    )
