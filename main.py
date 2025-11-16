from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Database utilities are pre-configured and provided by the environment
# They expose: db (Mongo database), create_document, get_documents
from database import db, create_document, get_documents  # type: ignore

app = FastAPI(title="Healthcare Benefits API", version="1.0.0")

# CORS: allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schemas (mirror of schemas.py but kept minimal here for direct use)
class ContactIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: Optional[str] = None
    message: str = Field(..., min_length=5, max_length=5000)
    preferred_time: Optional[str] = None


class ContactOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: str
    created_at: datetime


class Testimonial(BaseModel):
    author: str
    role: Optional[str] = None
    company: Optional[str] = None
    quote: str
    logo: Optional[str] = None


class TeamMember(BaseModel):
    name: str
    role: str
    bio: str
    photo: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None


class Service(BaseModel):
    key: str
    title: str
    subtitle: Optional[str] = None
    description: str
    icon: Optional[str] = None


@app.get("/test")
async def test_db():
    # Simple check that listCollections works
    try:
        await db.list_collection_names()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contact", response_model=ContactOut)
async def create_contact(payload: ContactIn):
    data = payload.dict()
    doc = await create_document("contact", data)
    # Map Mongo _id to id
    return ContactOut(
        id=str(doc.get("_id")),
        name=doc["name"],
        email=doc["email"],
        company=doc.get("company"),
        message=doc["message"],
        created_at=doc["created_at"],
    )


@app.get("/services", response_model=List[Service])
async def list_services():
    # Services can be static definitions served from DB when available
    # If collection empty, return defaults without writing
    defaults: List[Service] = [
        Service(
            key="corporate-benefits",
            title="Corporate Benefits Packages",
            subtitle="Custom plans for every team",
            description="Design comprehensive, scalable health plans for organizations of any size, optimized for cost, coverage, and employee satisfaction.",
            icon="Building",
        ),
        Service(
            key="wellness-programs",
            title="Employee Wellness Programs",
            subtitle="Holistic wellbeing at work",
            description="From fitness and nutrition to mental health, empower your workforce with programs that measurably improve wellbeing.",
            icon="HeartPulse",
        ),
        Service(
            key="telemedicine",
            title="Telemedicine & Digital Health",
            subtitle="Care, anywhere",
            description="Remote consultations, virtual primary care, and digital tools that bring healthcare to your people wherever they are.",
            icon="Smartphone",
        ),
        Service(
            key="claims-management",
            title="Insurance & Claims Management",
            subtitle="End-to-end support",
            description="Streamlined administration for benefits, eligibility, and claims — with transparency and compliance built-in.",
            icon="ShieldCheck",
        ),
    ]
    try:
        docs = await get_documents("service", {}, limit=100)
        if not docs:
            return defaults
        out: List[Service] = []
        for d in docs:
            out.append(Service(
                key=d.get("key", "service"),
                title=d.get("title", "Service"),
                subtitle=d.get("subtitle"),
                description=d.get("description", ""),
                icon=d.get("icon"),
            ))
        return out
    except Exception:
        # If DB not reachable for some reason, gracefully fallback
        return defaults


@app.get("/team", response_model=List[TeamMember])
async def list_team():
    defaults: List[TeamMember] = [
        TeamMember(
            name="Ava Thompson, MPH",
            role="Chief Executive Officer",
            bio="Leader in value-based care and benefits innovation with 15+ years building equitable health ecosystems.",
            photo=None,
            linkedin="https://www.linkedin.com/",
        ),
        TeamMember(
            name="Daniel Kim, FSA",
            role="Chief Actuary",
            bio="Actuarial strategist focused on cost containment and data-driven plan design for modern workforces.",
            photo=None,
            linkedin="https://www.linkedin.com/",
        ),
        TeamMember(
            name="Priya Nair, RN MSN",
            role="VP, Clinical Programs",
            bio="Nurse leader bringing human-centered care pathways to digital-first populations.",
            photo=None,
            linkedin="https://www.linkedin.com/",
        ),
        TeamMember(
            name="Miguel Alvarez",
            role="Director, Digital Health",
            bio="Builder of telehealth and engagement platforms connecting patients to the right care at the right time.",
            photo=None,
            linkedin="https://www.linkedin.com/",
        ),
    ]
    try:
        docs = await get_documents("teammember", {}, limit=100)
        if not docs:
            return defaults
        return [TeamMember(**{k: v for k, v in d.items() if k in TeamMember.__fields__}) for d in docs]
    except Exception:
        return defaults


@app.get("/testimonials", response_model=List[Testimonial])
async def list_testimonials():
    defaults: List[Testimonial] = [
        Testimonial(
            author="Lena M.",
            role="VP People",
            company="Atlas Robotics",
            quote="Their benefits redesign cut our costs by 12% while boosting engagement — the best decision we made this year.",
        ),
        Testimonial(
            author="Craig P.",
            role="Head of Total Rewards",
            company="Northwind Logistics",
            quote="Implementation was seamless and our employees love the telehealth access and mental health support.",
        ),
        Testimonial(
            author="Dr. Sofia R.",
            role="Medical Director",
            company="CareWorks Clinic",
            quote="Thoughtful, data-driven partners who truly understand the clinical and financial sides of health benefits.",
        ),
    ]
    try:
        docs = await get_documents("testimonial", {}, limit=100)
        if not docs:
            return defaults
        return [Testimonial(**{k: v for k, v in d.items() if k in Testimonial.__fields__}) for d in docs]
    except Exception:
        return defaults
