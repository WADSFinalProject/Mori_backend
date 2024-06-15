from fastapi import FastAPI
from database import engine 

from fastapi.middleware.cors import CORSMiddleware
from secured_routes import secured_router
import models
import  SMTP,security

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

#Handling CORS
origins = [
    "http://localhost:5173",
    "https://mori-frontend.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def welcome():
    return {"message": "Welcome to our API!"}



app.include_router(secured_router, prefix="/secured")