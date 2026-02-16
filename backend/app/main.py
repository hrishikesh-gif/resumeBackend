from fastapi import FastAPI
from .database import engine
from .database import Base
from . import models
from .routes import auth_routes


app = FastAPI()


# Create tables automatically
Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)

@app.get("/")
def read_root():
    return {"message": "Backend is running successfully 🚀"}
