"""Unit tests for social publishing and prime-time scheduling."""

from datetime import datetime, timezone, timedelta
from clipora.integrations.social_publisher import SmartScheduler
from clipora.publishing.intent_journal import IntentJournal, PublishStatus

def test_smart_scheduler_calculates_prime_time():
    # Base: 2026-06-15 10:00:00 UTC
    base = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    slot = SmartScheduler.calculate_prime_time_slot(existing_slots=[], base_time=base)
    # Should schedule at 18:00 UTC on same day
    assert slot.hour == 18
    assert slot.day == 15

def test_smart_scheduler_maintains_min_gap():
    base = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    existing_slot = datetime(2026, 6, 15, 18, 0, 0, tzinfo=timezone.utc)
    slot = SmartScheduler.calculate_prime_time_slot(
        existing_slots=[existing_slot],
        base_time=base,
        min_gap_seconds=5400, # 90 min
    )
    # Should be pushed to 19:30 UTC
    assert (slot - existing_slot).total_seconds() >= 5400

def test_intent_journal_lifecycle(tmp_path):
    journal_path = tmp_path / "publish_intents.json"
    journal = IntentJournal(journal_path)

    intent = journal.record_intent(
        intent_id="int_1",
        idempotency_key="key_1",
        job_id="job_1",
        clip_index=0,
        platforms=["tiktok"],
    )
    assert intent["status"] == PublishStatus.PENDING

    updated = journal.update_intent("int_1", status=PublishStatus.CONFIRMED, post_id="post_999")
    assert updated["status"] == PublishStatus.CONFIRMED
    assert updated["post_id"] == "post_999"
