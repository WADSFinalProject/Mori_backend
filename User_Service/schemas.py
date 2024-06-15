from typing import Optional
from pydantic import BaseModel, EmailStr

# user schemas
class UserBase(BaseModel):
    IDORole: Optional[int] = None
    Email: EmailStr
    FullName: str
    Role: str
    Phone: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    IDORole: Optional[str] = None
    Password: Optional[str] = None
    Email: Optional[str] = None
    FullName: Optional[str] = None
    Role: Optional[str] = None
    Phone: Optional[str] = None

class UserSetPassword(BaseModel):
    token: str
    new_password: str
  

class User(UserBase):
    UserID: int

    class Config:
        from_attributes = True

class UserRegistration(BaseModel):
    Email: str
    FullName: str
    Role: str
    Password: str


class UserLogin(BaseModel):
    Email: str
    Password: str
    
class UserVerification(BaseModel):
    Email:str
    Code: str

class UserResetPassword(BaseModel):
    Email: EmailStr
    new_password : str
