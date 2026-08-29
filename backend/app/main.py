from fastapi import FastAPI

from app.database.database import Base, engine

from app.models.customer import Customer
from app.models.payment import Payment

from app.api.payments import router as payments_router
from app.api.recovery import router as recovery_router
from app.api.analytics import router as analytics_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery platform",
    version="1.0.0",
)


app.include_router(payments_router)
app.include_router(recovery_router)
app.include_router(analytics_router)


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