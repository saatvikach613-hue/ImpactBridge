"""
ImpactBridge — Seed Data Script
================================
Based on direct field observations at U&I Visakhapatnam (2023–2024):
- 3 chapters in Visakhapatnam, ~200 kids city-wide
- ~50 volunteers across all chapters
- Sessions every Sunday
- 70% sheet completion rate (coordinator was persistent)
- ~30% volunteer no-show rate on any given Sunday
- 15 minutes average sheet fill time (replaced by 30-sec logger)
- Fundraiser ran close to target but with no live visibility

Run: python scripts/seed.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import (
    Base, Chapter, User, Kid, VolunteerKidAssignment,
    SessionEvent, SessionRsvp, SessionLog, ProgressLog,
    FundDrive, WishlistItem, Donation,
    UserRole, SessionRating, WishlistStatus, RsvpStatus
)
from passlib.context import CryptContext
from datetime import date, timedelta, datetime
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────
# CONFIG — mirrors real U&I Vizag numbers
# ─────────────────────────────────────────────

SEED_CONFIG = {
    "chapters": [
        {"name": "Visakhapatnam - Madhavadhara",  "city": "Visakhapatnam"},
        {"name": "Visakhapatnam - Gajuwaka",      "city": "Visakhapatnam"},
        {"name": "Visakhapatnam - MVP Colony",    "city": "Visakhapatnam"},
    ],
    "kids_per_chapter":       [68, 72, 60],   # total ~200
    "volunteers_per_chapter": [17, 18, 15],   # total ~50
    "kids_per_volunteer":     5,              # each volunteer teaches 4-5 kids
    "session_weeks":          44,             # Sept 2023 – Aug 2024
    "no_show_rate":           0.30,           # 3-4 out of 12 per Sunday
    "log_completion_rate":    0.70,           # 7/10 sessions logged
    "fund_drive_goal":        10000.0,        # ₹ per chapter
    "fund_drive_raised_pct":  0.87,           # close to target, rarely short
}

# Kid names — realistic Indian names
KID_NAMES = [
    "Arjun", "Priya", "Ravi", "Sneha", "Kiran", "Ananya", "Rohit", "Divya",
    "Sai", "Meera", "Vikram", "Pooja", "Aditya", "Kavya", "Rahul", "Shreya",
    "Suresh", "Deepika", "Harish", "Lakshmi", "Manoj", "Sunita", "Prasad",
    "Gayatri", "Naresh", "Radha", "Sunil", "Padma", "Ganesh", "Uma",
    "Venkat", "Bhavana", "Charan", "Swathi", "Dinesh", "Yamini", "Eshan",
    "Revathi", "Gopal", "Sindhu", "Hemant", "Tanvi", "Ishaan", "Pavithra",
    "Jai", "Keerthi", "Lokesh", "Manasa", "Naveen", "Ojaswi", "Pavan",
    "Qureshi", "Ramya", "Srinivas", "Teja", "Usha", "Vinay", "Wahida",
    "Xavier", "Yashoda", "Zara", "Abhi", "Bhanu", "Chandu", "Daksha",
    "Eshwar", "Falguni", "Girish", "Hema", "Indira", "Jyothi"
]

VOLUNTEER_NAMES = [
    "Saatvika Chokkapu", "Meera Reddy", "Vikram Naidu", "Ananya Sharma",
    "Rohit Varma", "Deepika Rao", "Suresh Babu", "Kavitha Pillai",
    "Aditya Kumar", "Priyanka Iyer", "Harish Nair", "Sunitha Devi",
    "Manoj Teja", "Bhavana Goud", "Charan Sai", "Swathi Lakshmi",
    "Dinesh Raju", "Yamini Prasad", "Eshan Murthy", "Revathi Anjali",
    "Gopal Krishna", "Sindhu Rani", "Naveen Chandra", "Padmavathi S",
    "Venkat Reddy", "Gayatri Devi", "Lokesh Babu", "Manasa Kumari",
    "Prasad Varma", "Tanvi Shastri", "Sunil Sharma", "Pooja Nair",
    "Rahul Goud", "Keerthi Sai", "Hemant Kumar", "Pavithra Rao",
    "Jai Prakash", "Ramya Devi", "Srinivas Rao", "Usha Rani",
    "Pavan Kumar", "Ojaswi Reddy", "Vinay Babu", "Bhanu Priya",
    "Girish Naidu", "Hema Latha", "Indira Devi", "Jyothi Kumari",
    "Abhi Ram", "Daksha Rao"
]

LEARNING_STYLES = ["visual", "hands-on", "storytelling", "music", "movement", "repetition"]
INTERESTS = [
    "drawing, art", "cricket, sports", "dancing", "singing",
    "stories, reading", "puzzles, games", "cooking", "animals",
    "movies, cartoons", "nature, outdoors"
]
UNLOCK_NOTES = [
    "Responds well to drawing activities — bring sketch work to sessions",
    "Loves cricket analogies — use sports examples for math",
    "Engages through storytelling — frame lessons as stories",
    "Sings while learning — use rhymes and songs for memory",
    "Needs movement breaks every 10 minutes — short bursts work better",
    "Visual learner — diagrams and colours help retention",
    "Competitive — works harder with gentle challenges",
    "Shy at first but opens up with one-on-one attention",
    "Responds to praise immediately — celebrate small wins",
    None  # some kids don't have unlock notes yet
]

WISHLIST_ITEMS = [
    ("Sketchbook + colour pencils", 180),
    ("English workbook set (Ch.4–8)", 240),
    ("Math activity kit", 320),
    ("Story books (set of 5)", 450),
    ("Geometry box + ruler set", 120),
    ("Hindi alphabet flashcards", 90),
    ("Counting blocks set", 280),
    ("Phonics reading cards", 160),
    ("Drawing compass + protractor", 85),
    ("Science activity book", 350),
]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_chapters(db: Session) -> list[Chapter]:
    print("Creating chapters...")
    chapters = []
    for c in SEED_CONFIG["chapters"]:
        chapter = Chapter(name=c["name"], city=c["city"])
        db.add(chapter)
        chapters.append(chapter)
    db.commit()
    [db.refresh(c) for c in chapters]
    print(f"  Created {len(chapters)} chapters")
    return chapters


def create_coordinators(db: Session, chapters: list[Chapter]) -> list[User]:
    print("Creating coordinators...")
    coordinators = []
    # 1 coordinator + 1 VP per chapter (the president/VP/manager structure you described)
    roles_titles = ["Chapter President", "Vice President", "Chapter Manager"]
    for i, chapter in enumerate(chapters):
        for j in range(2):
            coord = User(
                full_name=f"{roles_titles[j % 3]} - {chapter.city}",
                email=f"coord_{i}_{j}@impactbridge.org",
                hashed_password=hash_password("coord123"),
                role=UserRole.coordinator,
                chapter_id=chapter.id,
                joined_date=date(2023, 6, 1),
            )
            db.add(coord)
            coordinators.append(coord)
    db.commit()
    [db.refresh(c) for c in coordinators]
    print(f"  Created {len(coordinators)} coordinators")
    return coordinators


def create_volunteers(db: Session, chapters: list[Chapter]) -> list[User]:
    print("Creating volunteers...")
    volunteers = []
    name_idx = 0
    for i, chapter in enumerate(chapters):
        count = SEED_CONFIG["volunteers_per_chapter"][i]
        for _ in range(count):
            name = VOLUNTEER_NAMES[name_idx % len(VOLUNTEER_NAMES)]
            vol = User(
                full_name=name,
                email=f"vol_{name_idx}@impactbridge.org",
                hashed_password=hash_password("vol123"),
                role=UserRole.volunteer,
                chapter_id=chapter.id,
                joined_date=date(2023, 9, 1) + timedelta(days=random.randint(0, 60)),
                phone=f"+91 9{random.randint(100000000, 999999999)}",
            )
            db.add(vol)
            volunteers.append(vol)
            name_idx += 1
    db.commit()
    [db.refresh(v) for v in volunteers]
    print(f"  Created {len(volunteers)} volunteers")
    return volunteers


def create_kids(db: Session, chapters: list[Chapter]) -> list[Kid]:
    print("Creating kids...")
    kids = []
    name_idx = 0
    for i, chapter in enumerate(chapters):
        count = SEED_CONFIG["kids_per_chapter"][i]
        for _ in range(count):
            name = KID_NAMES[name_idx % len(KID_NAMES)]
            # Realistic chapter distribution — kids at different levels
            # Based on typical NGO literacy data (ASER India benchmarks)
            math_ch = random.choices(
                range(1, 10),
                weights=[5, 10, 15, 20, 18, 14, 10, 5, 3]
            )[0]
            eng_ch = random.choices(
                range(1, 10),
                weights=[8, 12, 18, 20, 16, 12, 8, 4, 2]
            )[0]
            kid = Kid(
                name=name,
                age=random.randint(7, 11),
                chapter_id=chapter.id,
                math_chapter=math_ch,
                english_chapter=eng_ch,
                learning_style=random.choice(LEARNING_STYLES),
                interests=random.choice(INTERESTS),
                unlock_note=random.choice(UNLOCK_NOTES),
                enrolled_date=date(2023, 9, 1) + timedelta(days=random.randint(0, 30)),
            )
            db.add(kid)
            kids.append(kid)
            name_idx += 1
    db.commit()
    [db.refresh(k) for k in kids]
    print(f"  Created {len(kids)} kids across 3 chapters")
    return kids


def create_assignments(
    db: Session,
    volunteers: list[User],
    kids: list[Kid],
    chapters: list[Chapter]
) -> None:
    print("Creating volunteer-kid assignments (4-5 kids per volunteer)...")
    assignments_created = 0
    for chapter in chapters:
        chapter_vols = [v for v in volunteers if v.chapter_id == chapter.id]
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]
        random.shuffle(chapter_kids)

        kid_idx = 0
        for vol in chapter_vols:
            n_kids = SEED_CONFIG["kids_per_volunteer"]
            assigned = chapter_kids[kid_idx: kid_idx + n_kids]
            for kid in assigned:
                db.add(VolunteerKidAssignment(
                    volunteer_id=vol.id,
                    kid_id=kid.id,
                    assigned_date=date(2023, 9, 3),
                ))
                assignments_created += 1
            kid_idx += n_kids

    db.commit()
    print(f"  Created {assignments_created} assignments")


def create_sessions_and_logs(
    db: Session,
    chapters: list[Chapter],
    volunteers: list[User],
    kids: list[Kid]
) -> None:
    print("Creating 44 weeks of Sunday sessions with logs...")

    start_date = date(2023, 9, 3)  # first Sunday
    total_logs = 0
    total_rsvps = 0

    for chapter in chapters:
        chapter_vols = [v for v in volunteers if v.chapter_id == chapter.id]
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]

        # Get assignments for this chapter
        assignments = {}
        for vol in chapter_vols:
            assigned_kids = [
                k for k in chapter_kids
                if any(
                    a.volunteer_id == vol.id and a.kid_id == k.id
                    for a in db.query(VolunteerKidAssignment)
                       .filter_by(volunteer_id=vol.id).all()
                )
            ]
            assignments[vol.id] = assigned_kids

        for week in range(SEED_CONFIG["session_weeks"]):
            session_date = start_date + timedelta(weeks=week)

            event = SessionEvent(
                chapter_id=chapter.id,
                session_date=session_date,
            )
            db.add(event)
            db.flush()

            for vol in chapter_vols:
                # RSVP — 70% confirmed, 30% no-show (your observation)
                showed_up = random.random() > SEED_CONFIG["no_show_rate"]
                rsvp_status = RsvpStatus.confirmed if showed_up else RsvpStatus.declined

                rsvp = SessionRsvp(
                    session_id=event.id,
                    volunteer_id=vol.id,
                    status=rsvp_status,
                    reminder_sent=True,
                )
                db.add(rsvp)
                total_rsvps += 1

                # Only log if volunteer showed up AND log completion rate hit
                if showed_up and random.random() < SEED_CONFIG["log_completion_rate"]:
                    vol_kids = assignments.get(vol.id, [])
                    for kid in vol_kids:
                        # Rating — weighted toward okay/nailed-it
                        rating = random.choices(
                            [SessionRating.struggling, SessionRating.okay, SessionRating.nailed_it],
                            weights=[20, 45, 35]
                        )[0]

                        subject = random.choice(["math", "english"])
                        chapter_num = kid.math_chapter if subject == "math" else kid.english_chapter

                        log = SessionLog(
                            session_id=event.id,
                            volunteer_id=vol.id,
                            kid_id=kid.id,
                            rating=rating,
                            subject=subject,
                            chapter_covered=chapter_num,
                        )
                        db.add(log)
                        total_logs += 1

                        # Progress — slowly advance chapter over time
                        if rating == SessionRating.nailed_it and week % 4 == 0:
                            if subject == "math" and kid.math_chapter < 9:
                                kid.math_chapter += 1
                            elif subject == "english" and kid.english_chapter < 9:
                                kid.english_chapter += 1

        db.commit()

    print(f"  Created {SEED_CONFIG['session_weeks'] * 3} session events")
    print(f"  Created {total_rsvps} RSVPs ({int(SEED_CONFIG['no_show_rate']*100)}% no-show rate)")
    print(f"  Created {total_logs} session logs ({int(SEED_CONFIG['log_completion_rate']*100)}% completion rate)")


def create_fund_drives_and_wishlist(
    db: Session,
    chapters: list[Chapter],
    kids: list[Kid]
) -> None:
    print("Creating fund drives and wishlist items...")
    drives_created = 0
    items_created = 0

    for chapter in chapters:
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]

        drive = FundDrive(
            chapter_id=chapter.id,
            title=f"Book & Resources Drive 2024 — {chapter.name}",
            goal_amount=SEED_CONFIG["fund_drive_goal"],
            raised_amount=round(
                SEED_CONFIG["fund_drive_goal"] * SEED_CONFIG["fund_drive_raised_pct"], 2
            ),
            start_date=date(2024, 1, 15),
            end_date=date(2024, 3, 31),
            is_active=True,
        )
        db.add(drive)
        db.flush()
        drives_created += 1

        # Wishlist — mix of kid-specific and chapter-level items
        # Kid-specific items (the "buy Arjun his sketchbook" feature)
        sample_kids = random.sample(chapter_kids, min(8, len(chapter_kids)))
        for kid in sample_kids:
            item_name, amount = random.choice(WISHLIST_ITEMS)
            status = random.choices(
                [WishlistStatus.open, WishlistStatus.funded, WishlistStatus.used],
                weights=[50, 30, 20]
            )[0]
            item = WishlistItem(
                kid_id=kid.id,
                fund_drive_id=drive.id,
                item_name=item_name,
                amount_needed=amount,
                status=status,
                ml_generated=random.choice([True, False]),
            )
            db.add(item)
            items_created += 1

        # Chapter-level items (e.g. story books for everyone)
        for _ in range(3):
            item_name, amount = random.choice(WISHLIST_ITEMS)
            item = WishlistItem(
                kid_id=None,
                fund_drive_id=drive.id,
                item_name=item_name,
                description=f"For all kids in {chapter.name}",
                amount_needed=amount * 10,
                status=WishlistStatus.open,
            )
            db.add(item)
            items_created += 1

    db.commit()
    print(f"  Created {drives_created} fund drives (₹{SEED_CONFIG['fund_drive_goal']:,.0f} goal each)")
    print(f"  Created {items_created} wishlist items")


def create_donors(db: Session) -> list[User]:
    print("Creating donor accounts...")
    donors = []
    donor_names = [
        "Rajesh Mehta", "Sunita Kapoor", "Arun Patel",
        "Lakshmi Iyer", "Sanjay Gupta", "Preethi Nair",
        "Venkat Rao", "Anitha Sharma", "Dinesh Choudhary", "Kavitha Menon"
    ]
    for i, name in enumerate(donor_names):
        donor = User(
            full_name=name,
            email=f"donor_{i}@example.com",
            hashed_password=hash_password("donor123"),
            role=UserRole.donor,
            chapter_id=None,
        )
        db.add(donor)
        donors.append(donor)
    db.commit()
    [db.refresh(d) for d in donors]
    print(f"  Created {len(donors)} donor accounts")
    return donors


def print_summary(db: Session) -> None:
    from app.models import Chapter, User, Kid, SessionEvent, SessionLog, FundDrive, WishlistItem

    print("\n" + "="*55)
    print("  IMPACTBRIDGE — SEED DATA SUMMARY")
    print("="*55)
    print(f"  Chapters     : {db.query(Chapter).count()}")
    print(f"  Kids         : {db.query(Kid).count()} (across 3 Vizag chapters)")
    print(f"  Volunteers   : {db.query(User).filter_by(role=UserRole.volunteer).count()}")
    print(f"  Coordinators : {db.query(User).filter_by(role=UserRole.coordinator).count()}")
    print(f"  Donors       : {db.query(User).filter_by(role=UserRole.donor).count()}")
    print(f"  Sessions     : {db.query(SessionEvent).count()} (44 Sundays × 3 chapters)")
    print(f"  Session logs : {db.query(SessionLog).count()} (70% completion rate)")
    print(f"  Fund drives  : {db.query(FundDrive).count()}")
    print(f"  Wishlist     : {db.query(WishlistItem).count()} items")
    print("="*55)
    print("  Credentials (for testing):")
    print("  Coordinator : coord_0_0@impactbridge.org / coord123")
    print("  Volunteer   : vol_0@impactbridge.org / vol123")
    print("  Donor       : donor_0@example.com / donor123")
    print("="*55)


def run_seed():
    print("\nDropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created.\n")

    db = SessionLocal()
    try:
        chapters    = create_chapters(db)
        coordinators= create_coordinators(db, chapters)
        volunteers  = create_volunteers(db, chapters)
        kids        = create_kids(db, chapters)
        create_assignments(db, volunteers, kids, chapters)
        create_sessions_and_logs(db, chapters, volunteers, kids)
        create_fund_drives_and_wishlist(db, chapters, kids)
        donors      = create_donors(db)
        print_summary(db)
        print("\nSeed complete. Run the FastAPI server to explore the data.")
    except Exception as e:
        db.rollback()
        print(f"\nSeed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
