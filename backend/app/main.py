from fastapi import FastAPI
from .database import engine
from .models import Base

app = FastAPI()

# Create tables automatically
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Backend is running successfully 🚀"}
