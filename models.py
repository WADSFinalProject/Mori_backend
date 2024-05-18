from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    UserID = Column(Integer, primary_key=True, index=True)
    IDORole = Column(String)
    Email = Column(String, unique=True, index=True)
    FullName = Column(String)
    Role = Column(String)
    hashed_password = Column(String, nullable=True)

    wet_leaves_collections = relationship("WetLeavesCollection", back_populates="user")
    drying_activities = relationship("DryingActivity", back_populates="user")
    flouring_activities = relationship("FlouringActivity", back_populates="user")
    received_packages = relationship("ReceivedPackage", back_populates="user")
    package_receipts = relationship("PackageReceipt", back_populates="user")

class ProcessedLeaves(Base):
    __tablename__ = 'ProcessedLeaves'
    ProductID = Column(Integer, primary_key=True)
    Description = Column(String(100))
    FlouringID = Column(String(50), ForeignKey('FlouringActivity.FlouringID'))
    DryingID = Column(String(50), ForeignKey('DryingActivity.DryingID'))

class WetLeavesCollection(Base):
    __tablename__ = 'WetLeavesCollection'
    WetLeavesBatchID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)
    DateTime = Column(DateTime, default=datetime.now)
    Weight = Column(Integer)
    Expired = Column(Boolean)
    ExpirationTime = Column(String(50))

    user = relationship("User", back_populates="wet_leaves_collections")

class DryingMachine(Base):
    __tablename__ = 'DryingMachine'
    MachineID = Column(String(50), primary_key=True)
    Capacity = Column(String(100))

class DryingActivity(Base):
    __tablename__ = 'DryingActivity'
    DryingID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)
    DateTime = Column(DateTime, default=datetime.now)
    Weight = Column(Integer)
    DryingMachineID = Column(String(50), ForeignKey('DryingMachine.MachineID'))

    user = relationship("User", back_populates="drying_activities")

class FlouringMachine(Base):
    __tablename__ = 'FlouringMachine'
    MachineID = Column(String(50), primary_key=True)
    Capacity = Column(String(100))

class FlouringActivity(Base):
    __tablename__ = 'FlouringActivity'
    FlouringID = Column(String(50), primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)
    DateTime = Column(DateTime, default=datetime.now)
    Weight = Column(Integer)
    FlouringMachineID = Column(String(50), ForeignKey('FlouringMachine.MachineID'))
    DryingID = Column(String(50))

    user = relationship("User", back_populates="flouring_activities")

class Centra(Base):
    __tablename__ = 'Centra'
    CentralID = Column(Integer, primary_key=True)
    Address = Column(String(100))

class Expedition(Base):
    __tablename__ = 'Expedition'
    ExpeditionID = Column(Integer, primary_key=True)
    EstimatedArrival = Column(DateTime)
    TotalPackages = Column(Integer)
    ExpeditionDate = Column(DateTime, default=datetime.now)
    ExpeditionServiceDetails = Column(String(100))
    Destination = Column(String(100))
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)

class ReceivedPackage(Base):
    __tablename__ = 'ReceivedPackage'
    PackageID = Column(Integer, primary_key=True)
    ExpeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    PackageType = Column(String(100))
    ReceivedDate = Column(DateTime, default=datetime.now)
    WarehouseDestination = Column(String(100))

    user = relationship("User", back_populates="received_packages")

class PackageReceipt(Base):
    __tablename__ = 'PackageReceipt'
    ReceiptID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    PackageID = Column(Integer, ForeignKey('ReceivedPackage.PackageID'))
    TotalWeight = Column(Integer)
    DateTimeAccepted = Column(DateTime, default=datetime.now)
    Note = Column(String(100))

    user = relationship("User", back_populates="package_receipts")

class ProductReceipt(Base):
    __tablename__ = 'ProductReceipt'
    ProductReceiptID = Column(Integer, primary_key=True)
    ProductID = Column(String(1000))
    ReceiptID = Column(Integer, ForeignKey('PackageReceipt.ReceiptID'))
    RescaledWeight = Column(Integer)

class PackageType(Base):
    __tablename__ = 'PackageType'
    PackageTypeID = Column(Integer, primary_key=True)
    Description = Column(String(100))
