from sqlalchemy import (
    BigInteger, Boolean, Column, Date, Float, Integer,
    String, Text, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from dependencies import Base


class User(Base):
    __tablename__ = "users"

    telegram_id             = Column(BigInteger, primary_key=True)
    full_name               = Column(String(200))
    last_name               = Column(String(100))
    first_name              = Column(String(100))
    middle_name             = Column(String(100))
    gender                  = Column(String(10))
    birth_date              = Column(Date)
    country                 = Column(String(100))
    city                    = Column(String(100))
    district                = Column(String(100))
    timezone_offset         = Column(Integer, default=3)
    level                   = Column(Integer)
    strength_format         = Column(String(10))
    program_start_date      = Column(Date)
    week_repeat_count       = Column(Integer, default=0)
    morning_reminder_hour   = Column(Integer, default=8)
    evening_reminder_hour   = Column(Integer, default=20)
    reminders_enabled       = Column(Boolean, default=True)
    extended_week5          = Column(Boolean, default=False)
    is_active               = Column(Boolean, default=True)
    status                  = Column(String(20), default="pending")
    onboarding_complete     = Column(Boolean, default=False)
    role                    = Column(String(20), default="athlete")
    created_at              = Column(DateTime(timezone=True))

    # Onboarding answers
    q_goal                  = Column(String(50))
    q_distance              = Column(String(20))
    q_race_date             = Column(String(50))
    q_runs                  = Column(String(20))
    q_frequency             = Column(String(20))
    q_volume                = Column(String(20))
    q_longest_run           = Column(String(20))
    q_structure             = Column(String(10))
    q_experience            = Column(String(20))
    q_break                 = Column(String(20))
    q_break_duration        = Column(String(20))
    q_run_feel              = Column(String(20))
    q_pain                  = Column(String(20))
    q_pain_location         = Column(String(200))
    q_pain_increases        = Column(String(20))
    q_injury_history        = Column(String(10))
    q_other_sports          = Column(String(200))
    q_strength_frequency    = Column(String(20))
    q_regularity            = Column(String(20))
    q_strength              = Column(String(20))
    q_self_level            = Column(String(20))
    q_continuous_run_test   = Column(String(10))   # yes/no/unsure (new v2)
    q_gadget                = Column(String(10))    # yes / no
    q_gadget_types          = Column(String(200))   # whoop,garmin,...
    q_gadget_sharing        = Column(String(10))    # yes / no / later

    # New: доступные дни и объём
    available_weekdays      = Column(String(20))   # "1,3,5"
    weekly_target_minutes   = Column(Integer)
    peak_volume_minutes     = Column(Integer)
    last_successful_volume  = Column(Integer)

    # Referral
    referral_code           = Column(String(50))

    # New: период и цикл
    current_period          = Column(String(30))
    period_start_date       = Column(Date)
    period_week_number      = Column(Integer, default=1)
    cycle_number            = Column(Integer, default=1)
    cycle_start_date        = Column(Date)
    program_week_number     = Column(Integer, default=1)

    # New: счётчики прогрессии
    growth_streak           = Column(Integer, default=0)
    weeks_since_recovery    = Column(Integer, default=0)

    # New: red flag
    red_flag_active         = Column(Boolean, default=False)
    red_flag_reason         = Column(String(100))
    red_flag_at             = Column(Date)

    # New: точка входа и цель
    has_goal_race           = Column(Boolean, default=False)
    entry_point             = Column(String(20))   # base_in / base

    # New: return-mode
    injury_return_active    = Column(Boolean, default=False)
    target_level            = Column(Integer)
    return_mode_started_at  = Column(Date)

    # New: macrocycle recovery
    in_macrocycle_recovery  = Column(Boolean, default=False)
    macrocycle_recovery_week = Column(Integer, default=0)
    macrocycle_peak_volume  = Column(Integer)

    # New: L1 long stage
    l1_long_independent     = Column(Boolean, default=False)
    l1_no_pain_streak_weeks = Column(Integer, default=0)
    l1_easy_reached_40min   = Column(Boolean, default=False)

    logs       = relationship("SessionLog", back_populates="user")
    week_plans = relationship("WeekPlan", back_populates="user")


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    level           = Column(Integer, nullable=False)
    day_type        = Column(String(20), nullable=False)
    run_subtype     = Column(String(30))
    version         = Column(String(20), nullable=False)
    intensity_kind  = Column(String(30))
    period          = Column(String(30))
    strength_format = Column(String(10))
    title           = Column(String(200), nullable=False)
    short_title     = Column(String(100))
    text            = Column(Text, nullable=False)
    micro_learning  = Column(Text)
    video_url       = Column(String(500))
    media_id        = Column(String(200))


class WeekPlan(Base):
    __tablename__ = "week_plans"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    user_id                 = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    week_number             = Column(Integer)
    cycle_number            = Column(Integer, default=1)
    period                  = Column(String(30))
    period_week_number      = Column(Integer, default=1)
    start_date              = Column(Date)
    end_date                = Column(Date)
    weekly_target_minutes   = Column(Integer)
    is_recovery_week        = Column(Boolean, default=False)
    is_rollback_week        = Column(Boolean, default=False)
    actual_running_minutes  = Column(Integer)
    completion_rate         = Column(Float)
    keys_completed          = Column(Boolean)
    growth_eligible         = Column(Boolean)
    no_growth_reason        = Column(String(100))
    closed_at               = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="week_plans")
    days = relationship("DayPlan", back_populates="week_plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_week_plans_user_start", "user_id", "start_date"),
    )


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
    session_log_id   = Column(Integer, ForeignKey("session_logs.id"))

    week_plan = relationship("WeekPlan", back_populates="days")

    __table_args__ = (
        UniqueConstraint("week_plan_id", "day_of_week", name="uq_day_plan_week_day"),
    )


class SessionLog(Base):
    __tablename__ = "session_logs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    user_id              = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    date                 = Column(Date, nullable=False)
    day_index            = Column(Integer, default=0)

    # New: связь с новыми планами
    week_plan_id         = Column(Integer, ForeignKey("week_plans.id"))
    day_plan_id          = Column(Integer, ForeignKey("day_plans.id"))
    day_of_week          = Column(Integer)
    planned_minutes      = Column(Integer)

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

    # New: coach override
    coach_override               = Column(Boolean, default=False)
    override_version             = Column(String(20))
    override_workout_template_id = Column(Integer, ForeignKey("workout_templates.id"))
    override_text                = Column(Text)
    override_minutes             = Column(Integer)
    approved_by_admin_id         = Column(BigInteger)
    approved_at                  = Column(DateTime(timezone=True))

    # New: absence-flow
    absence_reason               = Column(String(30))
    absence_reason_text          = Column(Text)
    absence_responded_at         = Column(DateTime(timezone=True))

    # New: re-checkin tracking
    recheckin_count              = Column(Integer, default=0)
    last_checkin_at              = Column(DateTime(timezone=True))

    red_flag             = Column(Boolean, default=False)
    fatigue_reduction    = Column(Boolean, default=False)
    morning_sent         = Column(Boolean, default=False)
    evening_sent         = Column(Boolean, default=False)
    checkin_done         = Column(Boolean, default=False)
    approval_pending     = Column(Boolean, default=False)
    checkin_at           = Column(DateTime(timezone=True))
    created_at           = Column(DateTime(timezone=True))

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


class Whitelist(Base):
    __tablename__ = "whitelist"

    telegram_id = Column(BigInteger, primary_key=True)
    added_by    = Column(BigInteger, nullable=False)
    note        = Column(String(500))
    created_at  = Column(DateTime(timezone=True))
