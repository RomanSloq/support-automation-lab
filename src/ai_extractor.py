"""OpenAI-backed extraction and normalization of ticket facts."""

import json
import os
from dataclasses import dataclass
from decimal import Decimal

from src.ticket_contract import FACT_FIELDS, TICKET_FACTS_JSON_SCHEMA, validate_ticket_facts

DEFAULT_MODEL = "gpt-5.6-luna"

# OpenAI GPT-5.6 Luna text pricing, retrieved 2026-09-15. Values are USD per
# million tokens and produce an estimate, not an invoice.
PRICING_AS_OF = "2026-09-15"
LUNA_PRICING_USD_PER_MILLION = {
    "input": Decimal("0.20"),
    "cached_input": Decimal("0.02"),
    "cache_write": Decimal("0.25"),
    "output": Decimal("1.20"),
}
TOKENS_PER_MILLION = Decimal("1000000")

EXTRACTION_INSTRUCTIONS = """Extract and normalize only facts supported by the ticket contract.
Do not guess. Use null when the client did not provide a fact.
Normalize explicit meaning into only these issue_type values: availability_sync,
reservation_sync, suspected_duplicate_booking. Use null for unsupported or unknown types.
Use a supported issue_type only when the message clearly matches that category; never choose a
closest match. availability_sync means availability, inventory, or free-room data is being
updated or synchronized between systems or channels. Access to, viewing of, or a generic problem
with a rate plan is not availability_sync; use null when no supported category clearly matches.
Set problem_active to true only when the message clearly says the problem is ongoing now,
false only when it clearly says the problem is resolved, otherwise null.
Set next_checkin_hours to 0 only when check-in or guest arrival is explicitly happening now,
right now, or immediately. Normalize an explicit "in N hours" statement to N. "Today" alone
does not establish 0; otherwise use null.
Normalize explicitly claimed urgency to low, normal, or high; otherwise use null.
Treat claimed urgency as a customer statement, never as priority.
An overbooking concern explicitly reported by the customer may be overbooking_risk=true;
this means reported risk, not independently verified external-system risk.
Do not choose route, priority, human_review_required, or any action."""


class AIExtractorError(RuntimeError):
    """Technical AI extraction failure with a safe public error category."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ExtractionResult:
    """Validated ticket facts plus non-business diagnostics for one AI call."""

    facts: dict
    usage: dict


def _find_refusal(response):
    for output in getattr(response, "output", None) or []:
        for content in getattr(output, "content", None) or []:
            if getattr(content, "type", None) == "refusal":
                return getattr(content, "refusal", "refused")
    return None


def _integer_usage(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _optional_usage(response_usage, details_name, field):
    details = getattr(response_usage, details_name, None)
    value = getattr(details, field, 0)
    return _integer_usage(value, field)


def _luna_pricing_applies(model):
    return model == DEFAULT_MODEL or model.startswith(f"{DEFAULT_MODEL}-")


def _usage_metadata(response, requested_model):
    response_usage = getattr(response, "usage", None)
    if response_usage is None:
        raise ValueError("response usage is missing")

    input_tokens = _integer_usage(getattr(response_usage, "input_tokens", None), "input_tokens")
    output_tokens = _integer_usage(
        getattr(response_usage, "output_tokens", None), "output_tokens"
    )
    total_tokens = _integer_usage(getattr(response_usage, "total_tokens", None), "total_tokens")
    cached_input_tokens = _optional_usage(
        response_usage, "input_tokens_details", "cached_tokens"
    )
    cache_write_tokens = _optional_usage(
        response_usage, "input_tokens_details", "cache_write_tokens"
    )
    reasoning_tokens = _optional_usage(
        response_usage, "output_tokens_details", "reasoning_tokens"
    )
    uncached_input_tokens = input_tokens - cached_input_tokens - cache_write_tokens
    if uncached_input_tokens < 0:
        raise ValueError("input token details exceed input_tokens")

    actual_model = getattr(response, "model", None) or requested_model
    metadata = {
        "model": actual_model,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "cache_write_tokens": cache_write_tokens,
        "uncached_input_tokens": uncached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": None,
    }
    if _luna_pricing_applies(actual_model):
        estimated_cost = (
            Decimal(uncached_input_tokens) * LUNA_PRICING_USD_PER_MILLION["input"]
            + Decimal(cached_input_tokens)
            * LUNA_PRICING_USD_PER_MILLION["cached_input"]
            + Decimal(cache_write_tokens)
            * LUNA_PRICING_USD_PER_MILLION["cache_write"]
            + Decimal(output_tokens) * LUNA_PRICING_USD_PER_MILLION["output"]
        ) / TOKENS_PER_MILLION
        metadata["estimated_cost_usd"] = float(estimated_cost)
    return metadata


def extract_ticket(text, client=None, model=None):
    """Use the Responses API to extract facts and return usage diagnostics."""
    if not isinstance(text, str) or not text.strip():
        raise AIExtractorError("empty_text")

    api_key = os.getenv("OPENAI_API_KEY")
    if client is None and not api_key:
        raise AIExtractorError("missing_api_key")

    try:
        from openai import (
            APIConnectionError,
            APIStatusError,
            AuthenticationError,
            OpenAI,
            OpenAIError,
            RateLimitError,
        )
    except ImportError as error:
        raise AIExtractorError("sdk_unavailable") from error

    if client is None:
        client = OpenAI(api_key=api_key, max_retries=0, timeout=30.0)

    requested_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    try:
        response = client.responses.create(
            model=requested_model,
            instructions=EXTRACTION_INSTRUCTIONS,
            input=text.strip(),
            reasoning={"effort": "none"},
            store=False,
            max_output_tokens=400,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ticket_facts",
                    "strict": True,
                    "schema": TICKET_FACTS_JSON_SCHEMA,
                }
            },
        )
    except AuthenticationError as error:
        raise AIExtractorError("authentication_failed") from error
    except RateLimitError as error:
        raise AIExtractorError("quota_or_rate_limit") from error
    except APIConnectionError as error:
        raise AIExtractorError("network_error") from error
    except APIStatusError as error:
        if getattr(error, "status_code", None) in (402, 429):
            raise AIExtractorError("quota_or_rate_limit") from error
        raise AIExtractorError("api_error") from error
    except OpenAIError as error:
        raise AIExtractorError("api_error") from error

    if getattr(response, "status", None) != "completed":
        raise AIExtractorError("incomplete_response")
    if _find_refusal(response):
        raise AIExtractorError("refused_response")

    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise AIExtractorError("invalid_response")

    try:
        facts = json.loads(output_text)
        if not isinstance(facts, dict):
            raise ValueError("facts must be an object")
        if set(facts) != set(FACT_FIELDS):
            raise ValueError("response must contain exactly the ticket contract fields")
        validate_ticket_facts(facts)
    except (json.JSONDecodeError, ValueError) as error:
        raise AIExtractorError("invalid_response") from error

    try:
        usage = _usage_metadata(response, requested_model)
    except ValueError as error:
        raise AIExtractorError("invalid_response") from error
    return ExtractionResult(facts=facts, usage=usage)


def extract_facts(text, client=None, model=None):
    """Compatibility helper for callers that need only the business facts."""
    return extract_ticket(text, client=client, model=model).facts
