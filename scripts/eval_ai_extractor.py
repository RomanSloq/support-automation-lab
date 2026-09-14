"""Opt-in live evaluation for the OpenAI ticket-facts extractor."""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ai_extractor import AIExtractorError, extract_ticket


CASES = [
    {
        "name": "mass availability risk",
        "text": "У нас в трёх отелях перестали обновляться свободные номера на площадках, боимся овербукинга.",
        "expected": {
            "affected_properties": 3,
            "issue_type": "availability_sync",
            "overbooking_risk": True,
        },
    },
    {
        "name": "one Booking reservation missing",
        "text": "Одна бронь Booking не появилась в PMS.",
        "expected": {
            "issue_type": "reservation_sync",
            "affected_bookings": 1,
            "problem_active": None,
        },
    },
    {
        "name": "active 401 reservation sync",
        "text": "Синхронизация бронирований сейчас не работает, получаем ошибку 401.",
        "expected": {
            "issue_type": "reservation_sync",
            "error_code": 401,
            "problem_active": True,
        },
    },
    {
        "name": "emotional unsupported rate-plan issue",
        "text": "СРОЧНО! Не могу сейчас открыть тарифный план для просмотра.",
        "expected": {
            "issue_type": None,
            "claimed_urgency": "high",
            "problem_active": True,
        },
    },
    {
        "name": "suspected duplicate with immediate check-in",
        "text": "Сейчас видим две предположительно дублирующиеся брони, гости заселяются прямо сейчас, проблема ещё активна.",
        "expected": {
            "issue_type": "suspected_duplicate_booking",
            "affected_bookings": 2,
            "next_checkin_hours": 0,
            "problem_active": True,
        },
    },
    {
        "name": "insufficient emotional report",
        "text": "ААААА ПОМОГИТЕ, ВСЁ СЛОМАЛОСЬ, СРОЧНО!!!",
        "expected": {
            "affected_properties": None,
            "issue_type": None,
            "affected_bookings": None,
            "claimed_urgency": "high",
        },
    },
]

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost_usd",
)
OPTIONAL_USAGE_FIELDS = ("cache_write_tokens", "reasoning_tokens")


def print_usage(usage):
    print("USAGE:")
    for field in USAGE_FIELDS:
        print(f"{field} = {usage[field]}")
    for field in OPTIONAL_USAGE_FIELDS:
        if usage[field]:
            print(f"{field} = {usage[field]}")


def add_usage(total_usage, usage):
    for field in USAGE_FIELDS[:-1]:
        total_usage[field] += usage[field]
    for field in OPTIONAL_USAGE_FIELDS:
        total_usage[field] += usage[field]
    if usage["estimated_cost_usd"] is not None:
        total_usage["estimated_cost_usd"] += Decimal(str(usage["estimated_cost_usd"]))
        total_usage["estimated_cost_cases"] += 1


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("AI EVAL NOT RUN: OPENAI_API_KEY is not set.")
        return 2

    passed = 0
    total_usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": Decimal("0"),
        "estimated_cost_cases": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
    }
    for case in CASES:
        print(f"\nCASE: {case['name']}")
        print("RAW TEXT:", case["text"])
        try:
            extraction = extract_ticket(case["text"])
        except AIExtractorError as error:
            print("ERROR:", error.code)
            continue

        facts = extraction.facts
        print_usage(extraction.usage)
        add_usage(total_usage, extraction.usage)

        failures = {
            field: {"expected": expected, "actual": facts.get(field)}
            for field, expected in case["expected"].items()
            if facts.get(field) != expected
        }
        print("ACTUAL FACTS:", json.dumps(facts, ensure_ascii=False, indent=2))
        print("EXPECTED IMPORTANT FIELDS:", json.dumps(case["expected"], ensure_ascii=False))
        if failures:
            print("RESULT: FAIL")
            print("MISMATCHES:", json.dumps(failures, ensure_ascii=False, indent=2))
        else:
            print("RESULT: PASS")
            passed += 1

    print(f"\nAI EVAL: {passed}/{len(CASES)} PASS")
    print("TOTAL USAGE:")
    for field in USAGE_FIELDS[:-1]:
        print(f"{field} = {total_usage[field]}")
    for field in OPTIONAL_USAGE_FIELDS:
        if total_usage[field]:
            print(f"{field} = {total_usage[field]}")
    if total_usage["estimated_cost_cases"]:
        print(f"estimated_cost_usd = {float(total_usage['estimated_cost_usd'])}")
        average = total_usage["estimated_cost_usd"] / total_usage["estimated_cost_cases"]
        print(f"AVERAGE ESTIMATED COST PER CASE: ${float(average):.10f}")
    else:
        print("estimated_cost_usd = unavailable for the configured model")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
