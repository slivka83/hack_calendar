#!/usr/bin/env python3
"""Парсер current_hacks.md -> data.js (данные для index.html)."""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "current_hacks.md"
OUT = HERE / "data.js"

YEAR = 2026
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def to_iso(day, month):
    day = max(1, min(day, MONTH_DAYS[month - 1]))
    return f"{YEAR}-{month:02d}-{day:02d}"


def parse_dates(raw):
    """'📅 9.02 – 30.03 (рег. до 4.04)' -> dict с датами."""
    main = raw.split("(", 1)[0]
    result = {"start": None, "end": None, "start_approx": False,
              "registration": None, "phases": None}

    reg_m = re.search(r"рег\.?\s*(до|с)\s*(\d{1,2})\.(\d{1,2})", raw)
    if reg_m:
        result["registration"] = f"{reg_m.group(1)} {int(reg_m.group(2))}.{int(reg_m.group(3)):02d}"

    parts = [p for p in main.split("|") if p.strip()]
    if len(parts) > 1:
        phases = []
        for part in parts:
            pairs = re.findall(r"(\d{1,2}|XX)\.(\d{1,2})", part)
            if len(pairs) < 2:
                continue
            label = re.sub(r"[\d.]+", "", part).strip(" -–").strip()
            (d1, m1), (d2, m2) = pairs[0], pairs[-1]
            approx = d1 == "XX"
            phases.append({
                "label": label,
                "start": to_iso(1 if approx else int(d1), int(m1)),
                "end": to_iso(int(d2), int(m2)),
                "start_approx": approx,
            })
        if phases:
            result["phases"] = phases
            result["start"] = phases[0]["start"]
            result["end"] = phases[-1]["end"]
            result["start_approx"] = phases[0]["start_approx"]
    else:
        pairs = re.findall(r"(\d{1,2}|XX)\.(\d{1,2})", main)
        if len(pairs) >= 2:
            (d1, m1), (d2, m2) = pairs[0], pairs[-1]
            result["start_approx"] = d1 == "XX"
            result["start"] = to_iso(1 if result["start_approx"] else int(d1), int(m1))
            result["end"] = to_iso(int(d2), int(m2))

    return result


def main():
    hacks = []
    cur = None

    for line in SRC.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r"^\[(СОР|ХАК)\]\s+(.+)$", line)
        if m:
            cur = {"type": m.group(1), "name": m.group(2), "tasks": [],
                   "prize": None, "participation": None, "format": None,
                   "lang": None, "registration": None, "phases": None,
                   "start": None, "end": None, "start_approx": False}
            hacks.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("📅"):
            cur.update(parse_dates(line))
        elif line.startswith("💡"):
            cur["tasks"].append(line.lstrip("💡").strip())
        elif line.startswith("💰"):
            cur["prize"] = line.lstrip("💰").strip()
        elif line.startswith("🏀"):
            cur["participation"] = line.lstrip("🏀").strip()
        elif line.startswith("🌐"):
            cur["format"] = line.lstrip("🌐").strip()
        elif line.startswith("🖥️"):
            cur["lang"] = line.lstrip("🖥️").strip()

    hacks.sort(key=lambda h: h["start"] or h["end"] or "")
    OUT.write_text("const HACKS = " + json.dumps(hacks, ensure_ascii=False, indent=2) + ";\n",
                   encoding="utf-8")
    print(f"OK: {len(hacks)} событий -> {OUT.name}")


if __name__ == "__main__":
    main()