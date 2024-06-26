from fastapi import FastAPI, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from database import get_db, engine 
from utils import create_access_token, create_refresh_token, verify_token
from security import verify_otp
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from secured_routes import secured_router
import crud, models, schemas  
import SMTP

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

#Handling CORS
origins = [
    "http://localhost:5173",
    "https://mori-mori.vercel.app"
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


    
@app.get("/users/validate-link") #for setpass
async def validate_token(token:str, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_token(db, token)
        return {"valid": True}
    except HTTPException as e:
        return {"valid": False, "error": str(e)}

@app.post("/users/setpassword")
async def set_password(response_model: schemas.UserSetPassword, db: Session = Depends(get_db)):
    print(response_model.token)
    print(response_model.new_password)
    try:
        db_user = crud.get_user_by_token(db,response_model.token)
        pass_user =crud.set_user_password(db,Email= db_user.Email, new_password= response_model.new_password)

        if pass_user:
            crud.delete_token(db, response_model.token)
            return {"message": "Password set successfully"}
        raise HTTPException(status_code=404, detail="User not found or error setting password")
    
    except HTTPException as e:
        return { "error": str(e)}
    
@app.post("/users/resetpassword-OTP")
async def reset_password_OTP(email: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db,email)
    if db_user:
        SMTP.send_resetPassword_OTP(db_user)
        return {"message" : "Email is a valid user, OTP Sent!"}
  
    raise HTTPException(status_code=401, detail="Invalid email")

@app.post("/users/verify-reset")
async def verify_reset(verification: schemas.UserVerification,  db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db,verification.Email)
    verified = verify_otp(db_user.secret_key, verification.Code)
    if verified:
         return {"message": "Valid OTP!"}
  
    raise HTTPException(status_code=401, detail="Invalid OTP!")

@app.put("/users/resetpassword")
async def reset_password(response_model: schemas.UserResetPassword, db: Session = Depends(get_db)):
   try:
        crud.set_user_password(db,response_model.Email, response_model.new_password)

        return {"message": "Password reset successfully!"}
   
   except Exception as e:
        db.rollback()  # Rollback in case of any exception
        raise HTTPException(status_code=500, detail=f"An error occurred during password reset: {str(e)}")
 
 

@app.post("/users/login")
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    
    db_user = crud.authenticate_user(db, user.Email, user.Password)  # Call with positional arguments
    
    if db_user:
        SMTP.send_OTP(db_user)
        return {"message": "Credentials valid, OTP Sent!"}
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/users/verify")
async def verify_user(verification: schemas.UserVerification, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, verification.Email)
    verified = verify_otp(db_user.secret_key, verification.Code)
    if verified:
        access_token = create_access_token(db, db_user.UserID, db_user.Role, db_user.FirstName + ' ' + db_user.LastName)
        refresh_token = create_refresh_token(db, db_user.UserID, db_user.Role, db_user.FirstName + ' ' + db_user.LastName)
        
        response = JSONResponse(content={"access_token": access_token, "refresh_token": refresh_token})
        return response

    raise HTTPException(status_code=404, detail="Verification failed")

@app.post("/token/refresh")
async def refresh_token(refresh_token: str , db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")
    try:
        payload = verify_token(refresh_token)
        new_access_token = create_access_token(db, payload["sub"], payload["role"], payload["name"])
        return {"access_token": new_access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/users/resend_code")
async def resend_code(data: dict, db: Session = Depends(get_db)):
    print(data.get("theEmail"))
    db_user = crud.get_user_by_email(db,data.get("theEmail"))
    resent = SMTP.send_OTP(db_user, db)
    if resent:
        return {"message": "Verification code resent"}
    raise HTTPException(status_code=404, detail="Failed to resend code")


@app.post("/users/logout")
async def logout():
    response = JSONResponse(content={"message": "Logout successful"}, status_code=200)
    response.delete_cookie(key="refresh_token")
    return response

@app.post("/usersNo", response_model=schemas.User)
def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, user=new_user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        SMTP.send_setPassEmail(db_user,db)
        return db_user

app.include_router(secured_router, prefix="/secured")


