"""
Seed script: creates SQLite DB and populates with realistic mock data.
Run: python seed.py
"""
import asyncio
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./mock.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id             INTEGER PRIMARY KEY,
    full_name               TEXT,
    last_name               TEXT,
    first_name              TEXT,
    middle_name             TEXT,
    gender                  TEXT,
    birth_date              TEXT,
    country                 TEXT,
    city                    TEXT,
    district                TEXT,
    timezone_offset         INTEGER DEFAULT 3,
    level                   INTEGER,
    strength_format         TEXT,
    program_start_date      TEXT,
    week_repeat_count       INTEGER DEFAULT 0,
    morning_reminder_hour   INTEGER DEFAULT 8,
    evening_reminder_hour   INTEGER DEFAULT 20,
    reminders_enabled       INTEGER DEFAULT 1,
    extended_week5          INTEGER DEFAULT 0,
    is_active               INTEGER DEFAULT 1,
    status                  TEXT DEFAULT 'pending',
    onboarding_complete     INTEGER DEFAULT 0,
    role                    TEXT DEFAULT 'athlete',
    created_at              TEXT,
    q_goal                  TEXT,
    q_distance              TEXT,
    q_race_date             TEXT,
    q_runs                  TEXT,
    q_frequency             TEXT,
    q_volume                TEXT,
    q_longest_run           TEXT,
    q_structure             TEXT,
    q_experience            TEXT,
    q_break                 TEXT,
    q_break_duration        TEXT,
    q_run_feel              TEXT,
    q_pain                  TEXT,
    q_pain_location         TEXT,
    q_pain_increases        TEXT,
    q_injury_history        TEXT,
    q_other_sports          TEXT,
    q_strength_frequency    TEXT,
    q_regularity            TEXT,
    q_strength              TEXT,
    q_self_level            TEXT
);

CREATE TABLE IF NOT EXISTS workouts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    level           INTEGER NOT NULL,
    day             INTEGER NOT NULL,
    day_type        TEXT NOT NULL,
    version         TEXT NOT NULL,
    strength_format TEXT,
    title           TEXT NOT NULL,
    short_title     TEXT,
    text            TEXT NOT NULL,
    micro_learning  TEXT,
    video_url       TEXT,
    media_id        TEXT
);

CREATE TABLE IF NOT EXISTS session_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    date                TEXT NOT NULL,
    day_index           INTEGER NOT NULL,
    wellbeing           INTEGER,
    sleep_quality       INTEGER,
    pain_level          INTEGER,
    pain_increases      INTEGER,
    stress_level        INTEGER,
    assigned_workout_id INTEGER,
    assigned_version    TEXT,
    completion_status   TEXT,
    effort_level        INTEGER,
    completion_pain     INTEGER,
    red_flag            INTEGER DEFAULT 0,
    fatigue_reduction   INTEGER DEFAULT 0,
    morning_sent        INTEGER DEFAULT 0,
    evening_sent        INTEGER DEFAULT 0,
    checkin_done        INTEGER DEFAULT 0,
    checkin_at          TEXT,
    approval_pending    INTEGER DEFAULT 0,
    created_at          TEXT,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
    FOREIGN KEY (assigned_workout_id) REFERENCES workouts(id)
);

CREATE TABLE IF NOT EXISTS whitelist (
    telegram_id INTEGER PRIMARY KEY,
    added_by    INTEGER NOT NULL,
    note        TEXT,
    created_at  TEXT
);
"""

# 10 users with realistic data matching real bot schema
USERS = [
    # tid, fn, ln, mn, g, bd, country, city, dist, tz, lvl, sf,
    # start_date, wrc, status, oc, role, created_at,
    # goal, dist_q, race_date, runs, freq, vol, longest, structure,
    # exp, break_, break_dur, run_feel, pain, pain_loc, pain_inc,
    # injury, sports, str_freq, regularity, strength, self_level
    # indices: 0=tid,1=fn,2=ln,3=mn,4=g,5=bd,6=country,7=city,8=dist,9=tz,
    #   10=lvl,11=sf,12=start,13=wrc,14=status,15=oc,16=role,17=ca,
    #   18=goal,19=qdist,20=qrd,21=qr,22=qf,23=qv,24=ql,25=qs,
    #   26=qe,27=qb,28=qbd,29=qrf,30=qp,31=qpl,32=qpi,33=qih,
    #   34=qos,35=qsf,36=qreg,37=qstr,38=qsl
    (100001,"Алексей","Смирнов","Игоревич","m","1990-05-15",
     "Россия","Москва","Центральный",3,2,"gym",
     (date.today()-timedelta(days=14)).isoformat(),1,"active",1,"athlete",
     (datetime.now()-timedelta(days=30)).isoformat(),
     "improve","10km",None,"regular","2_3","10_25","10_15","yes",
     "1_3y","no","no","medium","little","knees","no","no","gym","sometimes","regularly","sometimes","medium"),

    (100002,"Мария","Петрова","Андреевна","f","1995-08-22",
     "Россия","Санкт-Петербург","Василеостровский",3,1,"home",
     (date.today()-timedelta(days=7)).isoformat(),0,"active",1,"athlete",
     (datetime.now()-timedelta(days=14)).isoformat(),
     "health",None,None,"irregular","0_1","to_10","to_5","no",
     "to_6m","no","no","hard","none","","no","no","none","no","sometimes","no","beginner"),

    (100003,"Дмитрий","Козлов","Сергеевич","m","1985-03-10",
     "Россия","Казань","Советский",3,3,"gym",
     (date.today()-timedelta(days=21)).isoformat(),2,"active",1,"athlete",
     (datetime.now()-timedelta(days=45)).isoformat(),
     "distance","21km","2026-10-01","regular","4plus","25_50","15plus","yes",
     "3plus","yes","3_6m","easy","little","achilles","not_sure","yes","gym,bike","regularly","regularly","regularly","advanced"),

    (100004,"Анна","Волкова",None,"f","1998-11-30",
     "Россия","Новосибирск",None,5,1,"home",
     (date.today()-timedelta(days=3)).isoformat(),0,"active",1,"athlete",
     (datetime.now()-timedelta(days=10)).isoformat(),
     "start_zero",None,None,"no","0_1","to_10","to_5","no",
     "beginner","no","no","hard","none","","no","no","none","no","sometimes","no","beginner"),

    (100005,"Игорь","Новиков","Васильевич","m","1982-07-04",
     "Россия","Екатеринбург","Кировский",5,4,"gym",
     (date.today()-timedelta(days=10)).isoformat(),1,"active",1,"athlete",
     (datetime.now()-timedelta(days=60)).isoformat(),
     "return",None,None,"regular","2_3","10_25","10_15","yes",
     "1_3y","yes","6plus","medium","yes","knees,shin","yes","yes","gym","regularly","regularly","regularly","medium"),

    (100006,"Светлана","Морозова","Олеговна","f","1993-02-18",
     "Россия","Ростов-на-Дону","Ленинский",3,2,"home",
     None,None,"pending",1,"athlete",
     (datetime.now()-timedelta(days=2)).isoformat(),
     "no_pain",None,None,"irregular","0_1","to_10","5_10","no",
     "6_12m","no","no","hard","yes","feet,back","yes","no","swim","sometimes","sometimes","sometimes","base"),

    (100007,"Павел","Федоров","Николаевич","m","1988-09-25",
     "Россия","Краснодар","Прикубанский",3,3,"gym",
     None,None,"pending",1,"athlete",
     (datetime.now()-timedelta(days=1)).isoformat(),
     "improve","42km","2027-04-01","regular","4plus","25_50","15plus","yes",
     "3plus","no","no","easy","none","","no","no","gym,bike,swim","regularly","regularly","regularly","advanced"),

    (100008,"Елена","Кузнецова","Дмитриевна","f","2000-04-12",
     "Россия","Уфа","Октябрьский",3,1,"home",
     (date.today()-timedelta(days=28)).isoformat(),1,"active",1,"athlete",
     (datetime.now()-timedelta(days=40)).isoformat(),
     "health",None,None,"irregular","2_3","to_10","5_10","no",
     "to_6m","no","no","medium","none","","no","no","none","no","sometimes","no","beginner"),

    (100009,"Сергей","Попов","Александрович","m","1979-12-01",
     "Казахстан","Алматы",None,5,4,"gym",
     (date.today()-timedelta(days=5)).isoformat(),0,"active",1,"athlete",
     (datetime.now()-timedelta(days=20)).isoformat(),
     "distance","10km",None,"regular","2_3","10_25","15plus","yes",
     "1_3y","yes","1_3m","medium","little","back","no","yes","gym","sometimes","regularly","sometimes","medium"),

    (100010,"Юлия","Лебедева","Романовна","f","1996-06-14",
     "Беларусь","Минск","Центральный",3,2,"home",
     None,None,"pending",0,"athlete",
     datetime.now().isoformat(),
     None,None,None,None,None,None,None,None,
     None,None,None,None,None,None,None,None,None,None,None,None,None),
]

WORKOUTS = [
    # (level, day, day_type, version, sf, title, short_title, text, micro_learning)
    (1,1,"run","base",None,
     "Лёгкий бег — начало пути","День 1 — бег",
     "Разминка 5 мин\nЛёгкий бег 15 мин (пульс 130-140)\nЗаминка 5 мин",
     "Первая тренировка задаёт тон всей программе. Темп должен быть таким, чтобы можно было разговаривать."),

    (1,2,"strength","base","gym",
     "Силовая — базовая (зал)","День 2 — сила зал",
     "Приседания 3×15\nОтжимания 3×12\nПланка 3×30 сек\nСкручивания 3×20",
     "Силовая работа укрепляет мышцы-стабилизаторы, снижая риск травм при беге."),

    (1,2,"strength","base","home",
     "Силовая — базовая (дома)","День 2 — сила дома",
     "Приседания 3×20\nОтжимания 3×15\nПланка 3×40 сек\nОбратные выпады 3×12",
     "Домашняя тренировка не уступает залу при правильной технике."),

    (1,3,"recovery","recovery",None,
     "Восстановление и мобилити","День 3 — восст.",
     "Лёгкая ходьба 20 мин\nРастяжка основных групп мышц 15 мин\nДыхательные упражнения 5 мин",
     "Восстановление — такая же часть тренировочного процесса, как и нагрузка."),

    (1,4,"run","base",None,
     "Интервальный бег","День 4 — интервалы",
     "Разминка 5 мин\n4 × (3 мин бег + 2 мин ходьба)\nЗаминка 5 мин",
     "Интервалы развивают аэробную базу быстрее, чем монотонный бег."),

    (1,5,"strength","base","gym",
     "Силовая — ноги (зал)","День 5 — ноги зал",
     "Жим ногами 3×15\nРазгибания 3×15\nСгибания 3×15\nИкры 4×20",
     "Сильные ноги — основа беговой экономичности."),

    (1,5,"strength","base","home",
     "Силовая — ноги (дома)","День 5 — ноги дома",
     "Приседания сумо 3×20\nВыпады ходьба 3×16\nПодъём на носки 4×25\nМостик 3×20",
     "Эти упражнения прицельно работают на беговые мышцы."),

    (1,6,"run","base",None,
     "Длинный бег — 30 мин","День 6 — длинный",
     "Разминка 5 мин\nЛёгкий бег 30 мин (пульс 125-135)\nЗаминка 5 мин",
     "Длинный медленный бег строит аэробную базу."),

    (1,7,"rest","recovery",None,
     "День отдыха","День 7 — отдых",
     "Полный отдых или лёгкая прогулка 30 мин в комфортном темпе.",
     "Суперкомпенсация происходит во время отдыха."),

    (2,1,"run","base",None,
     "Возвращение — первый бег","Бег 1",
     "Разминка 5 мин\n5×(4 мин бег + 1 мин ходьба)\nЗаминка 5 мин",
     "После перерыва тело помнит нагрузку, но нуждается в адаптации."),

    (2,2,"strength","base","gym",
     "Возвращение — сила (зал)","Сила 1 зал",
     "Приседания со штангой 4×12 (60%)\nЖим лёжа 4×10\nТяга в наклоне 4×12\nПресс 3×20",
     "Возвращайтесь к весам постепенно — начните с 60% от рабочего."),

    (2,4,"run","base",None,
     "Темповый бег — 20 мин","Темп 1",
     "Разминка 10 мин\n20 мин темповый бег (пульс 150-160)\nЗаминка 10 мин",
     "Темповый бег повышает лактатный порог."),

    (2,6,"run","base",None,
     "Длинный бег — 45 мин","Длинный 1",
     "Разминка 5 мин\nЛёгкий бег 45 мин (пульс 120-135)\nЗаминка 5 мин",
     "Цель длинного бега — время на ногах, а не скорость."),

    (3,1,"run","base",None,
     "Базовый бег 40 мин","Бег 40",
     "Разминка 10 мин\n40 мин аэробный бег (пульс 135-145)\nЗаминка 10 мин",
     "80% всего объёма должно проходить в аэробной зоне."),

    (3,3,"run","base",None,
     "Интервалы 6×800м","Интервалы 800",
     "Разминка 15 мин\n6 × 800м (темп 5к+15с) / восст. 90 сек\nЗаминка 15 мин",
     "800-метровые интервалы развивают МПК — максимальное потребление кислорода."),

    (3,6,"run","base",None,
     "Длинный бег 60-70 мин","Длинный 60",
     "Разминка 10 мин\n60-70 мин лёгкий бег (пульс 125-138)\nЗаминка 10 мин",
     "На длинном беге практикуй питание и гидратацию."),

    (4,1,"run","base",None,
     "Стабильный темп 50 мин","Темп 50",
     "Разминка 10 мин\n50 мин марафонский темп (пульс 145-155)\nЗаминка 10 мин",
     "Марафонский темп — твоя ключевая тренировочная зона."),

    (4,4,"run","base",None,
     "Прогрессивный бег 45 мин","Прогрессив",
     "Разминка 10 мин\n15 мин легко → 15 мин средне → 15 мин быстро\nЗаминка 10 мин",
     "Прогрессивные пробежки тренируют терпение и управление темпом."),

    # Light versions
    (1,4,"run","light",None,
     "Лёгкие интервалы","Интервалы лайт",
     "Разминка 5 мин\n3 × (2 мин бег + 3 мин ходьба)\nЗаминка 5 мин",
     "Лёгкая версия для дней, когда самочувствие ниже обычного."),

    (2,1,"run","light",None,
     "Короткий восст. бег","Бег лайт",
     "Лёгкая ходьба 10 мин\nТрусца 15 мин (очень легко)\nРастяжка 10 мин",
     "Если устали — лёгкая тренировка лучше, чем пропуск."),

    (3,1,"run","light",None,
     "Лёгкий бег 25 мин","Бег 25 лайт",
     "Разминка 5 мин\n25 мин лёгкий бег (на 1-2 зоны ниже обычного)\nЗаминка 5 мин",
     "Восстановительный бег снижает накопленную усталость."),
]


def make_log(user_id, day_offset, day_index, workout_id, version,
             wellbeing, sleep, pain, stress, status, effort,
             red_flag=False, checkin=True, fatigue=False):
    d = (date.today() - timedelta(days=day_offset)).isoformat()
    checkin_at = (datetime.now() - timedelta(days=day_offset, hours=8)).isoformat() if checkin else None
    return {
        "user_id": user_id, "date": d, "day_index": day_index,
        "wellbeing": wellbeing, "sleep_quality": sleep,
        "pain_level": pain, "pain_increases": 0, "stress_level": stress,
        "assigned_workout_id": workout_id, "assigned_version": version,
        "completion_status": status, "effort_level": effort,
        "completion_pain": 0, "red_flag": 1 if red_flag else 0,
        "fatigue_reduction": 1 if fatigue else 0,
        "morning_sent": 1, "evening_sent": 1 if checkin else 0,
        "checkin_done": 1 if checkin else 0,
        "checkin_at": checkin_at,
        "approval_pending": 0,
        "created_at": (datetime.now() - timedelta(days=day_offset)).isoformat(),
    }


async def seed():
    async with engine.begin() as conn:
        for stmt in CREATE_TABLES.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await conn.execute(text(stmt))

    async with AsyncSession() as session:
        await session.execute(text("DELETE FROM session_logs"))
        await session.execute(text("DELETE FROM workouts"))
        await session.execute(text("DELETE FROM users"))
        await session.execute(text("DELETE FROM whitelist"))
        await session.commit()

        # --- Insert workouts ---
        workout_ids = {}
        for i, w in enumerate(WORKOUTS):
            r = await session.execute(text("""
                INSERT INTO workouts
                (level,day,day_type,version,strength_format,title,short_title,text,micro_learning)
                VALUES (:lv,:day,:dt,:ver,:sf,:title,:short,:text,:ml)
            """), {
                "lv": w[0], "day": w[1], "dt": w[2], "ver": w[3],
                "sf": w[4], "title": w[5], "short": w[6],
                "text": w[7], "ml": w[8],
            })
            workout_ids[i] = r.lastrowid
        await session.commit()

        # --- Insert users ---
        for u in USERS:
            full = f"{u[2]} {u[1]}" if u[2] and u[1] else (u[1] or u[2] or "")
            await session.execute(text("""
                INSERT INTO users
                (telegram_id,first_name,last_name,full_name,middle_name,gender,birth_date,
                 country,city,district,timezone_offset,level,strength_format,
                 program_start_date,week_repeat_count,status,onboarding_complete,
                 role,created_at,
                 q_goal,q_distance,q_race_date,q_runs,q_frequency,q_volume,
                 q_longest_run,q_structure,q_experience,q_break,q_break_duration,
                 q_run_feel,q_pain,q_pain_location,q_pain_increases,q_injury_history,
                 q_other_sports,q_strength_frequency,q_regularity,q_strength,q_self_level)
                VALUES
                (:tid,:fn,:ln,:full,:mn,:g,:bd,
                 :country,:city,:dist,:tz,:lvl,:sf,
                 :start,:wrc,:status,:oc,
                 :role,:ca,
                 :qg,:qdist,:qrd,:qr,:qf,:qv,
                 :ql,:qs,:qe,:qb,:qbd,
                 :qrf,:qp,:qpl,:qpi,:qih,
                 :qos,:qsf,:qreg,:qstr,:qsl)
            """), {
                "tid": u[0], "fn": u[1], "ln": u[2], "full": full,
                "mn": u[3], "g": u[4], "bd": u[5],
                "country": u[6], "city": u[7], "dist": u[8], "tz": u[9],
                "lvl": u[10], "sf": u[11], "start": u[12], "wrc": u[13],
                "status": u[14], "oc": u[15], "role": u[16], "ca": u[17],
                "qg": u[18], "qdist": u[19], "qrd": u[20],
                "qr": u[21], "qf": u[22], "qv": u[23],
                "ql": u[24], "qs": u[25], "qe": u[26],
                "qb": u[27], "qbd": u[28], "qrf": u[29],
                "qp": u[30], "qpl": u[31], "qpi": u[32],
                "qih": u[33], "qos": u[34], "qsf": u[35],
                "qreg": u[36], "qstr": u[37], "qsl": u[38],
            })
        await session.commit()

        # --- Whitelist (admin + 2 test users) ---
        for wl in [
            (999999, 999999, "admin"),
            (100001, 999999, "Смирнов"),
            (100003, 999999, "Козлов"),
        ]:
            await session.execute(text("""
                INSERT OR IGNORE INTO whitelist (telegram_id, added_by, note, created_at)
                VALUES (:tid,:by,:note,:ca)
            """), {"tid": wl[0], "by": wl[1], "note": wl[2],
                   "ca": datetime.now().isoformat()})
        await session.commit()

        # --- Session logs for user 100001 (14 days, level 2) ---
        # wellbeing is 1-5 in real schema
        logs_1 = [
            make_log(100001,13,1,  workout_ids[9],  "base",     4,3,1,1,"done",    3),
            make_log(100001,12,2,  workout_ids[1],  "base",     4,3,1,1,"done",    3),
            make_log(100001,11,3,  workout_ids[3],  "recovery", 5,3,1,1,"done",    2),
            make_log(100001,10,4,  workout_ids[4],  "base",     4,2,1,2,"done",    4),
            make_log(100001, 9,5,  workout_ids[5],  "base",     2,2,2,2,"partial", 3, red_flag=True),
            make_log(100001, 8,6,  workout_ids[7],  "base",     4,3,1,1,"done",    4),
            make_log(100001, 7,7,  workout_ids[8],  "recovery", 5,3,1,1,"done",    1),
            make_log(100001, 6,8,  workout_ids[9],  "base",     4,3,1,1,"done",    3),
            make_log(100001, 5,9,  workout_ids[18], "light",    3,2,2,2,"done",    2, fatigue=True),
            make_log(100001, 4,10, workout_ids[3],  "recovery", 5,3,1,1,"done",    2),
            make_log(100001, 3,11, workout_ids[4],  "base",     4,3,1,1,"done",    4),
            make_log(100001, 2,12, workout_ids[5],  "base",     5,3,1,1,"done",    3),
            make_log(100001, 1,13, workout_ids[7],  "base",     3,3,1,2,"skipped", None, checkin=False),
            make_log(100001, 0,14, workout_ids[8],  "recovery", None,None,None,None,None,None, checkin=False),
        ]

        # --- Session logs for user 100002 (7 days, level 1) ---
        logs_2 = [
            make_log(100002,6,1, workout_ids[0],  "base",     3,2,1,2,"done",    2),
            make_log(100002,5,2, workout_ids[2],  "base",     3,3,1,1,"done",    3),
            make_log(100002,4,3, workout_ids[3],  "recovery", 4,3,1,1,"done",    1),
            make_log(100002,3,4, workout_ids[18], "light",    2,2,1,2,"partial", 2, red_flag=True),
            make_log(100002,2,5, workout_ids[2],  "base",     3,3,1,1,"done",    3),
            make_log(100002,1,6, workout_ids[7],  "base",     4,3,1,1,"done",    3),
            make_log(100002,0,7, workout_ids[8],  "recovery", None,None,None,None,None,None, checkin=False),
        ]

        # --- Session logs for user 100003 (21 days, level 3) ---
        logs_3 = [
            make_log(100003,20,1,  workout_ids[13],"base",  5,3,1,1,"done",  3),
            make_log(100003,19,2,  workout_ids[1], "base",  5,3,1,1,"done",  4),
            make_log(100003,18,3,  workout_ids[3], "recovery",5,3,1,1,"done",1),
            make_log(100003,17,4,  workout_ids[14],"base",  4,3,1,1,"done",  4),
            make_log(100003,16,5,  workout_ids[1], "base",  4,2,2,1,"done",  3),
            make_log(100003,15,6,  workout_ids[15],"base",  5,3,1,1,"done",  4),
            make_log(100003,14,7,  workout_ids[8], "recovery",5,3,1,1,"done",1),
            make_log(100003,13,8,  workout_ids[13],"base",  4,3,1,1,"done",  3),
            make_log(100003,12,9,  workout_ids[9], "base",  2,2,2,2,"partial",3, red_flag=True, fatigue=True),
            make_log(100003,11,10, workout_ids[3], "recovery",4,3,1,1,"done",2),
            make_log(100003,10,11, workout_ids[14],"base",  5,3,1,1,"done",  4),
            make_log(100003, 9,12, workout_ids[1], "base",  5,3,1,1,"done",  4),
            make_log(100003, 8,13, workout_ids[3], "recovery",4,3,1,1,"done",2),
            make_log(100003, 7,14, workout_ids[15],"base",  5,3,1,1,"done",  4),
            make_log(100003, 6,15, workout_ids[20],"light", 3,2,2,2,"done",  2),
            make_log(100003, 5,16, workout_ids[15],"base",  5,3,1,1,"done",  4),
            make_log(100003, 4,17, workout_ids[8], "recovery",5,3,1,1,"done",1),
            make_log(100003, 3,18, workout_ids[14],"base",  4,3,1,1,"done",  3),
            make_log(100003, 2,19, workout_ids[13],"base",  5,3,1,1,"done",  4),
            make_log(100003, 1,20, workout_ids[3], "recovery",4,2,2,1,"done",2),
            make_log(100003, 0,21, workout_ids[14],"base",  None,None,None,None,None,None, checkin=False),
        ]

        # --- Session logs for user 100008 (completed 28 days, level 1) ---
        statuses = ["done"]*22 + ["skipped","done","done","partial","done","done"]
        wellbeings = [3,4,4,3,3,5,5,4,3,3,4,5,4,4,3,3,5,4,4,3,3,2,3,4,5,4,4,3]
        logs_8 = [
            make_log(100008, 27-i, i+1,
                     workout_ids[i % len(WORKOUTS)],
                     "base", wellbeings[i], 3, 1, 1,
                     statuses[i], 3 if statuses[i]!="skipped" else None)
            for i in range(28)
        ]

        all_logs = logs_1 + logs_2 + logs_3 + logs_8

        for log in all_logs:
            await session.execute(text("""
                INSERT INTO session_logs
                (user_id,date,day_index,wellbeing,sleep_quality,pain_level,pain_increases,
                 stress_level,assigned_workout_id,assigned_version,completion_status,
                 effort_level,completion_pain,red_flag,fatigue_reduction,morning_sent,
                 evening_sent,checkin_done,checkin_at,approval_pending,created_at)
                VALUES
                (:user_id,:date,:day_index,:wellbeing,:sleep_quality,:pain_level,:pain_increases,
                 :stress_level,:assigned_workout_id,:assigned_version,:completion_status,
                 :effort_level,:completion_pain,:red_flag,:fatigue_reduction,:morning_sent,
                 :evening_sent,:checkin_done,:checkin_at,:approval_pending,:created_at)
            """), log)
        await session.commit()

    print("Seed complete!")
    print(f"   Users:    {len(USERS)}")
    print(f"   Workouts: {len(WORKOUTS)}")
    print(f"   Logs:     {len(all_logs)}")
    print(f"   Whitelist: 3")

if __name__ == "__main__":
    asyncio.run(seed())
