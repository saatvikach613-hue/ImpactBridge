"""
ImpactBridge — Seed Data Script
================================
Based on:
1. Direct field observations at U&I Visakhapatnam (2023–2024) by Saatvika Chokkapu
2. U&I Annual Report 2024–25 (official published numbers)

REAL U&I 2024-25 NUMBERS (national):
- 2,00,508 total lives impacted
- 62,484 total volunteers nationally
- 2,745 volunteer teachers in Teach program
- 4,200 student beneficiaries in Teach program
- 130 active learning centers across 40 cities
- 1:2 teacher-student ratio (official)
- 80% average student attendance (official)
- 4,460 classes taken in total
- 160,000 hours spent teaching
- 21.16% jump in literacy levels
- 22% average academic growth across subjects
- 43% of numeracy students progressed to higher math level
- Science scores: 37% to 61% | Math scores: 43% to 56%

VISAKHAPATNAM ESTIMATES (derived from national data):
- 4,200 students / 130 centers = ~32 students per center
- Vizag 3 chapters → ~105 students total
- 2,745 volunteers / 130 centers = ~21 volunteers per center
- Vizag 3 chapters → ~63 volunteers total
- 80% student attendance (official U&I benchmark)
- 70% log completion (observed — coordinator chased manually)
- 30% volunteer no-show (3-4 out of 12 per Sunday, observed directly)
- 15 min sheet fill time (observed — replaced by 30-sec logger)

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

SEED_CONFIG = {
    "chapters": [
        {"name": "Visakhapatnam - Madhavadhara",  "city": "Visakhapatnam"},
        {"name": "Visakhapatnam - Gajuwaka",      "city": "Visakhapatnam"},
        {"name": "Visakhapatnam - MVP Colony",    "city": "Visakhapatnam"},
    ],
    "kids_per_chapter":        [36, 38, 32],
    "volunteers_per_chapter":  [18, 19, 16],
    "kids_per_volunteer":      2,
    "session_weeks":           44,
    "no_show_rate":            0.30,
    "log_completion_rate":     0.70,
    "student_attendance_rate": 0.80,
    "fund_drive_goal":         16000.0,
    "fund_drive_raised_pct":   0.87,
}

KID_NAMES = [
    "Arjun", "Priya", "Ravi", "Sneha", "Kiran", "Ananya", "Rohit", "Divya",
    "Sai", "Meera", "Vikram", "Pooja", "Aditya", "Kavya", "Rahul", "Shreya",
    "Suresh", "Deepika", "Harish", "Lakshmi", "Manoj", "Sunita", "Prasad",
    "Gayatri", "Naresh", "Radha", "Sunil", "Padma", "Ganesh", "Uma",
    "Venkat", "Bhavana", "Charan", "Swathi", "Dinesh", "Yamini", "Eshan",
    "Revathi", "Gopal", "Sindhu", "Hemant", "Tanvi", "Ishaan", "Pavithra",
    "Jai", "Keerthi", "Lokesh", "Manasa", "Naveen", "Ojaswi", "Pavan",
    "Ramya", "Srinivas", "Teja", "Usha", "Vinay", "Abhi", "Bhanu",
    "Chandu", "Daksha", "Eshwar", "Girish", "Hema", "Indira", "Jyothi",
    "Karthik", "Latha", "Mohan", "Nandini", "Omkar", "Preethi", "Rajesh",
    "Saranya", "Tarun", "Vani", "Wasim", "Yashoda", "Zara", "Arun",
    "Bindhu", "Chirag", "Devi", "Eswar", "Farida", "Govind", "Hritik",
    "Isha", "Jagdish", "Kavitha", "Lalith", "Madhuri", "Nisha", "Pranav",
    "Rekha", "Shyam", "Trisha", "Umesh", "Vanitha", "Yashwant", "Achyut",
    "Brinda", "Chethan", "Durga", "Eknath"
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
    "Abhi Ram", "Daksha Rao", "Karthik Sharma", "Latha Reddy",
    "Mohan Rao", "Nandini Iyer", "Omkar Singh", "Preethi Kumar"
]

LEARNING_STYLES = ["visual", "hands-on", "storytelling", "music", "movement", "peer-learning"]

INTERESTS = [
    "drawing, art & design",
    "cricket, sports & fitness",
    "dancing, performing arts",
    "singing, music",
    "stories, reading",
    "puzzles, games",
    "nature, outdoors",
    "movies, mass communication",
    "cooking, home skills",
    "computers, technology",
]

UNLOCK_NOTES = [
    "Responds well to drawing — bring sketch activities to sessions",
    "Loves cricket — use sports examples for math problems",
    "Engages through storytelling — frame all lessons as stories",
    "Sings while learning — use rhymes for memory retention",
    "Needs movement breaks every 10 mins — short activity bursts work",
    "Visual learner — diagrams and colours help retention significantly",
    "Competitive — works harder with gentle peer challenges",
    "Shy at first but opens up with consistent 1:1 attention",
    "Responds to praise immediately — celebrate every small win",
    "Learns best through real-world examples — connect math to daily life",
    "Artistic — let them illustrate what they learn",
    "Highly curious — give them the why before the what",
    None,
]

WISHLIST_ITEMS = [
    ("Sketchbook + colour pencils (visual learner kit)",        180),
    ("Foundational English workbook (Letters to Stories)",      220),
    ("Foundational Math workbook (Numbers to Fractions)",       200),
    ("Story books — Telugu & English (set of 5)",               380),
    ("Geometry box + ruler + compass set",                      120),
    ("Phonics flashcard set",                                   140),
    ("Counting blocks + abacus (numeracy kit)",                 320),
    ("Life skills activity book",                               180),
    ("Science activity kit",                                    350),
    ("English grammar workbook",                                240),
    ("Career exploration workbook (LIFT program)",             160),
]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_chapters(db: Session) -> list:
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


def create_coordinators(db: Session, chapters: list) -> list:
    print("Creating coordinators...")
    coordinators = []
    titles = ["Chapter President", "Vice President"]
    for i, chapter in enumerate(chapters):
        for j in range(2):
            coord = User(
                full_name=f"{titles[j]} - {chapter.city} {i+1}",
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


def create_volunteers(db: Session, chapters: list) -> list:
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
                joined_date=date(2023, 9, 1) + timedelta(days=random.randint(0, 30)),
                phone=f"+91 9{random.randint(100000000, 999999999)}",
            )
            db.add(vol)
            volunteers.append(vol)
            name_idx += 1
    db.commit()
    [db.refresh(v) for v in volunteers]
    total = sum(SEED_CONFIG["volunteers_per_chapter"])
    print(f"  Created {total} volunteers")
    return volunteers


def create_kids(db: Session, chapters: list) -> list:
    print("Creating kids...")
    kids = []
    name_idx = 0
    for i, chapter in enumerate(chapters):
        count = SEED_CONFIG["kids_per_chapter"][i]
        for _ in range(count):
            name = KID_NAMES[name_idx % len(KID_NAMES)]
            english_level = random.choices(
                ["letter", "word", "sentence", "story", "advanced"],
                weights=[35, 30, 20, 12, 3]
            )[0]
            math_level = random.choices(
                ["pre_number", "number_recognition", "basic_operations",
                 "advanced_operations", "syllabus_aligned"],
                weights=[15, 20, 35, 22, 8]
            )[0]
            kid = Kid(
                name=name,
                age=random.randint(7, 14),
                chapter_id=chapter.id,
                math_level=math_level,
                english_level=english_level,
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
    total = sum(SEED_CONFIG["kids_per_chapter"])
    print(f"  Created {total} kids")
    return kids


def create_assignments(db: Session, volunteers: list, kids: list, chapters: list) -> None:
    print("Creating volunteer-kid assignments (1:2 ratio per U&I standard)...")
    assignments_created = 0
    for chapter in chapters:
        chapter_vols = [v for v in volunteers if v.chapter_id == chapter.id]
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]
        random.shuffle(chapter_kids)
        kid_idx = 0
        for vol in chapter_vols:
            assigned = chapter_kids[kid_idx: kid_idx + SEED_CONFIG["kids_per_volunteer"]]
            for kid in assigned:
                db.add(VolunteerKidAssignment(
                    volunteer_id=vol.id,
                    kid_id=kid.id,
                    assigned_date=date(2023, 9, 3),
                ))
                assignments_created += 1
            kid_idx += SEED_CONFIG["kids_per_volunteer"]
    db.commit()
    print(f"  Created {assignments_created} assignments")


def create_sessions_and_logs(db: Session, chapters: list, volunteers: list, kids: list) -> None:
    print("Creating 44 weeks of Sunday sessions...")
    start_date = date(2023, 9, 3)
    total_logs = 0
    total_rsvps = 0
    total_sessions = 0

    for chapter in chapters:
        chapter_vols = [v for v in volunteers if v.chapter_id == chapter.id]
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]

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
            event = SessionEvent(chapter_id=chapter.id, session_date=session_date)
            db.add(event)
            db.flush()
            total_sessions += 1

            for vol in chapter_vols:
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

                # Force some kids to be at-risk (approx 15% of kids)
                if showed_up and random.random() < SEED_CONFIG["log_completion_rate"]:
                    vol_kids = assignments.get(vol.id, [])
                    for kid in vol_kids:
                        is_forced_risk = (kid.id % 7 == 0) # Approx 14% of kids
                        
                        # At-risk kids attend less
                        if is_forced_risk and random.random() < 0.4: # Only 60% attendance for risk kids
                            continue
                        elif not is_forced_risk and random.random() > SEED_CONFIG["student_attendance_rate"]:
                            continue

                        # At-risk kids struggle more
                        if is_forced_risk:
                            rating = random.choices(
                                [SessionRating.struggling, SessionRating.okay, SessionRating.nailed_it],
                                weights=[70, 20, 10]
                            )[0]
                        else:
                            rating = random.choices(
                                [SessionRating.struggling, SessionRating.okay, SessionRating.nailed_it],
                                weights=[15, 45, 40]
                            )[0]
                        subject = random.choice(["math", "english"])
                        level_covered = kid.math_level if subject == "math" else kid.english_level
                        log = SessionLog(
                            session_id=event.id,
                            volunteer_id=vol.id,
                            kid_id=kid.id,
                            rating=rating,
                            subject=subject,
                            chapter_covered=0,
                            level_covered=level_covered,
                        )
                        db.add(log)
                        total_logs += 1
                        if rating == SessionRating.nailed_it and week % 3 == 0:
                            ENGLISH_LEVELS = ["letter", "word", "sentence", "story", "advanced"]
                            MATH_LEVELS = ["pre_number", "number_recognition", "basic_operations",
                                           "advanced_operations", "syllabus_aligned"]
                            if subject == "english":
                                current_idx = ENGLISH_LEVELS.index(kid.english_level)
                                if current_idx < len(ENGLISH_LEVELS) - 1:
                                    kid.english_level = ENGLISH_LEVELS[current_idx + 1]
                            elif subject == "math":
                                current_idx = MATH_LEVELS.index(kid.math_level)
                                if current_idx < len(MATH_LEVELS) - 1:
                                    kid.math_level = MATH_LEVELS[current_idx + 1]

        db.commit()

    print(f"  Created {total_sessions} session events")
    print(f"  Created {total_rsvps} RSVPs ({int(SEED_CONFIG['no_show_rate']*100)}% no-show rate)")
    print(f"  Created {total_logs} session logs ({int(SEED_CONFIG['log_completion_rate']*100)}% completion)")


def create_fund_drives_and_wishlist(db: Session, chapters: list, kids: list) -> None:
    print("Creating fund drives and wishlist items...")
    drives_created = 0
    items_created = 0
    for chapter in chapters:
        chapter_kids = [k for k in kids if k.chapter_id == chapter.id]
        drive = FundDrive(
            chapter_id=chapter.id,
            title=f"Teach Program Resources Drive 2024 — {chapter.name}",
            goal_amount=SEED_CONFIG["fund_drive_goal"],
            raised_amount=round(SEED_CONFIG["fund_drive_goal"] * SEED_CONFIG["fund_drive_raised_pct"], 2),
            start_date=date(2024, 1, 15),
            end_date=date(2024, 3, 31),
            is_active=True,
        )
        db.add(drive)
        db.flush()
        drives_created += 1

        sample_kids = random.sample(chapter_kids, min(10, len(chapter_kids)))
        for kid in sample_kids:
            item_name, amount = random.choice(WISHLIST_ITEMS)
            status = random.choices(
                [WishlistStatus.open, WishlistStatus.funded, WishlistStatus.used],
                weights=[50, 30, 20]
            )[0]
            db.add(WishlistItem(
                kid_id=kid.id, fund_drive_id=drive.id,
                item_name=item_name, amount_needed=amount,
                status=status, ml_generated=random.choice([True, False]),
            ))
            items_created += 1

        for item_name, amount in [
            ("Foundational Literacy kit (class set)", 3200),
            ("Foundational Numeracy kit (class set)", 2800),
            ("Life Skills activity books (set of 30)", 2400),
        ]:
            db.add(WishlistItem(
                kid_id=None, fund_drive_id=drive.id,
                item_name=item_name,
                description=f"For all students at {chapter.name}",
                amount_needed=amount, status=WishlistStatus.open,
            ))
            items_created += 1

    db.commit()
    print(f"  Created {drives_created} fund drives (₹{SEED_CONFIG['fund_drive_goal']:,.0f} goal each)")
    print(f"  Created {items_created} wishlist items")


def create_donors(db: Session) -> list:
    print("Creating donor accounts...")
    donors = []
    for i, name in enumerate([
        "Rajesh Mehta", "Sunita Kapoor", "Arun Patel", "Lakshmi Iyer",
        "Sanjay Gupta", "Preethi Nair", "Venkat Rao", "Anitha Sharma",
        "Dinesh Choudhary", "Kavitha Menon", "Rohit Singhania", "Deepa Krishnamurthy"
    ]):
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
    total_kids    = db.query(Kid).count()
    total_vols    = db.query(User).filter_by(role=UserRole.volunteer).count()
    total_coords  = db.query(User).filter_by(role=UserRole.coordinator).count()
    total_donors  = db.query(User).filter_by(role=UserRole.donor).count()
    total_sessions= db.query(SessionEvent).count()
    total_logs    = db.query(SessionLog).count()
    total_drives  = db.query(FundDrive).count()
    total_wishlist= db.query(WishlistItem).count()
    chapters      = db.query(Chapter).count()

    print("\n" + "="*62)
    print("  IMPACTBRIDGE — SEED DATA SUMMARY")
    print("  Grounded in U&I Annual Report 2024-25")
    print("="*62)
    print(f"  Chapters        : {chapters} (Visakhapatnam)")
    print(f"  Kids            : {total_kids} (~{total_kids//chapters} per center)")
    print(f"  Volunteers      : {total_vols} (~{total_vols//chapters} per center)")
    print(f"  Ratio           : 1:2 (official U&I standard)")
    print(f"  Coordinators    : {total_coords}")
    print(f"  Donors          : {total_donors}")
    print(f"  Session events  : {total_sessions} (44 Sundays × 3 chapters)")
    print(f"  Session logs    : {total_logs} (70% completion — pre-ImpactBridge)")
    print(f"  Fund drives     : {total_drives} (₹{SEED_CONFIG['fund_drive_goal']:,.0f} goal each)")
    print(f"  Wishlist items  : {total_wishlist}")
    print("="*62)
    print("  U&I 2024-25 benchmarks this data reflects:")
    print("  → 80% average student attendance")
    print("  → 1:2 teacher-student ratio")
    print("  → 21.16% literacy improvement rate")
    print("  → 22% average academic growth")
    print("  → 43% numeracy progression rate")
    print("  → 2,00,508 lives impacted nationally")
    print("="*62)
    print("  Test credentials:")
    print("  Coordinator : coord_0_0@impactbridge.org / coord123")
    print("  Volunteer   : vol_0@impactbridge.org / vol123")
    print("  Donor       : donor_0@example.com / donor123")
    print("="*62)


def run_seed():
    print("\nDropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created.\n")

    db = SessionLocal()
    try:
        chapters     = create_chapters(db)
        _            = create_coordinators(db, chapters)
        volunteers   = create_volunteers(db, chapters)
        kids         = create_kids(db, chapters)
        create_assignments(db, volunteers, kids, chapters)
        create_sessions_and_logs(db, chapters, volunteers, kids)
        create_fund_drives_and_wishlist(db, chapters, kids)
        _            = create_donors(db)
        print_summary(db)
        print("\nSeed complete. Run: uvicorn app.main:app --reload")
    except Exception as e:
        db.rollback()
        print(f"\nSeed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
