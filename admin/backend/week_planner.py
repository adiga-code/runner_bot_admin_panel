"""Standalone copy of engine/week_planner.py logic (run_bot new_logic branch).
Used by admin panel to create WeekPlan + DayPlan when activating users.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ── Constants (inlined from engine/constants.py) ──────────────────────────────
L1_LONG_RATIO_DEPENDENT: float = 1.30
L1_LONG_MAX_RATIO: float = 0.35
L2_LONG_MAX_RATIO: float = 0.35
L3_REGULAR_LONG_RATIO_BASE: float = 0.35
L3_REGULAR_LONG_RATIO_PREP: float = 0.40

L2_RECOVERY_RUN_MINUTES: int = 40
L3_REGULAR_RECOVERY_RUN_MINUTES: int = 60

L1_STRENGTH_MINUTES: dict = {"base_in": 30, "base": 30, "specialized": 30}
L2_STRENGTH_MINUTES: dict = {"base": 30, "preparatory": 40}
L3_REGULAR_STRENGTH_MINUTES: dict = {"base": (30, 50), "preparatory": (35, 50)}
L3_RETURN_STRENGTH_MINUTES: dict = {"base": 40, "preparatory": 50}

MAX_INTENSITY_PER_WEEK: dict = {
    ("L1", "base_in"): 0, ("L1", "base"): 1, ("L1", "specialized"): 2,
    ("L1", "recovery_period"): 0, ("L2", "base"): 1, ("L2", "preparatory"): 2,
    ("L3_REGULAR", "base"): 2, ("L3_REGULAR", "preparatory"): 2,
    ("L3_REGULAR", "recovery_period"): 0, ("L3_RETURN", "base"): 1,
    ("L3_RETURN", "preparatory"): 2,
}


def _round_int(x: float) -> int:
    return math.floor(x + 0.5)


def _get_long_max_ratio(level: int, period: str, injury_return: bool) -> float:
    if level == 1:
        return L1_LONG_MAX_RATIO
    if level == 2:
        return L2_LONG_MAX_RATIO
    if level == 3:
        return L3_REGULAR_LONG_RATIO_PREP if (not injury_return and period == "preparatory") else L3_REGULAR_LONG_RATIO_BASE
    return 0.35


# ── Dataclasses ───────────────────────────────────────────────────────────────
@dataclass
class DaySlot:
    day_of_week: int
    day_type: str
    run_subtype: object
    planned_minutes: int
    intensity: object
    is_key: bool = False


@dataclass
class WeekBlueprint:
    weekly_target_minutes: int
    is_recovery_week: bool
    days: list = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_weekdays(s: str) -> list:
    if not s:
        return [1, 3, 5]
    return sorted(int(d) for d in s.split(",") if d.strip())


def _get_strength_minutes(level: int, period: str, injury_return: bool) -> int:
    if level == 1:
        return L1_STRENGTH_MINUTES.get(period, 30)
    if level == 2:
        return L2_STRENGTH_MINUTES.get(period, 30)
    if level == 3:
        tbl = L3_RETURN_STRENGTH_MINUTES if injury_return else L3_REGULAR_STRENGTH_MINUTES
        val = tbl.get(period, 40)
        return val[0] if isinstance(val, tuple) else val
    return 30


def _get_level_key(level: int, injury_return: bool) -> str:
    if level == 1:
        return "L1"
    if level == 2:
        return "L2"
    if level == 3:
        return "L3_RETURN" if injury_return else "L3_REGULAR"
    return "L3_REGULAR"


def _count_run_days(level: int, period: str, injury_return: bool, n_total: int) -> int:
    if level == 1:
        return min(n_total, 3)
    if level == 2 or (level == 3 and injury_return):
        return min(n_total - 1, 4)
    return min(n_total - 2, 5)


def _split_running_minutes(
    weekly_target: int, level: int, period: str, injury_return: bool,
    n_run_days: int, is_long_independent: bool, is_recovery_week: bool,
) -> dict:
    if n_run_days == 0:
        return {"long": 0, "easy": 0, "aerobic": 0, "recovery_run": 0}

    long_ratio = _get_long_max_ratio(level, period, injury_return)

    if level == 1 and not is_long_independent:
        avg_run = weekly_target / n_run_days
        long = _round_int(min(avg_run * L1_LONG_RATIO_DEPENDENT, weekly_target * L1_LONG_MAX_RATIO))
    else:
        long = _round_int(weekly_target * long_ratio)

    long = min(long, weekly_target)
    remaining = weekly_target - long
    n_other = n_run_days - 1

    if n_other <= 0:
        return {"long": long, "easy": 0, "aerobic": 0, "recovery_run": 0}

    per_other = _round_int(remaining / n_other)

    if level == 1:
        return {"long": long, "easy": per_other, "aerobic": 0, "recovery_run": 0}

    if level == 2 or (level == 3 and injury_return):
        if n_other >= 2:
            rec_min = L2_RECOVERY_RUN_MINUTES
            aerobic_min = _round_int((remaining - rec_min) / (n_other - 1))
            if aerobic_min < rec_min:
                aerobic_min = _round_int(remaining / n_other)
                return {"long": long, "easy": aerobic_min, "aerobic": 0, "recovery_run": 0}
            return {"long": long, "easy": 0, "aerobic": aerobic_min, "recovery_run": rec_min}
        return {"long": long, "easy": 0, "aerobic": per_other, "recovery_run": 0}

    # L3 regular
    rec_min = L3_REGULAR_RECOVERY_RUN_MINUTES
    if n_other >= 2:
        aerobic_min = _round_int((remaining - rec_min) / (n_other - 1))
        return {"long": long, "easy": 0, "aerobic": aerobic_min, "recovery_run": rec_min}
    return {"long": long, "easy": 0, "aerobic": 0, "recovery_run": per_other}


def _layout_days(
    available: list, level: int, period: str, injury_return: bool,
    minutes: dict, add_intensity: bool, is_recovery_week: bool,
) -> list:
    n = len(available)
    slots: dict = {}
    strength_min = _get_strength_minutes(level, period, injury_return)
    level_key = _get_level_key(level, injury_return)

    if level == 3 and not injury_return:
        n_strength = 2
    else:
        n_strength = 2 if n >= 5 else 1

    n_run_total = max(1, n - n_strength)

    long_day = available[-1]
    slots[long_day] = DaySlot(
        day_of_week=long_day, day_type="run", run_subtype="long",
        planned_minutes=minutes["long"], intensity=None, is_key=True,
    )

    other_days = [d for d in available if d != long_day]

    run_subtypes: list = []
    if level == 1:
        run_subtypes = ["easy"] * (n_run_total - 1)
    elif level == 2 or (level == 3 and injury_return):
        other_run = n_run_total - 1
        if other_run > 0 and minutes.get("recovery_run", 0) > 0:
            run_subtypes = ["recovery_run"] + ["aerobic"] * max(0, other_run - 1)
        elif minutes.get("easy", 0) > 0:
            run_subtypes = ["easy"] * other_run
        else:
            run_subtypes = ["aerobic"] * other_run
    else:
        other_run = n_run_total - 1
        if other_run > 0 and minutes.get("recovery_run", 0) > 0:
            run_subtypes = ["recovery_run"] + ["aerobic"] * max(0, other_run - 1)
        else:
            run_subtypes = ["aerobic"] * other_run

    if add_intensity and run_subtypes and not is_recovery_week:
        max_intensity = MAX_INTENSITY_PER_WEEK.get((level_key, period), 0)
        if max_intensity >= 1:
            for i, sub in enumerate(run_subtypes):
                if sub in ("aerobic", "easy"):
                    run_subtypes[i] = "intervals"
                    break

    pre_long_day = long_day - 1
    forbidden_strength = {pre_long_day} if pre_long_day in other_days else set()

    strength_days: list = []
    run_days: list = []
    last_run_day = None

    for i, day in enumerate(other_days):
        days_remaining = len(other_days) - i
        strength_still_needed = n_strength - len(strength_days)
        run_still_needed = (n_run_total - 1) - len(run_days)

        would_be_consecutive_strength = bool(strength_days) and day == strength_days[-1] + 1
        would_be_consecutive_run = last_run_day is not None and day == last_run_day + 1

        can_be_strength = (
            strength_still_needed > 0
            and day not in forbidden_strength
            and not would_be_consecutive_strength
        )
        can_be_run_ideal = run_still_needed > 0 and not would_be_consecutive_run
        must_be_run = run_still_needed > 0 and days_remaining <= run_still_needed

        if must_be_run and strength_still_needed == 0:
            run_days.append(day); last_run_day = day
        elif can_be_strength and can_be_run_ideal:
            if strength_still_needed >= run_still_needed:
                strength_days.append(day)
            else:
                run_days.append(day); last_run_day = day
        elif can_be_strength:
            strength_days.append(day)
        elif can_be_run_ideal:
            run_days.append(day); last_run_day = day
        elif strength_still_needed > 0 and day not in forbidden_strength:
            strength_days.append(day)
        else:
            run_days.append(day); last_run_day = day

    while len(strength_days) < n_strength and run_days:
        strength_days.append(run_days.pop(0))

    key_strength_assigned = False
    for day in strength_days:
        is_key = not key_strength_assigned
        key_strength_assigned = True
        slots[day] = DaySlot(
            day_of_week=day, day_type="strength", run_subtype=None,
            planned_minutes=strength_min, intensity=None, is_key=is_key,
        )

    key_run_assigned = False
    for i, day in enumerate(run_days):
        sub = run_subtypes[i] if i < len(run_subtypes) else ("easy" if level == 1 else "aerobic")
        mins_map = {
            "easy": minutes.get("easy", 30),
            "recovery_run": minutes.get("recovery_run", 40),
            "aerobic": minutes.get("aerobic", 50),
            "intervals": minutes.get("aerobic", 50),
            "run_walk": minutes.get("easy", 30),
        }
        mins = mins_map.get(sub, minutes.get("aerobic", 50))
        intensity_val = "intervals" if sub == "intervals" else ("tempo" if sub == "tempo" else None)
        is_key = not key_run_assigned and sub not in ("recovery_run",)
        if is_key:
            key_run_assigned = True
        slots[day] = DaySlot(
            day_of_week=day, day_type="run", run_subtype=sub,
            planned_minutes=mins, intensity=intensity_val, is_key=is_key,
        )

    for day in set(range(1, 8)) - set(slots.keys()):
        slots[day] = DaySlot(
            day_of_week=day, day_type="rest", run_subtype=None,
            planned_minutes=0, intensity=None, is_key=False,
        )

    return sorted(slots.values(), key=lambda s: s.day_of_week)


# ── Public API ────────────────────────────────────────────────────────────────
def parse_available_weekdays(s) -> list:
    return _parse_weekdays(s or "1,3,5")


def build_week_plan(
    user,
    week_number: int,
    period: str,
    target_minutes: int,
    is_recovery_week: bool,
    available_weekdays: list,
    add_intensity: bool = False,
) -> WeekBlueprint:
    level = user.level or 1
    injury_return = bool(getattr(user, "injury_return_active", False))
    is_long_independent = bool(getattr(user, "l1_long_independent", False))

    if not available_weekdays:
        available_weekdays = _parse_weekdays(user.available_weekdays or "1,3,5")

    n_run_days = _count_run_days(level, period, injury_return, len(available_weekdays))

    minutes = _split_running_minutes(
        weekly_target=target_minutes, level=level, period=period,
        injury_return=injury_return, n_run_days=n_run_days,
        is_long_independent=is_long_independent, is_recovery_week=is_recovery_week,
    )

    days = _layout_days(
        available=available_weekdays, level=level, period=period,
        injury_return=injury_return, minutes=minutes,
        add_intensity=add_intensity and not is_recovery_week,
        is_recovery_week=is_recovery_week,
    )

    return WeekBlueprint(
        weekly_target_minutes=target_minutes,
        is_recovery_week=is_recovery_week,
        days=days,
    )
