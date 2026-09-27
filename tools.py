"""
Phase 5 -- Custom tools for the follow-up agent (Stage D).

Three @tool-decorated functions the ReAct agent can call:
  - convert_currency:  currency/cost calculator (exchange conversion)
  - apply_discount:    currency/cost calculator (percentage math)
  - destination_info:  destination-info lookup

Rate tables and destination facts are small static stand-ins (no live
network calls), mirroring how the Custom Tools lab used mocked data --
swap in a real FX/weather API here if you have one available.
"""

from langchain_core.tools import tool

# --- static "reference data" the tools operate on -------------------------

_FX_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "IDR": 0.000064,   # Indonesian rupiah
    "THB": 0.028,      # Thai baht
    "JPY": 0.0067,
    "INR": 0.012,
}

_DESTINATION_INFO = {
    "bali": {
        "country": "Indonesia",
        "typical_weather": "Warm and humid year-round (26-31C); Apr-Oct is the drier season.",
        "best_months": "May, June, September",
    },
    "paris": {
        "country": "France",
        "typical_weather": "Mild; cool winters (0-8C), warm summers (15-25C).",
        "best_months": "April, May, September, October",
    },
    "bangkok": {
        "country": "Thailand",
        "typical_weather": "Hot and humid most of the year; Nov-Feb is coolest and driest.",
        "best_months": "November, December, January",
    },
    "tokyo": {
        "country": "Japan",
        "typical_weather": "Four distinct seasons; mild spring/autumn, hot humid summer.",
        "best_months": "March, April, October, November",
    },
}


def _clean_currency_code(code: str) -> str:
    return code.strip().upper()


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount of money from one currency to another.

    Args:
        amount: the numeric amount to convert.
        from_currency: 3-letter currency code it's currently in (e.g. "USD").
        to_currency: 3-letter currency code to convert it into (e.g. "IDR").
    """
    src = _clean_currency_code(from_currency)
    dst = _clean_currency_code(to_currency)

    if src not in _FX_RATES_TO_USD or dst not in _FX_RATES_TO_USD:
        known = ", ".join(sorted(_FX_RATES_TO_USD))
        return f"Unknown currency code. I know: {known}."

    usd_amount = amount * _FX_RATES_TO_USD[src]
    converted = usd_amount / _FX_RATES_TO_USD[dst]
    return f"{amount:,.2f} {src} is approximately {converted:,.2f} {dst}."


@tool
def apply_discount(amount: float, discount_percent: float) -> str:
    """Apply a percentage discount to a price and return the discounted total.

    Args:
        amount: the original price.
        discount_percent: the discount to apply, e.g. 15 for 15% off.
    """
    if discount_percent < 0 or discount_percent > 100:
        return "Discount percent should be between 0 and 100."

    discounted = amount * (1 - discount_percent / 100)
    savings = amount - discounted
    return (
        f"{discount_percent:.0f}% off {amount:,.2f} is {discounted:,.2f} "
        f"(you save {savings:,.2f})."
    )


@tool
def destination_info(destination: str) -> str:
    """Look up general travel info (country, typical weather, best months) for a destination.

    Args:
        destination: the destination name, e.g. "Bali".
    """
    key = destination.strip().lower()
    info = _DESTINATION_INFO.get(key)
    if info is None:
        known = ", ".join(sorted(d.title() for d in _DESTINATION_INFO))
        return f"No info on file for '{destination}'. I have info for: {known}."

    return (
        f"{destination.title()}, {info['country']}: {info['typical_weather']} "
        f"Best months to visit: {info['best_months']}."
    )


ALL_TOOLS = [convert_currency, apply_discount, destination_info]
