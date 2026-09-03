from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.payment import Payment

from app.api.payments import router as payments_router
from app.api.recovery import router as recovery_router
from app.api.analytics import router as analytics_router
from app.api.audit import router as audit_router
from app.api.evaluation import router as evaluation_router
from app.models.recovery_event import RecoveryEvent
from app.api.razorpay import (
    router as razorpay_router,
)
from app.api.webhooks import router as webhooks_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery platform",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://recover-ai-jet.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(payments_router)
app.include_router(recovery_router)
app.include_router(analytics_router)
app.include_router(audit_router)
app.include_router(evaluation_router)
app.include_router(
    razorpay_router
)
app.include_router(
    webhooks_router
)

@app.get("/")
def root():
    return {
        "message": "RecoverAI API is running 🚀"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }