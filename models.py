from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, Date, Time
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from database import Base
from typing import Optional
from datetime import datetime

from database import engine, Base

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

    processed_leaves = relationship("ProcessedLeaves", back_populates="creator")
    drying_machines = relationship("DryingMachine", back_populates="creator")
    flouring_machines = relationship("FlouringMachine", back_populates="creator")
    drying_activity = relationship("DryingActivity", back_populates="creator")
    flouring_activity = relationship("FlouringActivity", back_populates="creator")
    WetLeavesCollection = relationship("WetLeavesCollection", back_populates="creator")

class URLToken(Base):
    __tablename__ = "URLtoken"
    value = Column(String, primary_key=True, unique=True)
    UserID = Column(Integer, ForeignKey('users.UserID'))
    exp = Column(DateTime)

   

class ProcessedLeaves(Base):
    __tablename__ = 'ProcessedLeaves'
    ProductID = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    Description = Column(String(100))
    FlouringID = Column(Integer, ForeignKey('FlouringActivity.FlouringID'))
    DryingID = Column(Integer, ForeignKey('DryingActivity.DryingID'))
    DriedDate = Column(Date)
    FlouredDate = Column(Date)

    drying_activity = relationship("DryingActivity", backref="processed_leaves")
    flouring_activity = relationship("FlouringActivity", backref="processed_leaves")

    stocks = relationship("Stock", backref="processed_leaves")
    creator = relationship("User", back_populates="processed_leaves")

class WetLeavesCollection(Base):
    __tablename__ = 'WetLeavesCollection'
    WetLeavesBatchID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    # UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Date = Column(DateTime)
    # Time = Column(Time)
    Weight = Column(Integer)
    Expired = Column(Boolean)
    ExpirationTime = Column(Time, name="ExpirationTime")
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=False)

    centra = relationship("Centra")
    creator = relationship("User", back_populates="WetLeavesCollection")
class DryingMachine(Base):
    __tablename__ = 'DryingMachine'
    MachineID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    Capacity = Column(String(100))
    Status = Column(Enum('idle', 'running', name='machine_status'), default='idle')
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    creator = relationship("User", back_populates="drying_machines")

class DryingActivity(Base):
    __tablename__ = 'DryingActivity'
    DryingID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Date = Column(Date)
    Weight = Column(Integer)
    DryingMachineID = Column(Integer, ForeignKey('DryingMachine.MachineID'))
    Time = Column(Time)
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    centra = relationship("Centra")
    drying_machine = relationship("DryingMachine")
    creator = relationship("User", back_populates="drying_activity")

class FlouringMachine(Base):
    __tablename__ = 'FlouringMachine'
    MachineID = Column(Integer, primary_key=True, nullable=True,autoincrement=True)
    Capacity = Column(String(100))
    Status = Column(Enum('idle', 'running', name='machine_status'), default='idle')
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    creator = relationship("User", back_populates="flouring_machines")


class FlouringActivity(Base):
    __tablename__ = 'FlouringActivity'
    FlouringID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    # UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Date = Column(Date) 
    Weight = Column(Integer)
    FlouringMachineID = Column(Integer, ForeignKey('FlouringMachine.MachineID'))
    DryingID = Column(Integer, ForeignKey('DryingActivity.DryingID'))
    Time = Column(Time)
    creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    centra = relationship("Centra")
    # user = relationship("User")
    drying_activity = relationship("DryingActivity")
    flouring_machine = relationship("FlouringMachine")
    creator = relationship("User", back_populates="flouring_activity")

class Centra(Base):
    __tablename__ = 'Centra'
    CentralID = Column(Integer, primary_key=True)
    Address = Column(String(100))

class HarborGuard(Base):
    __tablename__ = 'HarborGuard'

    HarbourID = Column(Integer, primary_key=True, index=True, nullable=True, autoincrement=True)
    harbourName = Column(String, nullable=False)
    location = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    openingHour = Column(Time, nullable=False)
    closingHour = Column(Time, nullable=False)

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('ProcessedLeaves.ProductID'))
    weight = Column(Integer)
    # location_id = Column(Integer, ForeignKey('locations.id'))

    # product = relationship("processed_leaves", backref="stock")
    # location = relationship("Location", back_populates="stocks")

class Expedition(Base):
    __tablename__ = 'Expedition'
    ExpeditionID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    EstimatedArrival = Column(DateTime) 
    TotalPackages = Column(Integer)
    ExpeditionDate = Column(DateTime) 
    ExpeditionServiceDetails = Column(String(100))
    Destination = Column(String(100))
    CentralID = Column(Integer, nullable=False)
    received_packages = relationship("ReceivedPackage", back_populates="expedition", cascade="all, delete-orphan")

class ReceivedPackage(Base):
    __tablename__ = 'ReceivedPackage'
    PackageID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    ExpeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    PackageType = Column(String(100))
    ReceivedDate = Column(DateTime) 
    WarehouseDestination = Column(String(100))

    user = relationship("User")
    expedition = relationship("Expedition", back_populates="received_packages")


class PackageReceipt(Base):
    __tablename__ = 'PackageReceipt'
    ReceiptID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    PackageID = Column(Integer, ForeignKey('ReceivedPackage.PackageID'))
    TotalWeight = Column(Integer)
    TimeAccepted = Column(DateTime)
    Note = Column(String(100))
    Date = Column(DateTime)

    user = relationship("User")
    received_package = relationship("ReceivedPackage")

class ProductReceipt(Base):
    __tablename__ = 'ProductReceipt'
    ProductReceiptID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    ProductID = Column(Integer)
    ReceiptID = Column(Integer, ForeignKey('PackageReceipt.ReceiptID'))
    RescaledWeight = Column(Integer)

    package_receipt = relationship("PackageReceipt")

class PackageType(Base):
    __tablename__ = 'PackageType'
    PackageTypeID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    Description = Column(String(100))


class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    PIC_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)

class Shipment(Base):
    __tablename__ = 'shipments'

    ID = Column(Integer, primary_key=True, index=True, nullable=True, autoincrement=True)
    batch_id = Column(String, index=True)  
    shipmentId = Column(String, nullable=False) 
    driedDate = Column(String, nullable=True)  
    flouredDate = Column(String, nullable=True)  
    weight = Column(String, nullable=True)  
    status = Column(String, nullable=True)
    checkpoint = Column(String, nullable=True) 

class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    PIC_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
