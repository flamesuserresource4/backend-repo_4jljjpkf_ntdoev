import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Course, Lesson, Enrollment, Progress, User

app = FastAPI(title="LMS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "LMS Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# ----- Simple CRUD endpoints for LMS -----

class CourseCreate(Course):
    pass

class LessonCreate(Lesson):
    pass

class EnrollmentCreate(Enrollment):
    pass

class ProgressCreate(Progress):
    pass

@app.post("/api/courses")
def create_course(course: CourseCreate):
    course_id = create_document("course", course)
    return {"id": course_id}

@app.get("/api/courses")
def list_courses():
    items = get_documents("course")
    for i in items:
        i["id"] = str(i.get("_id"))
        i.pop("_id", None)
    return items

@app.post("/api/lessons")
def create_lesson(lesson: LessonCreate):
    if not ObjectId.is_valid(lesson.course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    lesson_id = create_document("lesson", lesson)
    return {"id": lesson_id}

@app.get("/api/lessons")
def list_lessons(course_id: str):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    items = get_documents("lesson", {"course_id": course_id})
    for i in items:
        i["id"] = str(i.get("_id"))
        i.pop("_id", None)
    return items

@app.post("/api/enrollments")
def enroll(enrollment: EnrollmentCreate):
    if not ObjectId.is_valid(enrollment.course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    enrollment_id = create_document("enrollment", enrollment)
    return {"id": enrollment_id}

@app.get("/api/enrollments")
def list_enrollments(user_email: EmailStr):
    items = get_documents("enrollment", {"user_email": user_email})
    for i in items:
        i["id"] = str(i.get("_id"))
        i.pop("_id", None)
    return items

@app.post("/api/progress")
def track_progress(progress: ProgressCreate):
    if not ObjectId.is_valid(progress.course_id) or not ObjectId.is_valid(progress.lesson_id):
        raise HTTPException(status_code=400, detail="Invalid ids")
    progress_id = create_document("progress", progress)
    return {"id": progress_id}

@app.get("/api/progress")
def get_progress(user_email: EmailStr, course_id: str):
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=400, detail="Invalid course_id")
    items = get_documents("progress", {"user_email": user_email, "course_id": course_id})
    for i in items:
        i["id"] = str(i.get("_id"))
        i.pop("_id", None)
    return items


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
