from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, Date, Time, Interval
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from database import Base
from typing import Optional
from datetime import datetime
from sqlalchemy.event import listen

from database import engine, Base, SessionLocal


class User(Base):
    __tablename__ = "users"

    UserID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    FirstName = Column(String)
    LastName = Column(String)
    Email = Column(String, unique=True, index=True)
    Phone = Column(String, nullable=True)
    Role = Column(String)
    BirthDate = Column(Date, nullable=True)
    Address = Column(String, nullable=True) #delete
    hashed_password = Column(String, nullable=True)  # Password can be nullable initially
    is_password_set = Column(Boolean, default=False) 
    secret_key = Column(String, unique=True) #OTP Secret Key
    

    xyz = relationship("XYZuser", back_populates="user")
    centra = relationship("UserCentra", back_populates="user")

class URLToken(Base):
    __tablename__ = "URLtoken"
    value = Column(String, primary_key=True, unique=True)
    UserID = Column(Integer, ForeignKey('users.UserID'))
    exp = Column(DateTime)

# shipment_batch_association = Table('shipment_batch_association', Base.metadata,
#     Column('shipment_id', Integer, ForeignKey('CentraShipment.id'), primary_key=True),
#     Column('batch_id', Integer, ForeignKey('ProcessedLeaves.ProductID'), primary_key=True)
# )

   

class ProcessedLeaves(Base):
    __tablename__ = 'ProcessedLeaves'
    ProductID = Column(Integer, primary_key=True, autoincrement=True)
    # creator_id = Column(Integer, ForeignKey("Centra.CentralID"), nullable=True)
    # Description = Column(String(100)) #drop
    CentraID = Column(Integer, ForeignKey('Centra.CentralID'))
    Weight = Column(Integer)
    FlouringID = Column(Integer, ForeignKey('FlouringActivity.FlouringID'))
    DryingID = DryingID = Column(Integer, ForeignKey('DryingActivity.DryingID'))
    DriedDate = Column(Date, ForeignKey('DriedLeaves.DriedDate'))
    FlouredDate = Column(Date)
    Shipped = Column(Boolean)

    drying_activity = relationship("DryingActivity", backref="processed_leaves")
    flouring_activity = relationship("FlouringActivity", backref="processed_leaves")

    stocks = relationship("Stock", backref="processed_leaves")
    creator = relationship("Centra", back_populates="processed_leaves", overlaps="centra,batch")
    date = relationship("DriedLeaves", back_populates="dried")
    expeditioncontent = relationship("ExpeditionContent", back_populates="batch")
    centra = relationship("Centra", back_populates="batch", overlaps="creator,processed_leaves")
    

class WetLeavesCollection(Base):
    __tablename__ = 'WetLeavesCollection'
    WetLeavesBatchID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    # UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Date = Column(Date)
    Time = Column(Time)
    Weight = Column(Integer)
    Expired = Column(Boolean)
    Dried = Column(Boolean)
    Status = Column(Enum('Fresh', 'Near expiry', 'Exceeded', 'Expired', 'Processed', name='wet_status'), default='Fresh')
    # Duration = Column(Interval)  # New column for duration
    # creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=False)

    centra = relationship("Centra", back_populates="wet")
    # creator = relationship("User", back_populates="WetLeavesCollection")
    
class DryingMachine(Base):
    __tablename__ = 'DryingMachine'
    MachineID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    CentraID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Capacity = Column(String(100))
    Duration = Column(Interval)
    Status = Column(Enum('idle', 'running', name='machine_status'), default='idle')
    # creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    # creator = relationship("User", back_populates="drying_machines")
    centra = relationship("Centra", back_populates="Dmachine")

class DryingActivity(Base):
    __tablename__ = 'DryingActivity'
    DryingID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    # Date = Column(Date)  #delete
    Weight = Column(Integer)
    DryingMachineID = Column(Integer, ForeignKey('DryingMachine.MachineID'))
    Time = Column(Time)
    # creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)
    centra = relationship("Centra")
    drying_machine = relationship("DryingMachine")
    # creator = relationship("User", back_populates="drying_activity")

class DriedLeaves (Base):
    __tablename__ = 'DriedLeaves'

    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    CentraID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Weight = Column(Integer)
    DriedDate = Column (Date)
    Floured = Column(Boolean, default=False)


    dried = relationship("ProcessedLeaves", back_populates="date")
    centra = relationship("Centra", back_populates="driedleaves")

class FlouringMachine(Base):
    __tablename__ = 'FlouringMachine'
    MachineID = Column(Integer, primary_key=True, nullable=True,autoincrement=True)
    CentraID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=True)
    Capacity = Column(String(100))
    Duration = Column(Interval)
    Status = Column(Enum('idle', 'running', name='machine_status'), default='idle')
    # creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    # creator = relationship("User", back_populates="flouring_machines")
    activity = relationship("FlouringActivity", back_populates="flouring_machine")
    centra = relationship("Centra", back_populates="Fmachine")


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
    # creator_id = Column(Integer, ForeignKey("users.UserID"), nullable=True)

    centra = relationship("Centra")
    # user = relationship("User")
    drying_activity = relationship("DryingActivity")
    flouring_machine = relationship("FlouringMachine", back_populates="activity")
    # creator = relationship("User", back_populates="flouring_activity")

class Centra(Base):
    __tablename__ = 'Centra'
    CentralID = Column(Integer, primary_key=True)
    Address = Column(String(100))
    FlouringSchedule = Column(String(100))


    usercentra = relationship("UserCentra", back_populates="centra")
    processed_leaves = relationship("ProcessedLeaves", back_populates="creator")
    driedleaves = relationship("DriedLeaves", back_populates="centra")
    wet = relationship("WetLeavesCollection", back_populates="centra")
    expedition = relationship("Expedition", back_populates="centra")
    batch = relationship("ProcessedLeaves", back_populates="centra", overlaps="processed_leaves")
    Dmachine = relationship("DryingMachine", back_populates="centra")
    Fmachine = relationship("FlouringMachine", back_populates="centra")
    notification = relationship("Notification", back_populates="user")

class UserCentra(Base):
    __tablename__ = 'UserCentra'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    CentraID = Column(Integer, ForeignKey('Centra.CentralID'))
    Active = Column(Boolean)
    userID = Column(Integer, ForeignKey("users.UserID"))

    centra = relationship("Centra", back_populates="usercentra")
    user = relationship("User", back_populates="centra")

#notifications
class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    centraid = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    user = relationship("Centra", back_populates="notification")


def after_update_listener(mapper, connection, target):
    db = SessionLocal(bind=connection)
    if target.Status == 'running':
        notification = Notification(
            centraid=target.CentraID,
            message=f"{target.__tablename__} with ID {target.MachineID} is now running."
        )
        db.add(notification)
        db.commit()
    db.close()

listen(DryingMachine, 'after_update', after_update_listener)
listen(FlouringMachine, 'after_update', after_update_listener)

class HarborGuard(Base):
    __tablename__ = 'HarborGuard'

    HarbourID = Column(Integer, primary_key=True, index=True, nullable=True, autoincrement=True)
    HarbourName = Column(String, nullable=False)
    Location = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    OpeningHour = Column(Time, nullable=False)
    ClosingHour = Column(Time, nullable=False)
    
class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('ProcessedLeaves.ProductID'))
    weight = Column(Integer)
    # location_id = Column(Integer, ForeignKey('locations.id'))

    # product = relationship("processed_leaves", backref="stock")
    # location = relationship("Location", back_populates="stocks")


# class CentraShipment(Base):
#     __tablename__ = 'CentraShipment'

#     id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
#     ShippingMethod = Column(String)
#     AirwayBill = Column(String)

#     batches = relationship("ProcessedLeaves", secondary=shipment_batch_association, back_populates="shipments")

class Expedition(Base):
    __tablename__ = 'Expedition'
    ExpeditionID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    AirwayBill = Column(String)
    EstimatedArrival = Column(DateTime) 
    TotalPackages = Column(Integer) 
    TotalWeight = Column(Integer)
    Status = Column(Enum('PKG_Delivered', 'PKG_Delivering', 'XYZ_PickingUp', 'XYZ_Completed', 'Missing', name='expedition_status'), default='PKG_Delivering')
    ExpeditionDate = Column(DateTime) 
    ExpeditionServiceDetails = Column(String(100))
    CentralID = Column(Integer, ForeignKey('Centra.CentralID'), nullable=False)

    pickup = relationship("Pickup", back_populates="expedition")
    content = relationship("ExpeditionContent", back_populates="expedition")
    centra = relationship("Centra", back_populates="expedition")
    status = relationship("CheckpointStatus", back_populates="expeditionpoint")

#ExpeditionContents
class ExpeditionContent(Base):
    __tablename__ = 'ExpeditionContent'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    ExpeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    BatchID = Column(Integer, ForeignKey('ProcessedLeaves.ProductID'))

    expedition = relationship("Expedition", back_populates="content")
    batch = relationship("ProcessedLeaves", back_populates="expeditioncontent")

#CheckpointStatus
class CheckpointStatus(Base):
    __tablename__ = 'checkpointstatus'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    expeditionid = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    status = Column(String)
    statusdate = Column(DateTime)

    expeditionpoint = relationship("Expedition", back_populates="status")


class Pickup(Base):
    __tablename__ = 'pickup'

    id = Column(Integer, primary_key=True, index=True, nullable=True, autoincrement=True)
    xyzID = Column(Integer, ForeignKey('XYZuser.id'))
    expeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
    warehouseid = Column(Integer, ForeignKey('warehouses.id'))
    pickup_time = Column(Time)


    expedition = relationship("Expedition", back_populates="pickup")
    xyz = relationship("XYZuser", back_populates="pickup")
    warehouse = relationship("Warehouse", back_populates="pickup")

# class ReceivedPackage(Base):
#     __tablename__ = 'ReceivedPackage'
#     PackageID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
#     ExpeditionID = Column(Integer, ForeignKey('Expedition.ExpeditionID'))
#     UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
#     PackageType = Column(String(100))
#     ReceivedDate = Column(DateTime) 
#     WarehouseDestination = Column(String(100))


class PackageReceipt(Base):
    __tablename__ = 'PackageReceipt'
    ReceiptID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    xyzID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    # haborId = Column(Integer, ForeignKey('ReceivedPackage.PackageID'))
    TotalWeight = Column(Integer)
    TimeAccepted = Column(DateTime)
    Note = Column(String(100))
    Date = Column(DateTime)

    user = relationship("User")
    # received_package = relationship("ReceivedPackage")

class ProductReceipt(Base):
    __tablename__ = 'ProductReceipt'
    ProductReceiptID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    ProductID = Column(Integer)
    ReceiptID = Column(Integer, ForeignKey('PackageReceipt.ReceiptID'))
    RescaledWeight = Column(Integer)
    
    package_receipt = relationship("PackageReceipt")

# class PackageType(Base):
#     __tablename__ = 'PackageType'
#     PackageTypeID = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
#     Description = Column(String(100))


class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
    TotalStock = Column(Integer)
    Capacity = Column(Integer)
    location = Column(String, index=True)
    created_at = Column(Date)

    xyzuser = relationship("XYZuser", back_populates="warehouse")
    pickup = relationship("Pickup", back_populates="warehouse")

class XYZuser(Base):
    __tablename__ = 'XYZuser'

    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    userID = Column(Integer, ForeignKey('users.UserID'))
    WarehouseID = Column(Integer, ForeignKey('warehouses.id'))

    warehouse = relationship("Warehouse", back_populates="xyzuser")
    user = relationship("User", back_populates="xyz")
    pickup = relationship("Pickup", back_populates="xyz")


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    PIC_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)