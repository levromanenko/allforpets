from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, date, timedelta
import uvicorn
import os
import shutil
import calendar as cal
import json

engine = create_engine("sqlite:///./petshelsi.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")
    is_blocked = Column(Boolean, default=False)
    pets = relationship("Pet", back_populates="owner")
    owned_clinics = relationship("Clinic", back_populates="owner")

class Pet(Base):
    __tablename__ = "pets"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    breed = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    medical_notes = Column(Text, nullable=True)
    medical_doc = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="pets")
    moods = relationship("Mood", back_populates="pet")
    visits = relationship("Visit", back_populates="pet")
    reminders = relationship("Reminder", back_populates="pet")

class Mood(Base):
    __tablename__ = "moods"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    mood = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    pet = relationship("Pet", back_populates="moods")

class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    district = Column(String, nullable=True)
    street = Column(String, nullable=True)
    house = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    work_hours = Column(String, nullable=True)
    is_24h = Column(Boolean, default=False)
    has_online_booking = Column(Boolean, default=False)
    show_vets = Column(Boolean, default=True)
    status = Column(String, default="pending")
    documents = Column(String, nullable=True)
    terms_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="owned_clinics")
    vets = relationship("Vet", back_populates="clinic")

class ClinicManager(Base):
    __tablename__ = "clinic_managers"
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    can_edit_clinic = Column(Boolean, default=False)
    can_manage_vets = Column(Boolean, default=False)
    can_view_schedule = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    clinic = relationship("Clinic")
    user = relationship("User")

class Vet(Base):
    __tablename__ = "vets"
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    animal_type = Column(String, nullable=True)
    service = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    experience = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    clinic = relationship("Clinic", back_populates="vets")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    vet_id = Column(Integer, ForeignKey("vets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True)
    date = Column(Date, nullable=False)
    time = Column(String, nullable=False)
    complaint = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    vet_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date)
    notes = Column(Text)
    document = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    pet = relationship("Pet")
    vet = relationship("User")
class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    vet_id = Column(Integer, ForeignKey("vets.id"), nullable=True)
    date = Column(Date, nullable=False)
    text = Column(Text, nullable=False)
    reminder_type = Column(String, default="routine")
    created_at = Column(DateTime, default=datetime.utcnow)
    pet = relationship("Pet", back_populates="reminders")

class WeightEntry(Base):
    __tablename__ = "weight_entries"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    date = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ToothCleaning(Base):
    __tablename__ = "tooth_cleanings"
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"))
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReminderCompletion(Base):
    __tablename__ = "reminder_completions"
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

class Pharmacy(Base):
    __tablename__ = "pharmacies"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=True)
    street = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    work_hours = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    documents = Column(String, nullable=True)
    edrpou = Column(String, nullable=True)
    status = Column(String, default="pending")
    terms_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    form = Column(String, nullable=True)
    volume = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    animal_type = Column(String, nullable=True)
    weight_from = Column(String, nullable=True)
    weight_to = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PharmacyProduct(Base):
    __tablename__ = "pharmacy_products"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="moi-ulyublentsi-secret-key-2026")
templates = Jinja2Templates(directory="templates")

os.makedirs("static/pets", exist_ok=True)
os.makedirs("static/clinic_docs", exist_ok=True)
os.makedirs("static/visits", exist_ok=True)
os.makedirs("static/vets", exist_ok=True)
os.makedirs("static/clinics", exist_ok=True)
os.makedirs("static/medical", exist_ok=True)
os.makedirs("static/pharmacies", exist_ok=True)
os.makedirs("static/pharmacy_docs", exist_ok=True)
os.makedirs("static/products", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

MOOD_EMOJI = {
    "жахливо": "😫",
    "погано": "😔",
    "нормально": "😐",
    "добре": "🙂",
    "дуже добре": "🤩"
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_blocked:
        request.session.clear()
        return None
    return user

def require_admin(user):
    return user and user.role == "admin"

def get_my_clinic(user, db):
    if not user:
        return None
    return db.query(Clinic).filter(Clinic.owner_id == user.id).first()

def get_my_pharmacy(user, db):
    if not user:
        return None
    return db.query(Pharmacy).filter(Pharmacy.owner_id == user.id).first()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    pets = []
    pets_need_mood = []
    main_reminders = []
    if user:
        pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
        if pets:
            today = date.today()
            for p in pets:
                today_mood = db.query(Mood).filter(
                    Mood.pet_id == p.id,
                    Mood.created_at >= datetime.combine(today, datetime.min.time())
                ).first()
                if not today_mood:
                    pets_need_mood.append(p)
            for p in pets:
                appts = db.query(Appointment).filter(Appointment.pet_id == p.id).all()
                for a in appts:
                    days_left = (a.date - today).days
                    if days_left == 14:
                        main_reminders.append({
                            "type": "appointment",
                            "color": "#2196f3",
                            "title": f"Прийом: {p.name}",
                            "text": f"{a.date.strftime('%d.%m')} о {a.time}",
                            "pet_id": p.id
                        })
                rems = db.query(Reminder).filter(Reminder.pet_id == p.id).all()
                for r in rems:
                    days_left = (r.date - today).days
                    if r.reminder_type == "deworm" and days_left == 7:
                        main_reminders.append({
                            "type": "deworm",
                            "color": "#c62828",
                            "title": f"Дегельмінтизація: {p.name}",
                            "text": r.text,
                            "pet_id": p.id
                        })
                    elif r.reminder_type == "routine" and days_left == 1:
                        main_reminders.append({
                            "type": "routine",
                            "color": "#ff9800",
                            "title": f"Нагадування: {p.name}",
                            "text": r.text,
                            "pet_id": p.id
                        })
                    elif r.reminder_type == "weight" and days_left == 2:
                        main_reminders.append({
                            "type": "weight",
                            "color": "#4caf50",
                            "title": f"Зважити: {p.name}",
                            "text": r.text,
                            "pet_id": p.id
                        })
                    elif r.reminder_type == "tooth" and days_left == 2:
                        main_reminders.append({
                            "type": "tooth",
                            "color": "#ffeb3b",
                            "title": f"Чистка зубів: {p.name}",
                            "text": r.text,
                            "pet_id": p.id
                        })
    return templates.TemplateResponse(request, "main.html", {
        "user": user,
        "pets": pets,
        "pets_need_mood": pets_need_mood,
        "main_reminders": main_reminders
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(request, "settings.html", {"user": user})

@app.get("/search", response_class=HTMLResponse)
async def search_vets(request: Request, q: str = "", specialty: str = "", db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    spec = specialty.strip() or q.strip()
    vets_query = db.query(Vet).join(Clinic).filter(Clinic.status == "approved")
    if spec:
        vets_query = vets_query.filter(Vet.specialty.ilike(f"%{spec}%"))
    vets = vets_query.all()
    return templates.TemplateResponse(request, "search.html", {"user": user, "q": spec, "vets": vets})

@app.get("/vet/cabinet", response_class=HTMLResponse)
async def vet_cabinet(request: Request, year: int = None, month: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/cabinet")

    my_vets = db.query(Vet).filter(Vet.user_id == user.id).all()
    vet_ids = [v.id for v in my_vets]

    appointments = db.query(Appointment).filter(
        Appointment.vet_id.in_(vet_ids),
        Appointment.status != "canceled"
    ).order_by(Appointment.date, Appointment.time).all() if vet_ids else []

    appointments_json = []
    for a in appointments:
        date_str = str(a.date)[:10]
        appointments_json.append({
            "id": a.id,
            "date": date_str,
            "time": a.time or "",
            "complaint": a.complaint or "",
            "pet_id": a.pet_id
        })

    today = date.today()
    if year is None: year = today.year
    if month is None: month = today.month
    if month < 1: month, year = 12, year - 1
    if month > 12: month, year = 1, year + 1

    month_days = cal.monthcalendar(year, month)
    month_name = date(year, month, 1).strftime("%B %Y")
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    clinic = None
    work_hours = "09:00-18:00"
    if my_vets and my_vets[0].clinic_id:
        clinic = db.query(Clinic).filter(Clinic.id == my_vets[0].clinic_id).first()
        if clinic and clinic.work_hours:
            work_hours = clinic.work_hours

    return templates.TemplateResponse(request, "vet_cabinet.html", {
        "user": user,
        "my_vets": my_vets,
        "appointments": appointments,
        "appointments_json": json.dumps(appointments_json),
        "month_days": month_days,
        "year": year,
        "month": month,
        "month_name": month_name,
        "today": today,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "work_hours": work_hours
    })

@app.post("/vet/search-client")
async def vet_search_client(request: Request, client_id: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/cabinet")
    try:
        cid = int(client_id)
    except:
        return RedirectResponse(url="/vet/cabinet")
    client = db.query(User).filter(User.id == cid).first()
    if not client:
        return templates.TemplateResponse(request, "vet_cabinet.html", {"user": user, "my_vets": db.query(Vet).filter(Vet.user_id == user.id).all(), "search_error": "Клієнта з таким ID не знайдено"})
    pets = db.query(Pet).filter(Pet.owner_id == client.id).all()
    return templates.TemplateResponse(request, "vet_client.html", {"user": user, "client": client, "pets": pets})

@app.get("/vet/pet/{pet_id}", response_class=HTMLResponse)
async def vet_pet_detail(request: Request, pet_id: int, appointment_id: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return RedirectResponse(url="/vet/cabinet")

    today = date.today()
    today_iso = today.isoformat()

    moods = db.query(Mood).filter(Mood.pet_id == pet_id).all()
    mood_by_date_str = {}
    for m in moods:
        if m.created_at:
            mood_by_date_str[m.created_at.date().isoformat()] = m.mood
    mood_emoji = {"жахливо": "😢", "погано": "😕", "нормально": "😐", "добре": "🙂", "дуже добре": "🤩"}

    appointments = db.query(Appointment).filter(Appointment.pet_id == pet_id).all()
    appointment_dates_str = []
    appointments_detail = {}
    for a in appointments:
        if a.date:
            ds = a.date.isoformat()
            appointment_dates_str.append(ds)
            appointments_detail[ds] = {
                "time": getattr(a, 'time', '') or "",
                "vet_name": a.vet.name if getattr(a, 'vet', None) else "",
                "clinic_address": a.clinic.address if getattr(a, 'clinic', None) else "",
                "complaint": getattr(a, 'complaint', '') or ""
            }

    visits = db.query(Visit).filter(Visit.pet_id == pet_id).all()
    visit_dates_str = []
    visits_detail = {}
    for v in visits:
        if getattr(v, 'date', None):
            ds = v.date.isoformat()
            visit_dates_str.append(ds)
            visits_detail[ds] = {
                "notes": getattr(v, 'notes', '') or "",
                "document": getattr(v, 'document', '') or ""
            }

    reminders = db.query(Reminder).filter(Reminder.pet_id == pet_id).all()
    reminder_by_date = {}
    for r in reminders:
        if r.date:
            ds = r.date.isoformat()
            reminder_by_date[ds] = {
                "text": getattr(r, 'text', '') or "",
                "type": getattr(r, 'reminder_type', 'routine') or "routine",
                "completed": getattr(r, 'completed', False)
            }

    weights = db.query(WeightEntry).filter(WeightEntry.pet_id == pet_id).all()
    weight_by_date = {}
    for w in weights:
        if w.date:
            ds = w.date.isoformat()
            weight_by_date[ds] = w.weight

    teeth = db.query(ToothCleaning).filter(ToothCleaning.pet_id == pet_id).all()
    tooth_dates = []
    for t in teeth:
        if getattr(t, 'date', None):
            tooth_dates.append(t.date.isoformat())

    latest_weight = None
    if weights:
        try:
            latest = max(weights, key=lambda w: w.date)
            latest_weight = f"{latest.weight} кг"
        except:
            pass

    complaint = None
    if appointment_id:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appt:
            complaint = getattr(appt, 'complaint', None)

    return templates.TemplateResponse(request, "vet_pet.html", {
        "user": user,
        "pet": pet,
        "appointment_id": request.query_params.get("appointment_id", 0),
        "complaint": complaint,
        "latest_weight": latest_weight,
        "today_iso": today_iso,
        "mood_by_date_str": mood_by_date_str,
        "mood_emoji": mood_emoji,
        "visit_dates_str": visit_dates_str,
        "appointment_dates_str": appointment_dates_str,
        "appointments_detail": appointments_detail,
        "visits_detail": visits_detail,
        "reminder_by_date": reminder_by_date,
        "weight_by_date": weight_by_date,
        "tooth_dates": tooth_dates
    })

@app.post("/vet/pet/{pet_id}/finish")
async def vet_finish_appointment(
    request: Request,
    pet_id: int,
    appointment_id: int = Form(0),
    notes: str = Form(...),
    document: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/login", status_code=303)

    appt = None
    if appointment_id and int(appointment_id) > 0:
        appt = db.query(Appointment).filter(Appointment.id == int(appointment_id)).first()
        if appt and appt.status == "done":
            return RedirectResponse(url="/vet/cabinet", status_code=303)

    visit = Visit(
        pet_id=pet_id,
        vet_id=user.id,
        date=date.today(),
        notes=notes
    )
    if document and document.filename:
        os.makedirs("static/visits", exist_ok=True)
        fn = f"{pet_id}_{int(datetime.now().timestamp())}_{document.filename}"
        path = f"static/visits/{fn}"
        with open(path, "wb") as f:
            f.write(await document.read())
        visit.document = "/" + path

    db.add(visit)
    if appt:
        appt.status = "done"
    db.commit()
    return RedirectResponse(url="/vet/cabinet", status_code=303)

@app.post("/vet/pet/{pet_id}/add-visit")
async def add_visit(request: Request, pet_id: int, date: str = Form(...), notes: str = Form(None), document: UploadFile = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/cabinet")
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return RedirectResponse(url="/vet/cabinet")
    my_vet = db.query(Vet).filter(Vet.user_id == user.id).first()
    doc_path = None
    if document and document.filename:
        ext = document.filename.split(".")[-1]
        filename = f"visit_{pet.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/visits/{filename}", "wb") as f:
            shutil.copyfileobj(document.file, f)
        doc_path = f"/static/visits/{filename}"
    visit_date = None
    try:
        visit_date = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        visit_date = date.today()
    visit = Visit(pet_id=pet.id, vet_id=my_vet.id if my_vet else None, clinic_id=my_vet.clinic_id if my_vet else None, date=visit_date, notes=notes, document=doc_path)
    db.add(visit)
    db.commit()
    return RedirectResponse(url=f"/vet/pet/{pet.id}", status_code=303)

@app.post("/vet/pet/{pet_id}/add-reminder")
async def add_reminder(request: Request, pet_id: int, date_from: str = Form(...), date_to: str = Form(...), text: str = Form(...), reminder_type: str = Form("routine"), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "vet":
        return RedirectResponse(url="/cabinet")
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return RedirectResponse(url="/vet/cabinet")
    my_vet = db.query(Vet).filter(Vet.user_id == user.id).first()
    try:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/vet/pet/{pet.id}")
    if end < start:
        start, end = end, start
    current = start
    while current <= end:
        reminder = Reminder(pet_id=pet.id, vet_id=my_vet.id if my_vet else None, date=current, text=text, reminder_type=reminder_type)
        db.add(reminder)
        current += timedelta(days=1)
    db.commit()
    return RedirectResponse(url=f"/vet/pet/{pet.id}", status_code=303)

@app.get("/vet/{vet_id}", response_class=HTMLResponse)
async def vet_public(request: Request, vet_id: int, year: int = None, month: int = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    vet = db.query(Vet).filter(Vet.id == vet_id).first()
    if not vet:
        return RedirectResponse(url="/clinics")
    clinic = db.query(Clinic).filter(Clinic.id == vet.clinic_id).first() if vet.clinic_id else None
    pets = db.query(Pet).filter(Pet.owner_id == user.id).all() if user else []
    today = date.today()
    if year is None: year = today.year
    if month is None: month = today.month
    apps = db.query(Appointment).filter(Appointment.vet_id == vet_id).all()
    booked = {}
    for a in apps:
        key = a.date.strftime("%Y-%m-%d")
        if key not in booked:
            booked[key] = []
        booked[key].append(a.time)
    return templates.TemplateResponse(request, "vet_public.html", {
        "user": user, "vet": vet, "clinic": clinic, "pets": pets, "year": year, "month": month, "booked": booked
    })

@app.post("/vet/{vet_id}/book")
async def book_appointment(
    request: Request,
    vet_id: int,
    pet_id: int = Form(...),
    date: str = Form(""),
    time: str = Form(""),
    complaint: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not date or not time:
        return RedirectResponse(url=f"/vet/{vet_id}", status_code=303)

    vet = db.query(Vet).filter(Vet.id == vet_id).first()
    if not vet:
        return RedirectResponse(url="/", status_code=303)

    existing = db.query(Appointment).filter(
        Appointment.vet_id == vet_id,
        Appointment.date == date,
        Appointment.time == time,
        Appointment.status != "cancelled"
    ).first()
    if existing:
        return RedirectResponse(url=f"/vet/{vet_id}?error=busy", status_code=303)

    appt = Appointment(
        user_id=user.id,
        vet_id=vet_id,
        pet_id=pet_id,
        date=date,
        time=time,
        complaint=complaint,
        status="pending"
    )
    db.add(appt)
    db.commit()
    return RedirectResponse(url="/cabinet", status_code=303)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.post("/register")
async def register(request: Request, full_name: str = Form(...), email: str = Form(None), phone: str = Form(None), password: str = Form(...), password2: str = Form(...), db: Session = Depends(get_db)):
    if password != password2:
        return templates.TemplateResponse(request, "register.html", {"error": "Паролі не співпадають"})
    if not email and not phone:
        return templates.TemplateResponse(request, "register.html", {"error": "Вкажіть пошту або телефон"})
    existing = None
    if email:
        existing = db.query(User).filter(User.email == email).first()
    if phone and not existing:
        existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        return templates.TemplateResponse(request, "register.html", {"error": "Такий користувач вже існує"})
    new_user = User(full_name=full_name, email=email, phone=phone, password=password, role="user")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/cabinet", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.post("/login")
async def login(request: Request, email: str = Form(None), phone: str = Form(None), password: str = Form(...), db: Session = Depends(get_db)):
    user = None
    if email:
        user = db.query(User).filter(User.email == email, User.password == password).first()
    if phone and not user:
        user = db.query(User).filter(User.phone == phone, User.password == password).first()
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Невірні дані для входу"})
    if user.is_blocked:
        return templates.TemplateResponse(request, "login.html", {"error": "Акаунт заблоковано"})
    request.session["user_id"] = user.id
    return RedirectResponse(url="/cabinet", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/cabinet", response_class=HTMLResponse)
async def cabinet(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
    return templates.TemplateResponse(request, "cabinet.html", {"user": user, "pets": pets})

@app.get("/pets", response_class=HTMLResponse)
async def pets_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
    return templates.TemplateResponse(request, "pets.html", {"user": user, "pets": pets})

@app.post("/mood")
async def save_mood(request: Request, pet_id: int = Form(...), mood: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if pet:
        db.add(Mood(pet_id=pet.id, mood=mood))
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/add-pet", response_class=HTMLResponse)
async def add_pet_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "add_pet.html")

@app.post("/add-pet")
async def add_pet(request: Request, name: str = Form(...), species: str = Form(...), breed: str = Form(None), birth_date: str = Form(None), gender: str = Form(None), medical_notes: str = Form(None), photo: UploadFile = File(None), medical_doc: UploadFile = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    photo_path = None
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"pet_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/pets/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/static/pets/{filename}"
    doc_path = None
    if medical_doc and medical_doc.filename:
        ext = medical_doc.filename.split(".")[-1]
        filename = f"med_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/medical/{filename}", "wb") as f:
            shutil.copyfileobj(medical_doc.file, f)
        doc_path = f"/static/medical/{filename}"
    birth = None
    if birth_date:
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except:
            pass
    db.add(Pet(owner_id=user.id, name=name, species=species, breed=breed, birth_date=birth, gender=gender, medical_notes=medical_notes, medical_doc=doc_path, photo=photo_path))
    db.commit()
    return RedirectResponse(url="/cabinet", status_code=303)

@app.get("/pet/{pet_id}", response_class=HTMLResponse)
async def pet_detail(request: Request, pet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    moods = db.query(Mood).filter(Mood.pet_id == pet.id).order_by(Mood.created_at.desc()).all()
    visits = db.query(Visit).filter(Visit.pet_id == pet.id).order_by(Visit.date.desc()).all()
    appointments = db.query(Appointment).filter(Appointment.pet_id == pet.id).all()
    reminders = db.query(Reminder).filter(Reminder.pet_id == pet.id).order_by(Reminder.date).all()
    weights = db.query(WeightEntry).filter(WeightEntry.pet_id == pet.id).all()
    teeth = db.query(ToothCleaning).filter(ToothCleaning.pet_id == pet.id).all()
    completions = db.query(ReminderCompletion).filter(ReminderCompletion.reminder_id.in_([r.id for r in reminders])).all() if reminders else []
    completed_ids = {c.reminder_id for c in completions if c.completed}
    mood_by_date_str = {}
    for m in moods:
        d = m.created_at.date().isoformat()
        if d not in mood_by_date_str:
            mood_by_date_str[d] = m.mood
    visit_dates_str = [v.date.isoformat() for v in visits]
    appointment_dates_str = [a.date.isoformat() for a in appointments]
    appointments_detail = {}
    for a in appointments:
        vet_name = ""
        clinic_address = ""
        if a.vet_id:
            vet = db.query(Vet).filter(Vet.id == a.vet_id).first()
            if vet:
                vet_name = vet.name or ""
                if vet.clinic_id:
                    clinic = db.query(Clinic).filter(Clinic.id == vet.clinic_id).first()
                    if clinic:
                        clinic_address = clinic.address or ""
        appointments_detail[a.date.isoformat()] = {
            "time": a.time,
            "complaint": a.complaint or "",
            "vet_name": vet_name,
            "clinic_address": clinic_address
        }
    visits_detail = {}
    for v in visits:
        visits_detail[v.date.isoformat()] = {
            "notes": v.notes or "",
            "document": v.document or ""
        }
    reminder_by_date = {}
    for r in reminders:
        reminder_by_date[r.date.isoformat()] = {
            "text": r.text or "",
            "type": r.reminder_type,
            "completed": r.id in completed_ids
        }
    weight_by_date = {}
    for w in weights:
        weight_by_date[w.date.isoformat()] = w.weight
    tooth_dates = [t.date.isoformat() for t in teeth]
    latest_weight = None
    if weights:
        latest = max(weights, key=lambda x: x.date)
        latest_weight = f"{latest.weight} кг"
    streak = 0
    check = date.today()
    while check.isoformat() in mood_by_date_str:
        streak += 1
        check -= timedelta(days=1)
    return templates.TemplateResponse(request, "pet_detail.html", {
        "user": user,
        "pet": pet,
        "mood_by_date_str": mood_by_date_str,
        "visit_dates_str": visit_dates_str,
        "appointment_dates_str": appointment_dates_str,
        "appointments_detail": appointments_detail,
        "visits_detail": visits_detail,
        "reminder_by_date": reminder_by_date,
        "weight_by_date": weight_by_date,
        "tooth_dates": tooth_dates,
        "mood_emoji": MOOD_EMOJI,
        "streak": streak,
        "today_iso": date.today().isoformat(),
        "latest_weight": latest_weight
    })

@app.post("/pet/{pet_id}/mark-no-show")
async def mark_no_show(request: Request, pet_id: int, date_str: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    try:
        app_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/pet/{pet_id}")
    app = db.query(Appointment).filter(Appointment.pet_id == pet.id, Appointment.date == app_date).first()
    if app:
        db.delete(app)
        db.commit()
    return RedirectResponse(url=f"/pet/{pet_id}", status_code=303)

@app.post("/pet/{pet_id}/complete-reminder")
async def complete_reminder(request: Request, pet_id: int, date_str: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    try:
        r_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/pet/{pet_id}")
    reminder = db.query(Reminder).filter(Reminder.pet_id == pet.id, Reminder.date == r_date).first()
    if reminder:
        existing = db.query(ReminderCompletion).filter(ReminderCompletion.reminder_id == reminder.id).first()
        if not existing:
            db.add(ReminderCompletion(reminder_id=reminder.id, completed=True, completed_at=datetime.utcnow()))
            db.commit()
    return RedirectResponse(url=f"/pet/{pet_id}", status_code=303)

@app.post("/pet/{pet_id}/add-weight")
async def add_weight(request: Request, pet_id: int, date_str: str = Form(...), weight: float = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    try:
        w_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/pet/{pet_id}")
    db.add(WeightEntry(pet_id=pet.id, date=w_date, weight=weight))
    db.commit()
    return RedirectResponse(url=f"/pet/{pet_id}", status_code=303)

@app.post("/pet/{pet_id}/add-tooth")
async def add_tooth(request: Request, pet_id: int, date_str: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    try:
        t_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/pet/{pet_id}")
    db.add(ToothCleaning(pet_id=pet.id, date=t_date))
    db.commit()
    return RedirectResponse(url=f"/pet/{pet_id}", status_code=303)

@app.post("/pet/{pet_id}/add-reminder")
async def add_pet_reminder(request: Request, pet_id: int, date_from: str = Form(...), date_to: str = Form(...), text: str = Form(...), reminder_type: str = Form("routine"), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    try:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    except:
        return RedirectResponse(url=f"/pet/{pet_id}")
    if end < start:
        start, end = end, start
    current = start
    while current <= end:
        db.add(Reminder(pet_id=pet.id, date=current, text=text, reminder_type=reminder_type))
        current += timedelta(days=1)
    db.commit()
    return RedirectResponse(url=f"/pet/{pet_id}", status_code=303)

@app.get("/pet/{pet_id}/edit", response_class=HTMLResponse)
async def edit_pet_page(request: Request, pet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    return templates.TemplateResponse(request, "edit_pet.html", {"pet": pet})

@app.post("/pet/{pet_id}/edit")
async def edit_pet(request: Request, pet_id: int, name: str = Form(...), species: str = Form(...), breed: str = Form(None), birth_date: str = Form(None), gender: str = Form(None), medical_notes: str = Form(None), photo: UploadFile = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if not pet:
        return RedirectResponse(url="/cabinet")
    pet.name, pet.species, pet.breed, pet.gender, pet.medical_notes = name, species, breed, gender, medical_notes
    if birth_date:
        try:
            pet.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except:
            pass
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"pet_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/pets/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        pet.photo = f"/static/pets/{filename}"
    db.commit()
    return RedirectResponse(url=f"/pet/{pet.id}", status_code=303)

@app.get("/pet/{pet_id}/delete")
async def delete_pet(request: Request, pet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
    if pet:
        db.delete(pet)
        db.commit()
    return RedirectResponse(url="/cabinet", status_code=303)

@app.get("/clinics", response_class=HTMLResponse)
async def clinics_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    approved = db.query(Clinic).filter(Clinic.status == "approved").all()
    my_clinic = None
    if user:
        my_clinic = db.query(Clinic).filter(Clinic.owner_id == user.id).first()
    return templates.TemplateResponse(request, "clinics.html", {"user": user, "clinics": approved, "my_clinic": my_clinic})

@app.get("/clinics/register", response_class=HTMLResponse)
async def clinic_register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    existing = db.query(Clinic).filter(Clinic.owner_id == user.id).first()
    if existing and existing.status != "rejected":
        return RedirectResponse(url="/clinics")
    return templates.TemplateResponse(request, "register_clinic.html", {"user": user, "error": None})

@app.post("/clinics/register")
async def clinic_register(request: Request, name: str = Form(...), clinic_type: str = Form(...), district: str = Form(...), street: str = Form(...), house: str = Form(...), phone: str = Form(...), owner_phone: str = Form(...), email: str = Form(...), description: str = Form(...), work_from: str = Form(...), work_to: str = Form(...), weekend_from: str = Form(None), weekend_to: str = Form(None), weekend_off: str = Form(None), terms: str = Form(None), photo: UploadFile = File(...), documents: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    if not terms:
        return templates.TemplateResponse(request, "register_clinic.html", {"user": user, "error": "Потрібно прийняти умови співпраці"})
    existing = db.query(Clinic).filter(Clinic.owner_id == user.id).first()
    if existing and existing.status == "rejected":
        clinic = existing
    else:
        clinic = Clinic(owner_id=user.id)
        db.add(clinic)
    work_hours = f"Будні: {work_from}–{work_to}"
    if weekend_off:
        work_hours += "; Вихідні: не працюємо"
    elif weekend_from and weekend_to:
        work_hours += f"; Вихідні: {weekend_from}–{weekend_to}"
    clinic.name = name
    clinic.district = district
    clinic.street = street
    clinic.house = house
    clinic.address = f"м. Київ, {district} район, {street}, {house}"
    clinic.phone = phone
    clinic.owner_phone = owner_phone
    clinic.email = email
    clinic.description = description
    clinic.work_hours = work_hours
    clinic.status = "pending"
    clinic.terms_accepted = True
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"clinic_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/clinics/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        clinic.photo = f"/static/clinics/{filename}"
    if documents and documents.filename:
        ext = documents.filename.split(".")[-1]
        filename = f"docs_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/clinic_docs/{filename}", "wb") as f:
            shutil.copyfileobj(documents.file, f)
        clinic.documents = f"/static/clinic_docs/{filename}"
    db.commit()
    return RedirectResponse(url="/clinics?sent=1", status_code=303)

@app.get("/clinics/{clinic_id}", response_class=HTMLResponse)
async def clinic_public(request: Request, clinic_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id, Clinic.status == "approved").first()
    if not clinic:
        return RedirectResponse(url="/clinics")
    vets = []
    if clinic.show_vets:
        vets = db.query(Vet).filter(Vet.clinic_id == clinic.id).all()
    grouped = {}
    for v in vets:
        spec = v.specialty or "Інше"
        if spec not in grouped:
            grouped[spec] = []
        grouped[spec].append(v)
    return templates.TemplateResponse(request, "clinic_public.html", {"user": user, "clinic": clinic, "grouped_vets": grouped})

@app.get("/clinic/cabinet", response_class=HTMLResponse)
async def clinic_cabinet(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic or clinic.status != "approved":
        return RedirectResponse(url="/clinics")
    vets = db.query(Vet).filter(Vet.clinic_id == clinic.id).all()
    managers = db.query(ClinicManager).filter(ClinicManager.clinic_id == clinic.id).all()
    return templates.TemplateResponse(request, "clinic_cabinet.html", {
        "user": user,
        "clinic": clinic,
        "vets": vets,
        "managers": managers
    })

@app.post("/clinic/update")
async def clinic_update(request: Request, name: str = Form(...), address: str = Form(...), phone: str = Form(...), email: str = Form(None), description: str = Form(None), work_hours: str = Form(None), is_24h: str = Form(None), has_online_booking: str = Form(None), show_vets: str = Form(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic or clinic.status != "approved":
        return RedirectResponse(url="/clinics")
    clinic.name = name
    clinic.address = address
    clinic.phone = phone
    clinic.email = email
    clinic.description = description
    clinic.work_hours = work_hours
    clinic.is_24h = bool(is_24h)
    clinic.has_online_booking = bool(has_online_booking)
    clinic.show_vets = bool(show_vets)
    db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.post("/clinic/add-vet")
async def add_vet(request: Request, specialty: str = Form(...), animal_type: str = Form(...), description: str = Form(...), photo: UploadFile = File(...), experience: str = Form(None), service: str = Form(None), phone: str = Form(None), price: str = Form(...), user_id: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic or clinic.status != "approved":
        return RedirectResponse(url="/clinics")
    error = None
    uid = None
    try:
        uid = int(user_id)
    except:
        error = "Невірний ID"
    vet_user = None
    if not error and uid:
        vet_user = db.query(User).filter(User.id == uid).first()
        if not vet_user:
            error = "Користувача з таким ID не знайдено"
    if not error and uid:
        existing_vet = db.query(Vet).filter(Vet.clinic_id == clinic.id, Vet.user_id == uid).first()
        if existing_vet:
            error = "Цей лікар уже доданий до клініки"
    if error:
        vets = db.query(Vet).filter(Vet.clinic_id == clinic.id).all()
        return templates.TemplateResponse(request, "clinic_cabinet.html", {"user": user, "clinic": clinic, "vets": vets, "error": error})
    if vet_user and vet_user.role not in ["admin", "clinic_owner"]:
        vet_user.role = "vet"
    price_val = None
    if price:
        try:
            price_val = float(price)
        except:
            price_val = None
    clean_phone = None
    if phone:
        digits = phone.replace(" ", "").replace("+", "")
        if digits and digits != "380":
            clean_phone = phone.strip()
    photo_path = None
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"vet_{clinic.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/vets/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/static/vets/{filename}"
    vet_name = vet_user.full_name if vet_user and vet_user.full_name else f"Лікар #{uid}"
    vet = Vet(clinic_id=clinic.id, user_id=uid, name=vet_name, specialty=specialty, animal_type=animal_type, service=service if service else None, phone=clean_phone, price=price_val, description=description, experience=experience if experience else None, photo=photo_path)
    db.add(vet)
    db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.post("/clinic/delete-vet/{vet_id}")
async def delete_vet(request: Request, vet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic:
        return RedirectResponse(url="/clinics")
    vet = db.query(Vet).filter(Vet.id == vet_id, Vet.clinic_id == clinic.id).first()
    if vet:
        other = db.query(Vet).filter(Vet.user_id == vet.user_id, Vet.id != vet.id).first()
        if not other and vet.user_id:
            vet_user = db.query(User).filter(User.id == vet.user_id).first()
            if vet_user and vet_user.role == "vet":
                vet_user.role = "user"
        db.delete(vet)
        db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.get("/clinic/vet/{vet_id}/edit", response_class=HTMLResponse)
async def edit_vet_page(request: Request, vet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic:
        return RedirectResponse(url="/clinics")
    vet = db.query(Vet).filter(Vet.id == vet_id, Vet.clinic_id == clinic.id).first()
    if not vet:
        return RedirectResponse(url="/clinic/cabinet")
    return templates.TemplateResponse(request, "edit_vet.html", {"user": user, "clinic": clinic, "vet": vet})

@app.post("/clinic/vet/{vet_id}/edit")
async def edit_vet(request: Request, vet_id: int, specialty: str = Form(...), animal_type: str = Form(...), service: str = Form(None), phone: str = Form(None), price: str = Form(...), description: str = Form(None), experience: str = Form(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    clinic = get_my_clinic(user, db)
    if not clinic:
        return RedirectResponse(url="/clinics")
    vet = db.query(Vet).filter(Vet.id == vet_id, Vet.clinic_id == clinic.id).first()
    if not vet:
        return RedirectResponse(url="/clinic/cabinet")
    price_val = None
    if price:
        try:
            price_val = float(price)
        except:
            price_val = None
    clean_phone = None
    if phone:
        digits = phone.replace(" ", "").replace("+", "")
        if digits and digits != "380":
            clean_phone = phone.strip()
    vet.specialty = specialty
    vet.animal_type = animal_type
    vet.service = service if service else None
    vet.phone = clean_phone
    vet.price = price_val
    vet.description = description if description else None
    vet.experience = experience if experience else None
    db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.get("/pharmacies", response_class=HTMLResponse)
async def pharmacies_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    approved = db.query(Pharmacy).filter(Pharmacy.status == "approved").all()
    return templates.TemplateResponse(request, "pharmacies.html", {"user": user, "pharmacies": approved})

@app.get("/pharmacies/register", response_class=HTMLResponse)
async def pharmacy_register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    existing = db.query(Pharmacy).filter(Pharmacy.owner_id == user.id).first()
    if existing and existing.status != "rejected":
        return RedirectResponse(url="/pharmacies")
    return templates.TemplateResponse(request, "register_pharmacy.html", {"user": user, "error": None})

@app.post("/pharmacies/register")
async def pharmacy_register(request: Request, name: str = Form(...), district: str = Form(...), street: str = Form(...), phone: str = Form(...), owner_phone: str = Form(...), email: str = Form(...), description: str = Form(...), work_from: str = Form(...), work_to: str = Form(...), weekend_from: str = Form(None), weekend_to: str = Form(None), photo: UploadFile = File(...), documents: UploadFile = File(...), edrpou: str = Form(...), edrpou_doc: UploadFile = File(...), terms: str = Form(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    if not terms:
        return templates.TemplateResponse(request, "register_pharmacy.html", {"user": user, "error": "Потрібно прийняти умови співпраці"})
    existing = db.query(Pharmacy).filter(Pharmacy.owner_id == user.id).first()
    if existing and existing.status == "rejected":
        pharmacy = existing
    else:
        pharmacy = Pharmacy(owner_id=user.id)
        db.add(pharmacy)
    full_hours = f"Будні: {work_from}–{work_to}"
    if weekend_from and weekend_to:
        full_hours += f"; Вихідні: {weekend_from}–{weekend_to}"
    else:
        full_hours += "; Вихідні: не працюємо"
    pharmacy.name = name
    pharmacy.district = district
    pharmacy.street = street
    pharmacy.phone = phone
    pharmacy.owner_phone = owner_phone
    pharmacy.email = email
    pharmacy.description = description
    pharmacy.work_hours = full_hours
    pharmacy.edrpou = edrpou
    pharmacy.status = "pending"
    pharmacy.terms_accepted = True
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"pharm_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/pharmacies/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        pharmacy.photo = f"/static/pharmacies/{filename}"
    if documents and documents.filename:
        ext = documents.filename.split(".")[-1]
        filename = f"pharmdocs_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/pharmacy_docs/{filename}", "wb") as f:
            shutil.copyfileobj(documents.file, f)
        pharmacy.documents = f"/static/pharmacy_docs/{filename}"
    db.commit()
    return RedirectResponse(url="/pharmacies?sent=1", status_code=303)

@app.get("/pharmacy/cabinet", response_class=HTMLResponse)
async def pharmacy_cabinet(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pharmacy = get_my_pharmacy(user, db)
    if not pharmacy or pharmacy.status != "approved":
        return RedirectResponse(url="/pharmacies")
    pps = db.query(PharmacyProduct).filter(PharmacyProduct.pharmacy_id == pharmacy.id).all()
    products = []
    for pp in pps:
        prod = db.query(Product).filter(Product.id == pp.product_id).first()
        if prod:
            products.append({
                "pp_id": pp.id,
                "name": prod.name,
                "price": pp.price,
                "quantity": pp.quantity,
                "added": pp.created_at.strftime("%d.%m.%Y") if pp.created_at else ""
            })
    catalog = db.query(Product).all()
    return templates.TemplateResponse(request, "pharmacy_cabinet.html", {
        "user": user, "pharmacy": pharmacy, "products": products, "catalog": catalog,
        "products_json": json.dumps(products)
    })

@app.post("/pharmacy/add-product")
async def pharmacy_add_product(request: Request, product_id: int = Form(...), price: float = Form(...), quantity: int = Form(0), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pharmacy = get_my_pharmacy(user, db)
    if not pharmacy or pharmacy.status != "approved":
        return RedirectResponse(url="/pharmacies")
    existing = db.query(PharmacyProduct).filter(PharmacyProduct.pharmacy_id == pharmacy.id, PharmacyProduct.product_id == product_id).first()
    if existing:
        existing.price = price
        existing.quantity = quantity
    else:
        db.add(PharmacyProduct(pharmacy_id=pharmacy.id, product_id=product_id, price=price, quantity=quantity))
    db.commit()
    return RedirectResponse(url="/pharmacy/cabinet", status_code=303)

@app.post("/pharmacy/update-product")
async def pharmacy_update_product(request: Request, pp_id: int = Form(...), price: float = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pharmacy = get_my_pharmacy(user, db)
    if not pharmacy:
        return RedirectResponse(url="/pharmacies")
    pp = db.query(PharmacyProduct).filter(PharmacyProduct.id == pp_id, PharmacyProduct.pharmacy_id == pharmacy.id).first()
    if pp:
        pp.price = price
        pp.quantity = quantity
        db.commit()
    return RedirectResponse(url="/pharmacy/cabinet", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not require_admin(user):
        return RedirectResponse(url="/cabinet")
    users = db.query(User).order_by(User.id).all()
    clinics = db.query(Clinic).order_by(Clinic.created_at.desc()).all()
    pharmacies = db.query(Pharmacy).order_by(Pharmacy.created_at.desc()).all()
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    users_data = []
    for u in users:
        clinic_name = None
        if u.role == "clinic_owner":
            cl = db.query(Clinic).filter(Clinic.owner_id == u.id).first()
            if cl:
                clinic_name = cl.name
        users_data.append({
            "id": u.id,
            "email": u.email,
            "phone": u.phone,
            "full_name": u.full_name,
            "role": u.role,
            "is_blocked": u.is_blocked,
            "clinic_name": clinic_name
        })
    clinics_data = []
    for c in clinics:
        clinics_data.append({
            "id": c.id,
            "name": c.name,
            "address": c.address,
            "phone": c.phone,
            "status": c.status,
            "owner_id": c.owner_id
        })
    pharmacies_data = []
    for p in pharmacies:
        pharmacies_data.append({
            "id": p.id,
            "name": p.name,
            "street": p.street,
            "phone": p.phone,
            "status": p.status,
            "owner_id": p.owner_id
        })
    products_data = []
    for p in products:
        products_data.append({
            "id": p.id,
            "name": p.name,
            "form": p.form,
            "volume": p.volume,
            "manufacturer": p.manufacturer
        })
    return templates.TemplateResponse(request, "admin.html", {
        "user": user,
        "users_json": json.dumps(users_data),
        "clinics_json": json.dumps(clinics_data),
        "pharmacies_json": json.dumps(pharmacies_data),
        "products_json": json.dumps(products_data)
    })

@app.get("/admin/clinic/{clinic_id}", response_class=HTMLResponse)
async def admin_clinic_detail(request: Request, clinic_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not require_admin(user):
        return RedirectResponse(url="/cabinet")
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        return RedirectResponse(url="/admin")
    return templates.TemplateResponse(request, "admin_clinic_detail.html", {"user": user, "clinic": clinic})

@app.get("/admin/pharmacy/{pharmacy_id}", response_class=HTMLResponse)
async def admin_pharmacy_detail(request: Request, pharmacy_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not require_admin(user):
        return RedirectResponse(url="/cabinet")
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
    if not pharmacy:
        return RedirectResponse(url="/admin")
    return templates.TemplateResponse(request, "admin_pharmacy_detail.html", {"user": user, "pharmacy": pharmacy})

@app.get("/admin/product/{product_id}", response_class=HTMLResponse)
async def admin_product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not require_admin(user):
        return RedirectResponse(url="/cabinet")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/admin")
    return templates.TemplateResponse(request, "admin_product_detail.html", {"user": user, "product": product})

@app.post("/admin/set-role")
async def admin_set_role(request: Request, user_id: int = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    if role in ["user", "clinic_owner", "vet", "pharmacy_owner", "shop_owner", "admin", "moderator", "seller"]:
        target = db.query(User).filter(User.id == user_id).first()
        if target:
            target.role = role
            db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/block-user")
async def admin_block_user(request: Request, user_id: int = Form(...), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    target = db.query(User).filter(User.id == user_id).first()
    if target and target.id != admin.id:
        target.is_blocked = not target.is_blocked
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/clinic-status")
async def admin_clinic_status(request: Request, clinic_id: int = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if clinic and status in ["pending", "approved", "rejected", "blocked"]:
        clinic.status = status
        if status == "approved" and clinic.owner_id:
            owner = db.query(User).filter(User.id == clinic.owner_id).first()
            if owner and owner.role not in ["admin", "clinic_owner"]:
                owner.role = "clinic_owner"
        if status in ["rejected", "blocked"] and clinic.owner_id:
            owner = db.query(User).filter(User.id == clinic.owner_id).first()
            if owner and owner.role == "clinic_owner":
                owner.role = "user"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/pharmacy-status")
async def admin_pharmacy_status(request: Request, pharmacy_id: int = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
    if pharmacy and status in ["pending", "approved", "rejected", "blocked"]:
        pharmacy.status = status
        if status == "approved" and pharmacy.owner_id:
            owner = db.query(User).filter(User.id == pharmacy.owner_id).first()
            if owner and owner.role not in ["admin", "pharmacy_owner"]:
                owner.role = "pharmacy_owner"
        if status in ["rejected", "blocked"] and pharmacy.owner_id:
            owner = db.query(User).filter(User.id == pharmacy.owner_id).first()
            if owner and owner.role == "pharmacy_owner":
                owner.role = "user"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/add-product")
async def admin_add_product(request: Request, name: str = Form(...), form: str = Form(...), animal_type: str = Form(None), weight_from: str = Form(None), weight_to: str = Form(None), volume_num: str = Form(None), volume_unit: str = Form(None), manufacturer: str = Form(None), description: str = Form(None), photo: UploadFile = File(None), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    photo_path = None
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"prod_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/products/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/static/products/{filename}"
    volume = None
    if volume_num and volume_unit:
        volume = f"{volume_num} {volume_unit}"
    product = Product(name=name, form=form, animal_type=animal_type, weight_from=weight_from, weight_to=weight_to, volume=volume, manufacturer=manufacturer, description=description, photo=photo_path)
    db.add(product)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/delete-product")
async def admin_delete_product(request: Request, product_id: int = Form(...), db: Session = Depends(get_db)):
    admin = get_current_user(request, db)
    if not require_admin(admin):
        return RedirectResponse(url="/cabinet")
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/pharmacy/{pharmacy_id}", response_class=HTMLResponse)
async def pharmacy_public(request: Request, pharmacy_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id, Pharmacy.status == "approved").first()
    if not pharmacy:
        return RedirectResponse(url="/pharmacies")
    pps = db.query(PharmacyProduct).filter(PharmacyProduct.pharmacy_id == pharmacy.id).all()
    products = []
    for pp in pps:
        prod = db.query(Product).filter(Product.id == pp.product_id).first()
        if prod:
            products.append({
                "id": prod.id,
                "name": prod.name,
                "form": prod.form,
                "volume": prod.volume,
                "photo": prod.photo,
                "price": pp.price
            })
    return templates.TemplateResponse(request, "pharmacy_public.html", {
        "user": user,
        "pharmacy": pharmacy,
        "products": products,
        "products_json": json.dumps(products)
    })

@app.get("/pharmacy/{pharmacy_id}/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, pharmacy_id: int, product_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id, Pharmacy.status == "approved").first()
    if not pharmacy:
        return RedirectResponse(url="/pharmacies")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return RedirectResponse(url=f"/pharmacy/{pharmacy_id}")
    pp = db.query(PharmacyProduct).filter(PharmacyProduct.pharmacy_id == pharmacy_id, PharmacyProduct.product_id == product_id).first()
    price = pp.price if pp else 0
    return templates.TemplateResponse(request, "product_detail.html", {
        "user": user,
        "pharmacy": pharmacy,
        "product": product,
        "price": price
    })

@app.post("/pharmacy/update")
async def pharmacy_update(request: Request, phone: str = Form(None), description: str = Form(None), work_hours: str = Form(None), photo: UploadFile = File(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pharmacy = get_my_pharmacy(user, db)
    if not pharmacy:
        return RedirectResponse(url="/pharmacies")
    if phone:
        pharmacy.phone = phone
    if description is not None:
        pharmacy.description = description
    if work_hours:
        pharmacy.work_hours = work_hours
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        filename = f"pharm_{pharmacy.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(f"static/pharmacies/{filename}", "wb") as f:
            shutil.copyfileobj(photo.file, f)
        pharmacy.photo = f"/static/pharmacies/{filename}"
    db.commit()
    return RedirectResponse(url="/pharmacy/cabinet", status_code=303)

@app.get("/pharmacy/product/{pp_id}", response_class=HTMLResponse)
async def pharmacy_product_detail(request: Request, pp_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    pp = db.query(PharmacyProduct).filter(PharmacyProduct.id == pp_id).first()
    if not pp:
        return RedirectResponse(url="/pharmacy/cabinet")
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pp.pharmacy_id).first()
    if not pharmacy or pharmacy.owner_id != user.id:
        return RedirectResponse(url="/pharmacy/cabinet")
    product = db.query(Product).filter(Product.id == pp.product_id).first()
    return templates.TemplateResponse(request, "pharmacy_product.html", {
        "user": user, "pharmacy": pharmacy, "product": product, "pp": pp
    })

@app.post("/book")
async def book_appointment(request: Request, vet_id: int = Form(...), date: str = Form(...), time: str = Form(...), pet_id: int = Form(None), complaint: str = Form(None), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    book_date = datetime.strptime(date, "%Y-%m-%d").date()
    existing = db.query(Appointment).filter(
        Appointment.vet_id == vet_id,
        Appointment.date == book_date,
        Appointment.time == time,
        Appointment.status != "done"
    ).first()
    if existing:
        return RedirectResponse(url=f"/vet/{vet_id}?error=busy", status_code=303)
    appointment = Appointment(vet_id=vet_id, user_id=user.id, pet_id=pet_id, date=book_date, time=time, complaint=complaint)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    vet = db.query(Vet).filter(Vet.id == vet_id).first()
    pet = db.query(Pet).filter(Pet.id == pet_id).first() if pet_id else None
    return templates.TemplateResponse(request, "booking_success.html", {
        "user": user,
        "appointment": appointment,
        "vet": vet,
        "pet": pet,
        "complaint": complaint or ""
    })

@app.post("/clinic/add-manager")
async def add_manager(
    request: Request,
    user_id: int = Form(...),
    can_edit_clinic: bool = Form(False),
    can_manage_vets: bool = Form(False),
    can_view_schedule: bool = Form(False),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    clinic = db.query(Clinic).filter(Clinic.owner_id == user.id).first()
    if not clinic:
        return RedirectResponse(url="/cabinet", status_code=303)
    
    existing = db.query(ClinicManager).filter(ClinicManager.clinic_id == clinic.id).count()
    if existing >= 3:
        return RedirectResponse(url="/clinic/cabinet", status_code=303)
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/clinic/cabinet", status_code=303)

    if target_user.role and target_user.role != "user":
        return RedirectResponse(url="/clinic/cabinet?error=busy", status_code=303)

    already = db.query(ClinicManager).filter(
        ClinicManager.clinic_id == clinic.id,
        ClinicManager.user_id == user_id
    ).first()
    if already:
        return RedirectResponse(url="/clinic/cabinet", status_code=303)
    
    manager = ClinicManager(
        clinic_id=clinic.id,
        user_id=user_id,
        can_edit_clinic=can_edit_clinic,
        can_manage_vets=can_manage_vets,
        can_view_schedule=can_view_schedule
    )
    db.add(manager)
    target_user.role = "clinic_manager"
    db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.get("/clinic/edit-manager/{manager_id}", response_class=HTMLResponse)
async def edit_manager_page(request: Request, manager_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    manager = db.query(ClinicManager).filter(ClinicManager.id == manager_id).first()
    if not manager or manager.clinic.owner_id != user.id:
        return RedirectResponse(url="/clinic/cabinet")
    return templates.TemplateResponse(request, "edit_manager.html", {"user": user, "manager": manager})
@app.post("/clinic/delete-manager/{manager_id}")
async def delete_manager(request: Request, manager_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    manager = db.query(ClinicManager).filter(ClinicManager.id == manager_id).first()
    if manager and manager.clinic.owner_id == user.id:
        db.delete(manager)
        db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.post("/clinic/update-manager/{manager_id}")
async def update_manager(
    request: Request,
    manager_id: int,
    can_edit_clinic: bool = Form(False),
    can_manage_vets: bool = Form(False),
    can_view_schedule: bool = Form(False),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    manager = db.query(ClinicManager).filter(ClinicManager.id == manager_id).first()
    if not manager or manager.clinic.owner_id != user.id:
        return RedirectResponse(url="/clinic/cabinet")
    manager.can_edit_clinic = can_edit_clinic
    manager.can_manage_vets = can_manage_vets
    manager.can_view_schedule = can_view_schedule
    db.commit()
    return RedirectResponse(url="/clinic/cabinet", status_code=303)

@app.get("/manager/cabinet", response_class=HTMLResponse)
async def manager_cabinet(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "clinic_manager":
        return RedirectResponse(url="/cabinet", status_code=303)
    
    manager = db.query(ClinicManager).filter(ClinicManager.user_id == user.id).first()
    if not manager:
        return RedirectResponse(url="/cabinet", status_code=303)
    
    clinic = db.query(Clinic).filter(Clinic.id == manager.clinic_id).first()
    vets = db.query(Vet).filter(Vet.clinic_id == clinic.id).all() if clinic else []
    
    return templates.TemplateResponse(request, "manager_cabinet.html", {
        "user": user,
        "manager": manager,
        "clinic": clinic,
        "vets": vets
    })

@app.get("/manager/schedule/{vet_id}", response_class=HTMLResponse)
async def manager_vet_schedule(request: Request, vet_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")

    manager = db.query(ClinicManager).filter(ClinicManager.user_id == user.id).first()
    if not manager or not manager.can_view_schedule:
        return RedirectResponse(url="/cabinet")

    vet = db.query(Vet).filter(Vet.id == vet_id, Vet.clinic_id == manager.clinic_id).first()
    if not vet:
        return RedirectResponse(url="/manager/cabinet")

    # Беремо всі записи цього лікаря
    appointments = db.query(Appointment).filter(Appointment.vet_id == vet.id).order_by(Appointment.date, Appointment.time).all()

    return templates.TemplateResponse(request, "manager_schedule.html", {
        "user": user,
        "vet": vet,
        "clinic": manager.clinic,
        "appointments": appointments
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)