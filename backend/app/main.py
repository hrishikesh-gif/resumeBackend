from fastapi import FastAPI
from .database import engine
from .database import Base
from . import models

app = FastAPI()

# Create tables automatically
# Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Backend is running successfully 🚀"}
