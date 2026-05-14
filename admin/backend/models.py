from sqlalchemy import (
    BigInteger, Boolean, Column, Date, Integer,
    String, Text, DateTime, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from dependencies import Base


class User(Base):
    __tablename__ = "users"

    telegram_id              = Column(BigInteger, primary_key=True)
    full_name                = Column(String(200))
    last_name                = Column(String(100))
    first_name               = Column(String(100))
    middle_name              = Column(String(100))
    gender                   = Column(String(10))
    birth_date               = Column(Date)
    country                  = Column(String(100))
    city                     = Column(String(100))
    district                 = Column(String(100))
    timezone_offset          = Column(Integer, default=3)
    level                    = Column(Integer)
    strength_format          = Column(String(10))
    program_start_date       = Column(Date)
    week_repeat_count        = Column(Integer, default=0)
    morning_reminder_hour    = Column(Integer, default=8)
    evening_reminder_hour    = Column(Integer, default=20)
    reminders_enabled        = Column(Boolean, default=True)
    extended_week5           = Column(Boolean, default=False)
    is_active                = Column(Boolean, default=True)
    status                   = Column(String(20), default="pending")
    onboarding_complete      = Column(Boolean, default=False)
    role                     = Column(String(20), default="athlete")
    created_at               = Column(DateTime(timezone=True))

    # Onboarding answers
    q_goal                   = Column(String(50))
    q_distance               = Column(String(20))
    q_race_date              = Column(String(50))
    q_runs                   = Column(String(20))
    q_frequency              = Column(String(20))
    q_volume                 = Column(String(20))
    q_longest_run            = Column(String(20))
    q_structure              = Column(String(10))
    q_experience             = Column(String(20))
    q_break                  = Column(String(20))
    q_break_duration         = Column(String(20))
    q_run_feel               = Column(String(20))
    q_pain                   = Column(String(20))
    q_pain_location          = Column(String(200))
    q_pain_increases         = Column(String(20))
    q_injury_history         = Column(String(10))
    q_other_sports           = Column(String(200))
    q_strength_frequency     = Column(String(20))
    q_regularity             = Column(String(20))
    q_strength               = Column(String(20))
    q_self_level             = Column(String(20))
    q_continuous_run_test    = Column(String(10))
    q_gadget                 = Column(String(10))
    q_gadget_types           = Column(String(200))
    q_gadget_sharing         = Column(String(10))

    # New-logic program state
    available_weekdays       = Column(String(20))
    weekly_target_minutes    = Column(Integer)
    peak_volume_minutes      = Column(Integer)
    last_successful_volume   = Column(Integer)
    current_period           = Column(String(30))
    period_start_date        = Column(Date)
    period_week_number       = Column(Integer, default=1)
    cycle_number             = Column(Integer, default=1)
    cycle_start_date         = Column(Date)
    program_week_number      = Column(Integer, default=1)
    growth_streak            = Column(Integer, default=0)
    weeks_since_recovery     = Column(Integer, default=0)

    # Red flag
    red_flag_active          = Column(Boolean, default=False)
    red_flag_reason          = Column(String(100))
    red_flag_at              = Column(Date)

    # Entry & goal
    has_goal_race            = Column(Boolean, default=False)
    entry_point              = Column(String(20))

    # Return-mode
    injury_return_active     = Column(Boolean, default=False)
    target_level             = Column(Integer)
    return_mode_started_at   = Column(Date)

    # L3 macrocycle
    in_macrocycle_recovery   = Column(Boolean, default=False)
    macrocycle_recovery_week = Column(Integer, default=0)
    macrocycle_peak_volume   = Column(Integer)

    # L1 long stage
    l1_long_independent      = Column(Boolean, default=False)
    l1_no_pain_streak_weeks  = Column(Integer, default=0)
    l1_easy_reached_40min    = Column(Boolean, default=False)

    logs       = relationship("SessionLog", back_populates="user")
    week_plans = relationship("WeekPlan", back_populates="user")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    user_id              = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    date                 = Column(Date, nullable=False)
    day_index            = Column(Integer, nullable=False)
    wellbeing            = Column(Integer)
    sleep_quality        = Column(Integer)
    pain_level           = Column(Integer)
    pain_increases       = Column(Boolean)
    stress_level         = Column(Integer)
    assigned_workout_id  = Column(Integer, ForeignKey("workouts.id"))
    assigned_version     = Column(String(20))
    completion_status    = Column(String(20))
    effort_level         = Column(Integer)
    completion_pain      = Column(Boolean)
    red_flag             = Column(Boolean, default=False)
    fatigue_reduction    = Column(Boolean, default=False)
    morning_sent         = Column(Boolean, default=False)
    evening_sent         = Column(Boolean, default=False)
    checkin_done         = Column(Boolean, default=False)
    checkin_at           = Column(DateTime(timezone=True))
    approval_pending     = Column(Boolean, default=False)
    created_at           = Column(DateTime(timezone=True))
    # New-logic fields (no FK to avoid circular dependency at ORM level)
    week_plan_id         = Column(Integer)
    day_plan_id          = Column(Integer)
    day_of_week          = Column(Integer)
    planned_minutes      = Column(Integer)
    coach_override       = Column(Boolean, default=False)
    recheckin_count      = Column(Integer, default=0)
    absence_reason       = Column(String(30))

    user    = relationship("User", back_populates="logs")
    workout = relationship("Workout")


class Workout(Base):
    __tablename__ = "workouts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    level           = Column(Integer, nullable=False)
    day             = Column(Integer, nullable=False)
    day_type        = Column(String(20), nullable=False)
    version         = Column(String(20), nullable=False)
    strength_format = Column(String(10))
    title           = Column(String(200), nullable=False)
    short_title     = Column(String(100))
    text            = Column(Text, nullable=False)
    micro_learning  = Column(Text)
    video_url       = Column(String(500))
    media_id        = Column(String(200))


class WeekPlan(Base):
    __tablename__ = "week_plans"

    id                     = Column(Integer, primary_key=True, autoincrement=True)
    user_id                = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    week_number            = Column(Integer)
    cycle_number           = Column(Integer, default=1)
    period                 = Column(String(30))
    period_week_number     = Column(Integer, default=1)
    start_date             = Column(Date)
    end_date               = Column(Date)
    weekly_target_minutes  = Column(Integer)
    is_recovery_week       = Column(Boolean, default=False)
    is_rollback_week       = Column(Boolean, default=False)
    actual_running_minutes = Column(Integer)
    completion_rate        = Column(Float)
    closed_at              = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="week_plans")
    days = relationship("DayPlan", back_populates="week_plan")


class DayPlan(Base):
    __tablename__ = "day_plans"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    week_plan_id     = Column(Integer, ForeignKey("week_plans.id"), nullable=False)
    day_of_week      = Column(Integer)
    day_type         = Column(String(20))
    run_subtype      = Column(String(30))
    planned_minutes  = Column(Integer)
    intensity        = Column(String(30))
    is_key           = Column(Boolean, default=False)
    is_key_completed = Column(Boolean)
    session_log_id   = Column(Integer)

    week_plan = relationship("WeekPlan", back_populates="days")


class Whitelist(Base):
    __tablename__ = "whitelist"

    telegram_id = Column(BigInteger, primary_key=True)
    added_by    = Column(BigInteger, nullable=False)
    note        = Column(String(500))
    created_at  = Column(DateTime(timezone=True))
