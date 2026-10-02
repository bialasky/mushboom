"""Public grzyby.pl report overlay. Comparison, not ground truth of fungi."""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any

import httpx

REPORT_URL = "https://www.grzyby.pl/foto/wystepowanie-0.htm"

WOJ_ALIASES = {
    "dolnośl.": "dolnośląskie",
    "kuj.-pom.": "kujawsko-pomorskie",
    "lubel.": "lubelskie",
    "lubus.": "lubuskie",
    "łódz.": "łódzkie",
    "małopol.": "małopolskie",
    "mazow.": "mazowieckie",
    "opols.": "opolskie",
    "podkarp.": "podkarpackie",
    "podlas.": "podlaskie",
    "pomor.": "pomorskie",
    "śląsk.": "śląskie",
    "św.-krz.": "świętokrzyskie",
    "war.-maz.": "warmińsko-mazurskie",
    "wlkpl.": "wielkopolskie",
    "zach.-pom.": "zachodniopomorskie",
}

WOJ_CODES = {
    "DS": "dolnośląskie",
    "KP": "kujawsko-pomorskie",
    "LB": "lubelskie",
    "LS": "lubuskie",
    "LD": "łódzkie",
    "MP": "małopolskie",
    "MZ": "mazowieckie",
    "OP": "opolskie",
    "PK": "podkarpackie",
    "PL": "podlaskie",
    "PM": "pomorskie",
    "SL": "śląskie",
    "SK": "świętokrzyskie",
    "WM": "warmińsko-mazurskie",
    "WP": "wielkopolskie",
    "ZP": "zachodniopomorskie",
}

# Header counters look like <!-- WOJ-DS --> (79) or mazowieckie (100/109).
WOJ_HEADER = re.compile(
    r"<!--\s*WOJ-([A-Z]{2})\s*-->\s*(?:\(([^)]*)\))?\s*<!--\s*END\s*-->",
    re.IGNORECASE,
)
WOJ_ALIAS_HEADER = re.compile(
    r"<b>\s*(" + "|".join(re.escape(alias) for alias in WOJ_ALIASES) + r")\s*</b>"
    r"(?:(?!</a>).)*?\((\d+(?:\s*/\s*\d+)?)\)",
    re.IGNORECASE | re.DOTALL,
)
PERIOD_MARK = re.compile(
    r"<!--\s*TYTUL-RAPORT-OD-DO\s*-->\s*([^<]+?)\s*<!--\s*END\s*-->",
    re.IGNORECASE,
)
WOJ_IN_REPORT = re.compile(
    r"woj\.\s+(dolnośląskie|kujawsko-pomorskie|lubelskie|lubuskie|łódzkie|"
    r"małopolskie|mazowieckie|opolskie|podkarpackie|podlaskie|pomorskie|"
    r"śląskie|świętokrzyskie|warmińsko-mazurskie|wielkopolskie|zachodniopomorskie)",
    re.IGNORECASE,
)
POW_LINE = re.compile(r"pow\.\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\s\-]+)", re.IGNORECASE)


def _count_from_header(raw: str | None) -> int:
    if not raw:
        return 0
    parts = [int(part) for part in re.findall(r"\d+", raw)]
    return max(parts) if parts else 0


def _empty_woj() -> dict[str, int]:
    return {name: 0 for name in WOJ_ALIASES.values()}


def _norm_powiat(raw: str) -> str:
    name = " ".join(raw.split()).strip(" .")
    if name.casefold().startswith("powiat "):
        return f"powiat {name[7:].strip()}"
    return f"powiat {name}"


def _counts_from_header(html: str) -> tuple[dict[str, int], int] | None:
    by_woj = _empty_woj()
    unknown = 0
    found = False
    for code, raw in WOJ_HEADER.findall(html):
        count = _count_from_header(raw)
        key = code.upper()
        if key == "ZZ":
            continue
        name = WOJ_CODES.get(key)
        if name is not None:
            by_woj[name] = count
            found = True
        elif key == "ZX":
            unknown = count
            found = True
    if found:
        return by_woj, unknown

    by_woj = _empty_woj()
    for alias, raw in WOJ_ALIAS_HEADER.findall(html):
        name = WOJ_ALIASES.get(alias.casefold()) or WOJ_ALIASES.get(alias)
        if name is None:
            folded = alias.casefold()
            name = next((value for key, value in WOJ_ALIASES.items() if key.casefold() == folded), None)
        if name is None:
            continue
        by_woj[name] = _count_from_header(raw)
        found = True
    if found:
        return by_woj, 0
    return None


def _counts_from_blocks(html: str) -> dict[str, int]:
    by_woj = _empty_woj()
    blocks = re.split(r"doniesienie-blok", html)
    haystacks = blocks[1:] if len(blocks) > 1 else [html]
    for block in haystacks:
        match = WOJ_IN_REPORT.search(block)
        if match:
            by_woj[match.group(1).casefold()] = by_woj.get(match.group(1).casefold(), 0) + 1
            continue
        folded = block.casefold()
        for name in WOJ_ALIASES.values():
            if f"woj. {name}" in folded:
                by_woj[name] += 1
                break
    return by_woj


def _parse(html: str) -> dict[str, Any]:
    header = _counts_from_header(html)
    if header is not None:
        by_woj, unknown = header
    else:
        by_woj = _counts_from_blocks(html)
        unknown = 0

    # Exact powiat names are login-gated on grzyby.pl. Keep the hook if a public page includes them.
    powiat_hits = Counter(_norm_powiat(match) for match in POW_LINE.findall(html))
    period_match = PERIOD_MARK.search(html)
    period = " ".join(period_match.group(1).split()) if period_match else None
    report_total = int(sum(by_woj.values()) + unknown)
    return {
        "by_woj": by_woj,
        "by_powiat": dict(powiat_hits),
        "unknown_location": unknown,
        "period": period,
        "report_total": report_total,
    }


def _note(period: str | None) -> str:
    window = f" for {period}" if period else ""
    return (
        f"Forager reports{window}, not mushroom counts. "
        "Totals come from the page header, not the last 50 posts. "
        "Empty counties are often empty of reporters."
    )


async def fetch_grzyby() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": "mushboom/0.1 (research comparison; +local)"},
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            response = await client.get(REPORT_URL)
            response.raise_for_status()
            parsed = _parse(response.text)
            return {
                "ok": True,
                "source": "grzyby.pl",
                "url": REPORT_URL,
                "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
                **parsed,
                "note": _note(parsed["period"]),
            }
    except Exception as exc:
        return {
            "ok": False,
            "source": "grzyby.pl",
            "url": REPORT_URL,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "by_woj": {},
            "by_powiat": {},
            "unknown_location": 0,
            "period": None,
            "report_total": 0,
            "error": str(exc),
            "note": "Could not reach grzyby.pl. Map still shows the weather model.",
        }


def intensity_for_county(
    name: str,
    woj: str,
    grzyby: dict[str, Any],
) -> dict[str, float | int]:
    by_powiat: dict[str, int] = grzyby.get("by_powiat") or {}
    by_woj: dict[str, int] = grzyby.get("by_woj") or {}
    direct = 0
    folded = name.casefold()
    for key, value in by_powiat.items():
        if key.casefold() == folded or key.casefold().removeprefix("powiat ") == folded.removeprefix(
            "powiat "
        ):
            direct += int(value)
    woj_count = int(by_woj.get(woj, 0))
    woj_max = max(by_woj.values()) if by_woj else 0
    powiat_max = max(by_powiat.values()) if by_powiat else 0
    woj_intensity = (100.0 * woj_count / woj_max) if woj_max else 0.0
    local_intensity = (100.0 * direct / powiat_max) if powiat_max and direct else 0.0
    intensity = local_intensity if direct else woj_intensity
    return {
        "reports": direct,
        "woj_reports": woj_count,
        "intensity": round(float(intensity), 1),
    }
