from sqlalchemy import (
    BigInteger, Boolean, Column, Date, Integer,
    String, Text, DateTime, ForeignKey
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

    logs = relationship("SessionLog", back_populates="user")


class SessionLog(Base):
    __tablename__ = "session_logs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    user_id              = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    date                 = Column(Date, nullable=False)
    day_index            = Column(Integer, nullable=False)   # calendar day 1–35
    wellbeing            = Column(Integer)                   # 1–5
    sleep_quality        = Column(Integer)                   # 1–3
    pain_level           = Column(Integer)                   # 1–3
    pain_increases       = Column(Boolean)
    stress_level         = Column(Integer)                   # 1–3
    assigned_workout_id  = Column(Integer, ForeignKey("workouts.id"))
    assigned_version     = Column(String(20))                # base/light/recovery/rest
    completion_status    = Column(String(20))                # done/partial/skipped
    effort_level         = Column(Integer)                   # 1–5
    completion_pain      = Column(Boolean)
    red_flag             = Column(Boolean, default=False)
    fatigue_reduction    = Column(Boolean, default=False)
    morning_sent         = Column(Boolean, default=False)
    evening_sent         = Column(Boolean, default=False)
    checkin_done         = Column(Boolean, default=False)
    checkin_at           = Column(DateTime(timezone=True))
    approval_pending     = Column(Boolean, default=False)
    created_at           = Column(DateTime(timezone=True))

    user    = relationship("User", back_populates="logs")
    workout = relationship("Workout")


class Workout(Base):
    __tablename__ = "workouts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    level           = Column(Integer, nullable=False)
    day             = Column(Integer, nullable=False)        # template day 1–28
    day_type        = Column(String(20), nullable=False)     # run/strength/recovery/rest
    version         = Column(String(20), nullable=False)     # base/light/recovery
    strength_format = Column(String(10))                     # gym/home/null
    title           = Column(String(200), nullable=False)
    short_title     = Column(String(100))
    text            = Column(Text, nullable=False)
    micro_learning  = Column(Text)
    video_url       = Column(String(500))
    media_id        = Column(String(200))                    # Telegram cached file ID


class Whitelist(Base):
    __tablename__ = "whitelist"

    telegram_id = Column(BigInteger, primary_key=True)
    added_by    = Column(BigInteger, nullable=False)
    note        = Column(String(500))
    created_at  = Column(DateTime(timezone=True))
