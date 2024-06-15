from fastapi import FastAPI, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from database import get_db, engine 
from typing import Optional, List
from datetime import datetime
from security import create_access_token,verify_otp, create_refresh_token, verify_token
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from secured_routes import secured_router
import crud, models, schemas  
import SMTP, security

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

# Users
@app.post("/users/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = crud.create_user(db, user)

    if db_user is None:
        raise HTTPException(status_code=400, detail="User already registered or integrity error")
    
    SMTP.send_setPassEmail(db_user,db)
    return {"message": "User registered successfully"}
    


app.include_router(secured_router, prefix="/secured")