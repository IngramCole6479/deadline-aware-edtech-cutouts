from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.background_listing import CourseListing, reporting_decision


def test_deadline_within_three_days_enters_educator_review() -> None:
    listing = CourseListing("course-7", "Async Python", date(2026, 10, 28), "teacher@example.com")

    assert reporting_decision(listing, date(2026, 10, 25)) == "review"


def test_deadline_with_more_than_three_days_is_scheduled() -> None:
    listing = CourseListing("course-8", "HTTP Basics", date(2026, 11, 2), "teacher@example.com")

    assert reporting_decision(listing, date(2026, 10, 25)) == "scheduled"
