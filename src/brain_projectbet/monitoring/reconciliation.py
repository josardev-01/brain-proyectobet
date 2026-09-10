from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Mapping, Sequence

from brain_projectbet.discovery.eligible import EligibleFixture


_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_IGNORED_TOKENS = {"afc", "cf", "club", "fc", "fk", "sc"}


def canonical_team_name(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    ascii_name = ascii_name.replace(".", "")
    tokens = [
        token for token in _NON_ALNUM.sub(" ", ascii_name.casefold()).split()
        if token not in _IGNORED_TOKENS
    ]
    return " ".join(tokens)


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


@dataclass(frozen=True, slots=True)
class FixtureLink:
    eligible: EligibleFixture
    live_fixture: Mapping[str, Any]
    confidence: float


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    links: tuple[FixtureLink, ...]
    unmatched_fixture_ids: tuple[str, ...]
    ambiguous_fixture_ids: tuple[str, ...]


def reconcile_apifootball_live(
    eligible: Sequence[EligibleFixture],
    live_payload: Mapping[str, Any],
    *,
    minimum_similarity: float = 0.88,
    minimum_margin: float = 0.08,
) -> ReconciliationResult:
    """Cruza IDs de proveedores por equipos y rechaza resultados dudosos."""
    live = tuple(live_payload.get("response", []))
    links: list[FixtureLink] = []
    unmatched: list[str] = []
    ambiguous: list[str] = []
    used_live_ids: set[str] = set()

    for registered in eligible:
        home = canonical_team_name(registered.home_team_name)
        away = canonical_team_name(registered.away_team_name)
        if not home or not away:
            unmatched.append(registered.fixture_id)
            continue
        scored = []
        for item in live:
            live_id = str(item.get("match_id", ""))
            if not live_id or live_id in used_live_ids:
                continue
            live_home = canonical_team_name(str(item.get("match_hometeam_name", "")))
            live_away = canonical_team_name(str(item.get("match_awayteam_name", "")))
            confidence = (_similarity(home, live_home) + _similarity(away, live_away)) / 2
            if confidence >= minimum_similarity:
                scored.append((confidence, live_id, item))
        scored.sort(key=lambda candidate: (-candidate[0], candidate[1]))
        if not scored:
            unmatched.append(registered.fixture_id)
            continue
        if len(scored) > 1 and scored[0][0] - scored[1][0] < minimum_margin:
            ambiguous.append(registered.fixture_id)
            continue
        confidence, live_id, item = scored[0]
        used_live_ids.add(live_id)
        links.append(FixtureLink(registered, item, confidence))

    return ReconciliationResult(tuple(links), tuple(unmatched), tuple(ambiguous))
