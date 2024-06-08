from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from database import Base
from typing import Optional
from datetime import datetime

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

class URLToken(Base):
    __tablename__ = "URLtoken"
    value = Column(String, primary_key=True, unique=True)
    UserID = Column(Integer, ForeignKey('users.UserID'))
    type = Column(String)
    exp = Column(DateTime)

   

class ProcessedLeaves(Base):
    __tablename__ = 'ProcessedLeaves'
    ProductID = Column(Integer, primary_key=True)
    Description = Column(String(100))
    FlouringID = Column(String(50), ForeignKey('FlouringActivity.FlouringID'))
    DryingID = Column(String(50), ForeignKey('DryingActivity.DryingID'))
    DriedDate = Column(String)
    FlouredDate = Column(String)

    drying_activity = relationship("DryingActivity", backref="processed_leaves")
    flouring_activity = relationship("FlouringActivity", backref="processed_leaves")

    stocks = relationship("Stock", backref="processed_leaves")
    
class WetLeavesCollection(Base):
    __tablename__ = 'WetLeavesCollection'
    WetLeavesBatchID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, nullable=False)
    Date = Column(DateTime)
    Time = Column(DateTime)
    Weight = Column(Integer)
    Expired = Column(Boolean)
    ExpirationTime = Column(String(50))

    user = relationship("User")

class DryingMachine(Base):
    __tablename__ = 'DryingMachine'
    MachineID = Column(String(50), primary_key=True)
    Capacity = Column(String(100))
    Status = Column(Enum('idle', 'running', name='machine_status'), default='idle')

class DryingActivity(Base):
    __tablename__ = 'DryingActivity'
    DryingID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, nullable=False)
    Date = Column(DateTime)
    Weight = Column(Integer)
    DryingMachineID = Column(String(50), ForeignKey('DryingMachine.MachineID'))
    Time = Column(DateTime)
    user = relationship("User")
    drying_machine = relationship("DryingMachine")

class FlouringMachine(Base):
    __tablename__ = 'FlouringMachine'
    MachineID = Column(String(50), primary_key=True)
    Capacity = Column(String(100))

class FlouringActivity(Base):
    __tablename__ = 'FlouringActivity'
    FlouringID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, nullable=False)
    Date = Column(DateTime) 
    Weight = Column(Integer)
    FlouringMachineID = Column(String(50), ForeignKey('FlouringMachine.MachineID'))
    DryingID = Column(String(50))

    user = relationship("User")
    flouring_machine = relationship("FlouringMachine")

class Centra(Base):
    __tablename__ = 'Centra'
    CentralID = Column(Integer, primary_key=True)
    Address = Column(String(100))

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('ProcessedLeaves.ProductID'))
    weight = Column(Integer)
    # location_id = Column(Integer, ForeignKey('locations.id'))

    # product = relationship("processed_leaves", backref="stock")
    # location = relationship("Location", back_populates="stocks")

class Expedition(Base):
    __tablename__ = 'Expedition'
    ExpeditionID = Column(Integer, primary_key=True)
    EstimatedArrival = Column(DateTime) 
    TotalPackages = Column(Integer)
    ExpeditionDate = Column(DateTime) 
    ExpeditionServiceDetails = Column(String(100))
    Destination = Column(String(100))
    CentralID = Column(Integer, nullable=False)

class ReceivedPackage(Base):
    __tablename__ = 'ReceivedPackage'
    PackageID = Column(Integer, primary_key=True)
    ExpeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    PackageType = Column(String(100))
    ReceivedDate = Column(DateTime) 
    WarehouseDestination = Column(String(100))

    user = relationship("User")
    expedition = relationship("Expedition")


class PackageReceipt(Base):
    __tablename__ = 'PackageReceipt'
    ReceiptID = Column(Integer, primary_key=True)
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
    ProductReceiptID = Column(Integer, primary_key=True)
    ProductID = Column(String(1000))
    ReceiptID = Column(Integer, ForeignKey('PackageReceipt.ReceiptID'))
    RescaledWeight = Column(Integer)

    package_receipt = relationship("PackageReceipt")

class PackageType(Base):
    __tablename__ = 'PackageType'
    PackageTypeID = Column(Integer, primary_key=True)
    Description = Column(String(100))


class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, index=True)
    PIC_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)

# # class User(BaseModel):
# #     PIC_name: str
# #     email: EmailStr
# #     phone: str

# # class Batch(BaseModel):
# #     weight: float
# #     collection_date: str
# #     time: str

# # class MachineAction(BaseModel):
# #     machine_id: int

# # class ShipmentStatusUpdate(BaseModel):
# #     status: str

# # class ShipmentConfirmation(BaseModel):
# #     shipment_id: int
# #     weight: Optional[float] = None

# # class ShipmentSchedule(BaseModel):
# #     shipment_id: int
# #     pickup_time: str
# #     location: str

# # class ShipmentIssue(BaseModel):
# #     shipment_id: int
# #     issue_description: str

# # class ShipmentRescale(BaseModel):
# #     shipment_id: int
# #     new_weight: float

# # class ShipmentPickupSchedule(BaseModel):
# #     shipment_id: int
# #     pickup_time: datetime
# #     location: str

# # class ShipmentUpdate(BaseModel):
# #     status: str
# #     checkpoint: str
# #     action: str

# # class CentraDetails(BaseModel):
# #     PIC_name: str
# #     location: str
# #     email: str
# #     phone: int
# #     drying_machine_status: str
# #     flouring_machine_status: str
# #     action: str

# # class HarborGuard(BaseModel):
# #     PIC_name: str
# #     email: EmailStr
# #     phone: str

