from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, Date, Time

from utils.database import Base


class User(Base):
    __tablename__ = "users"

    UserID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    IDORole = Column(String)
    Email = Column(String, unique=True, index=True)
    FullName = Column(String)
    Role = Column(String)
    Phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Password can be nullable initially
    is_password_set = Column(Boolean, default=False) 
    secret_key = Column(String, unique=True) #OTP Secret Key

class URLToken(Base):
    __tablename__ = "URLtoken"
    value = Column(String, primary_key=True, unique=True)
    UserID = Column(Integer, ForeignKey('users.UserID'))
    exp = Column(DateTime)