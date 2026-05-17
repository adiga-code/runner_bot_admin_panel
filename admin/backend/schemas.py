from pydantic import BaseModel
from typing import Optional, List
from datetime import date as Date, datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserListItem(BaseModel):
    telegram_id: int
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    level: Optional[int] = None
    status: Optional[str] = None
    program_start_date: Optional[Date] = None
    week_repeat_count: Optional[int] = None
    created_at: Optional[datetime] = None
    current_day: Optional[int] = None
    current_period: Optional[str] = None
    program_week_number: Optional[int] = None
    onboarding_complete: Optional[bool] = None
    injury_return_active: Optional[bool] = None
    city: Optional[str] = None
    q_goal: Optional[str] = None
    q_runs: Optional[str] = None
    q_frequency: Optional[str] = None
    q_volume: Optional[str] = None
    q_longest_run: Optional[str] = None
    q_break: Optional[str] = None
    q_break_duration: Optional[str] = None
    q_pain: Optional[str] = None
    q_injury_history: Optional[str] = None
    q_structure: Optional[str] = None
    q_distance: Optional[str] = None
    q_race_date: Optional[str] = None
    q_self_level: Optional[str] = None

    model_config = {"from_attributes": True}


class UserDetail(BaseModel):
    telegram_id: int
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[Date] = None
    country: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    timezone_offset: Optional[int] = None
    level: Optional[int] = None
    strength_format: Optional[str] = None
    program_start_date: Optional[Date] = None
    week_repeat_count: Optional[int] = None
    status: Optional[str] = None
    onboarding_complete: Optional[bool] = None
    created_at: Optional[datetime] = None
    q_goal: Optional[str] = None
    q_runs: Optional[str] = None
    q_frequency: Optional[str] = None
    q_volume: Optional[str] = None
    q_longest_run: Optional[str] = None
    q_structure: Optional[str] = None
    q_experience: Optional[str] = None
    q_break: Optional[str] = None
    q_break_duration: Optional[str] = None
    q_run_feel: Optional[str] = None
    q_pain: Optional[str] = None
    q_pain_location: Optional[str] = None
    q_pain_increases: Optional[str] = None
    q_injury_history: Optional[str] = None
    q_other_sports: Optional[str] = None
    q_strength_frequency: Optional[str] = None
    q_regularity: Optional[str] = None
    q_strength: Optional[str] = None
    q_self_level: Optional[str] = None
    q_distance: Optional[str] = None
    q_race_date: Optional[str] = None
    q_continuous_run_test: Optional[str] = None
    q_gadget: Optional[str] = None
    q_gadget_types: Optional[str] = None
    q_gadget_sharing: Optional[str] = None
    # Extra user fields
    role: Optional[str] = None
    is_active: Optional[bool] = None
    reminders_enabled: Optional[bool] = None
    morning_reminder_hour: Optional[int] = None
    evening_reminder_hour: Optional[int] = None
    extended_week5: Optional[bool] = None
    # New program state (new_logic branch)
    available_weekdays: Optional[str] = None
    weekly_target_minutes: Optional[int] = None
    peak_volume_minutes: Optional[int] = None
    last_successful_volume: Optional[int] = None
    current_period: Optional[str] = None
    period_start_date: Optional[Date] = None
    period_week_number: Optional[int] = None
    cycle_number: Optional[int] = None
    cycle_start_date: Optional[Date] = None
    program_week_number: Optional[int] = None
    growth_streak: Optional[int] = None
    weeks_since_recovery: Optional[int] = None
    red_flag_active: Optional[bool] = None
    red_flag_reason: Optional[str] = None
    red_flag_at: Optional[Date] = None
    has_goal_race: Optional[bool] = None
    entry_point: Optional[str] = None
    injury_return_active: Optional[bool] = None
    target_level: Optional[int] = None
    return_mode_started_at: Optional[Date] = None
    in_macrocycle_recovery: Optional[bool] = None
    macrocycle_recovery_week: Optional[int] = None
    macrocycle_peak_volume: Optional[int] = None
    l1_long_independent: Optional[bool] = None
    l1_no_pain_streak_weeks: Optional[int] = None
    l1_easy_reached_40min: Optional[bool] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: List[UserListItem]
    total: int
    page: int
    pages: int


class UpdateLevelRequest(BaseModel):
    level: int


class UpdateStartDateRequest(BaseModel):
    start_date: Date


class UpdateStatusRequest(BaseModel):
    status: str


class SetDayRequest(BaseModel):
    day: int


class WorkoutInfo(BaseModel):
    id: int
    level: Optional[int] = None
    day: Optional[int] = None
    day_type: Optional[str] = None
    version: Optional[str] = None
    strength_format: Optional[str] = None
    title: Optional[str] = None
    short_title: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionLogItem(BaseModel):
    id: int
    user_id: int
    date: Optional[Date] = None
    day_index: Optional[int] = None
    wellbeing: Optional[int] = None
    sleep_quality: Optional[int] = None
    pain_level: Optional[int] = None
    pain_increases: Optional[bool] = None
    stress_level: Optional[int] = None
    assigned_workout_id: Optional[int] = None
    assigned_version: Optional[str] = None
    completion_status: Optional[str] = None
    effort_level: Optional[int] = None
    completion_pain: Optional[bool] = None
    red_flag: Optional[bool] = None
    fatigue_reduction: Optional[bool] = None
    morning_sent: Optional[bool] = None
    evening_sent: Optional[bool] = None
    checkin_done: Optional[bool] = None
    approval_pending: Optional[bool] = None
    checkin_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    calendar_day: Optional[int] = None
    workout: Optional[WorkoutInfo] = None
    # New
    week_plan_id: Optional[int] = None
    day_plan_id: Optional[int] = None
    day_of_week: Optional[int] = None
    planned_minutes: Optional[int] = None
    coach_override: Optional[bool] = None
    recheckin_count: Optional[int] = None
    absence_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdateLogRequest(BaseModel):
    assigned_version: Optional[str] = None
    assigned_workout_id: Optional[int] = None


class UpdateCompletionRequest(BaseModel):
    completion_status: str


class WorkoutItem(BaseModel):
    id: int
    level: Optional[int] = None
    day: Optional[int] = None
    day_type: Optional[str] = None
    version: Optional[str] = None
    strength_format: Optional[str] = None
    title: Optional[str] = None
    short_title: Optional[str] = None
    text: Optional[str] = None
    micro_learning: Optional[str] = None
    video_url: Optional[str] = None
    media_id: Optional[str] = None

    model_config = {"from_attributes": True}


class UpdateWorkoutRequest(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    micro_learning: Optional[str] = None
    video_url: Optional[str] = None


class AnalyticsSummary(BaseModel):
    total_users: int
    active_users: int
    pending_users: int
    avg_completion_7d: float


class CompletionChartItem(BaseModel):
    date: str
    done: int
    partial: int
    skipped: int


class LevelAnalytics(BaseModel):
    level: int
    name: str
    total: int
    active: int
    avg_completion: float
    avg_day: float


class ScoreBreakdown(BaseModel):
    base: int
    frequency: int
    volume: int
    structure: int
    break_penalty: int
    pain_penalty: int
    total: int


class RecalcLevelResponse(BaseModel):
    level: int
    entry_point: str
    injury_return: bool
    has_goal_race: bool
    starting_volume_min: int
    initial_period: str
    hard_stop: Optional[str] = None
    score: Optional[int] = None
    score_breakdown: Optional[ScoreBreakdown] = None
