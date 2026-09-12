from __future__ import annotations

from brain_projectbet.database.models import MatchRecord, SnapshotRecord
from brain_projectbet.domain.models import MatchSnapshot


def snapshot_record_to_domain(match: MatchRecord, record: SnapshotRecord) -> MatchSnapshot:
    return MatchSnapshot(
        provider=match.provider,
        provider_match_id=match.provider_match_id,
        captured_at=record.captured_at,
        minute=record.minute,
        minute_extra=record.minute_extra,
        status=record.status,
        score_home=record.score_home,
        score_away=record.score_away,
        shots_home=record.shots_home,
        shots_away=record.shots_away,
        shots_on_target_home=record.shots_on_target_home,
        shots_on_target_away=record.shots_on_target_away,
        shots_off_target_home=record.shots_off_target_home,
        shots_off_target_away=record.shots_off_target_away,
        attacks_home=record.attacks_home,
        attacks_away=record.attacks_away,
        dangerous_attacks_home=record.dangerous_attacks_home,
        dangerous_attacks_away=record.dangerous_attacks_away,
        corners_home=record.corners_home,
        corners_away=record.corners_away,
        possession_home=record.possession_home,
        possession_away=record.possession_away,
        xg_home=record.xg_home,
        xg_away=record.xg_away,
        red_cards_home=record.red_cards_home,
        red_cards_away=record.red_cards_away,
        yellow_cards_home=record.yellow_cards_home,
        yellow_cards_away=record.yellow_cards_away,
        raw_metadata=record.raw_metadata,
    )
