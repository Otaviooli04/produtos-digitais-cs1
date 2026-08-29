from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.exam import router as exam_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.student import router as student_router
from app.api.routes.student_activity import router as student_activity_router
from app.api.routes.submission import router as submission_router
from app.api.routes.turma import router as turma_router
from app.auth.routes import router as auth_router

app = FastAPI(title="Learning Analytics — CS1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(exam_router)
app.include_router(jobs_router)
app.include_router(student_router)
app.include_router(student_activity_router)
app.include_router(submission_router)
app.include_router(turma_router)


@app.get("/")
async def health_check():
    return {"status": "online", "system": "Learning Analytics CS1"}
