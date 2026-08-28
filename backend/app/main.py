from fastapi import FastAPI

app = FastAPI(
    title="RecoverAI",
    description="AI-powered revenue recovery platform",
    version="1.0.0",
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