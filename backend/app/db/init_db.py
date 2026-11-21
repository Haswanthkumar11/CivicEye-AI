from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.department import Department
import app.models  # ensure all models are registered with Base.metadata
from app.core.security import get_password_hash

# Predefined standard municipal departments for civic routing
DEFAULT_DEPARTMENTS = [
    {
        "name": "Municipal Roads & Infrastructure",
        "code": "ROADS",
        "description": "Responsible for potholes, asphalt damage, road cave-ins, and bridge maintenance.",
        "contact_email": "roads@civiceye.gov",
    },
    {
        "name": "Water Supply & Sewerage Board",
        "code": "WATER",
        "description": "Responsible for pipe bursts, potable water shortages, contaminated supply, and leaks.",
        "contact_email": "water@civiceye.gov",
    },
    {
        "name": "Solid Waste Management & Sanitation",
        "code": "SANITATION",
        "description": "Handles garbage pileups, open waste burning, street sweeping, and animal carcasses.",
        "contact_email": "sanitation@civiceye.gov",
    },
    {
        "name": "Storm Water & Surface Drainage",
        "code": "DRAINAGE",
        "description": "Responsible for clogged storm drains, monsoon overflow, manhole covers, and sewer flooding.",
        "contact_email": "drainage@civiceye.gov",
    },
    {
        "name": "Electricity & Public Lighting",
        "code": "ELECTRICAL",
        "description": "Handles faulty streetlights, hanging live wires, damaged transformers, and power hazards.",
        "contact_email": "electrical@civiceye.gov",
    },
    {
        "name": "Public Infrastructure & Parks",
        "code": "PUBLIC_INFRA",
        "description": "Responsible for bus shelters, public parks, footpaths, civic signage, and encroachment.",
        "contact_email": "infra@civiceye.gov",
    },
]

DEMO_USERS = [
    {
        "email": "citizen@civiceye.gov",
        "password": "Citizen@123",
        "full_name": "Ravi Kumar (Citizen)",
        "phone_number": "+91 98765 43210",
        "role": "citizen",
    },
    {
        "email": "admin@civiceye.gov",
        "password": "Admin@123",
        "full_name": "Municipal Commissioner (Admin)",
        "phone_number": "+91 98765 00001",
        "role": "admin",
    },
]


def init_db():
    """Initializes tables and seeds default municipal departments & test accounts."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Seed Departments
        for dept_data in DEFAULT_DEPARTMENTS:
            existing_dept = db.query(Department).filter(Department.code == dept_data["code"]).first()
            if not existing_dept:
                dept = Department(
                    name=dept_data["name"],
                    code=dept_data["code"],
                    description=dept_data["description"],
                    contact_email=dept_data["contact_email"],
                    is_active=True,
                )
                db.add(dept)

        # Seed Demo Users
        for user_data in DEMO_USERS:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    phone_number=user_data["phone_number"],
                    role=user_data["role"],
                    is_active=True,
                )
                db.add(new_user)
        
        db.commit()
        print("✅ Database tables created and seed data initialized successfully.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Error during database initialization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
