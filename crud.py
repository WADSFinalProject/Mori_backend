from sqlalchemy.orm import Session
import models, schemas
from fastapi import HTTPException
from schemas import ShipmentPickupSchedule, CentraDetails
# from .schemas import 

from typing import List, Optional
import bcrypt
from passlib.context import CryptContext
from security import get_hash, generate_key,  decrypt_token, encrypt_token
import traceback
from sqlalchemy.exc import IntegrityError


from datetime import datetime, timedelta

from logging import error


# USER
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.Email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Check if the email already exists
    db_user = get_user_by_email(db, user.Email)
    if db_user:
        return None  # Indicate that the user already exists
    secretKey = generate_key("OTP") #forOTP 
    print(secretKey)
    encryptedKey = encrypt_token(secretKey)
    print(encryptedKey)

    new_user = models.User(
        IDORole=user.IDORole,
        Email=user.Email,
        FullName=user.FullName,
        Role=user.Role,
        Phone=user.Phone,
        secret_key = str(encryptedKey)
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        return None  # Indicate that an integrity error occurred

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.UserID == user_id).first()

def update_user(db: Session, user_id: str, update_data: schemas.UserUpdate) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.UserID == user_id).first()
    if db_user:
        for key, value in update_data.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def delete_user(db: Session, user_id: str):
    user = db.query(models.User).filter(models.User.userID == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user


def create_URLToken(db: Session, userid:int, tokenType: str): #to maintain security of the setpass URL
    try:
        token_value = generate_key("URL")

        one_day = datetime.now() + timedelta(hours=24)

        new_token = models.URLToken(
            value=token_value,
            UserID=userid,
            type= tokenType,
            exp=one_day
        )

        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        
        # Log the generated token value
        print("Generated token value:", token_value)

        return new_token
    
    except IntegrityError as e:
        db.rollback()
        print("IntegrityError:", e)
        return None  # Indicate that an integrity error occurred
    
    except Exception as e:
        db.rollback()
        print("Error:", e)
        traceback.print_exc()  # Print the full stack trace for debugging
        return None  # Indicate that an error occurred
    

    

def get_user_by_token(db:Session, token:str):

    try:
        decryptedToken = decrypt_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")


    URLtoken = db.query(models.URLToken).filter(models.URLToken.value == decryptedToken).first()

    if URLtoken is None:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    db_user = db.query(models.User).filter(models.User.UserID == URLtoken.UserID).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user


def delete_token(db:Session, token:str):
    try:
        
        decryptedToken = decrypt_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")

    
    URLtoken = db.query(models.URLToken).filter(models.URLToken.value == decryptedToken).first()

    if URLtoken:
        db.delete(URLtoken)
        db.commit()

    else:
        raise HTTPException(status_code=404, detail="Invalid token")


    return URLtoken

# def get_hash(password: str) -> str:
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password.decode('utf-8')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.Email == email).first()
    if user and pwd_context.verify(password, user.hashed_password):
        return user
    return None




def set_user_password(db: Session, Email: str, new_password: str):
    try:
        db_user = db.query(models.User).filter(models.User.Email == Email).first()
        if db_user:
            db_user.hashed_password = get_hash(new_password)
            db_user.is_password_set = True
            db.commit()
            db.refresh(db_user)
            return db_user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        error(f"Error setting password: {e}")
        raise HTTPException(status_code=422, detail="Error setting password")
    


# BATCHES
def create_batch(db: Session, batch: schemas.ProcessedLeavesCreate):
    drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == batch.DryingID).first()
    flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == batch.FlouringID).first()
    
    db_batch = models.ProcessedLeaves(
        Description=batch.Description,
        DryingID=batch.DryingID,
        FlouringID=batch.FlouringID,
        DriedDate=drying_activity.Date if drying_activity else None,
        FlouredDate=flouring_activity.Date if flouring_activity else None
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_all_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).offset(skip).limit(limit).all()

def get_batch_by_id(db: Session, batch_id: int):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()

def update_batch(db: Session, batch_id: int, update_data: schemas.ProcessedLeavesUpdate):
    batch = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()
    if batch:
        if update_data.DryingID is not None:
            drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == update_data.DryingID).first()
            batch.DryingID = update_data.DryingID
            batch.DriedDate = drying_activity.Date if drying_activity else None

        if update_data.FlouringID is not None:
            flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == update_data.FlouringID).first()
            batch.FlouringID = update_data.FlouringID
            batch.FlouredDate = flouring_activity.Date if flouring_activity else None

        if update_data.Description is not None:
            batch.Description = update_data.Description

        db.commit()
        db.refresh(batch)
        return batch
    return None



def delete_batch(db: Session, batch_id: int):
    batch = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()
    if batch:
        db.delete(batch)
        db.commit()
    return batch

def batch_get_dried_date(db: Session, drying_id: str):
    activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if activity:
        return activity.Date
    return None

def batch_get_floured_date(db: Session, flouring_id: str):
    activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()
    if activity:
        return activity.Date
    return None

def add_new_drying_activity(db: Session, drying_activity: schemas.DryingActivityCreate):
    db_drying_activity = models.DryingActivity(
        # DryingID=drying_activity.DryingID,
        # UserID=drying_activity.UserID,
        CentralID=drying_activity.CentralID,
        Date=drying_activity.Date,
        Weight=drying_activity.Weight,
        DryingMachineID=drying_activity.DryingMachineID,
        Time=drying_activity.Time
    )

    db.add(db_drying_activity)
    db.commit()
    db.refresh(db_drying_activity)
    return db_drying_activity

def get_drying_activity(db: Session, drying_id: int):
    drying= db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if not drying:
        raise HTTPException(status_code=404, detail="Drying Activity not found")
    return drying

def update_drying_activity(db: Session, drying_id: str, drying_activity: schemas.DryingActivityUpdate):
    db_drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if db_drying_activity:
        for key, value in drying_activity.dict().items():
            setattr(db_drying_activity, key, value)
        db.commit()
        db.refresh(db_drying_activity)
    return db_drying_activity

def delete_drying_activity(db: Session, drying_id: str):
    db_drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if db_drying_activity:
        db.delete(db_drying_activity)
        db.commit()
    return db_drying_activity

# MACHINES - FLOURING
def add_new_flouring_machine(db: Session, flouring_machine: schemas.FlouringMachineCreate):
    db_flouring_machine = models.FlouringMachine(
        # MachineID=flouring_machine.MachineID,
        Capacity=flouring_machine.Capacity,
        Status=flouring_machine.Status
    )
    db.add(db_flouring_machine)
    db.commit()
    db.refresh(db_flouring_machine)
    return db_flouring_machine

def get_flouring_machine_status(db: Session, machine_id: str):
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if machine:
        return machine.Status
    return None

def start_flouring_machine(db: Session, machine_id: str) -> bool:
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if  machine.Status != 'running':
        machine.Status = 'running'
        db.commit()
        db.refresh(machine)
        return True
    return False

def stop_flouring_machine(db: Session, machine_id: str) -> bool:
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if machine and machine.Status != 'idle':
        machine.Status = 'idle'
        db.commit()
        db.refresh(machine)
        return True
    return False

def add_new_flouring_activity(db: Session, flouring_activity: schemas.FlouringActivityCreate):
    db_flouring_activity = models.FlouringActivity(
        CentralID=flouring_activity.CentralID,
        Date=flouring_activity.Date,
        Weight=flouring_activity.Weight,
        FlouringMachineID=flouring_activity.FlouringMachineID,
        Time=flouring_activity.Time
    )
    db.add(db_flouring_activity)
    db.commit()
    db.refresh(db_flouring_activity)
    return db_flouring_activity

def get_flouring_activity(db: Session, flouring_id: int):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()

def get_all_flouring_activity(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringActivity).offset(skip).limit(limit).all()

def update_flouring_activity(db: Session, flouring_id: int, flouring_activity: schemas.FlouringActivityUpdate):
    db_flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()
    if db_flouring_activity:
        updated_flouring = flouring_activity.dict(exclude_unset=True)
        for key, value in updated_flouring.items():
            setattr(db_flouring_activity, key, value)
        db.commit()
        db.refresh(db_flouring_activity)
    else:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return db_flouring_activity

def delete_flouring_activity(db: Session, flouring_id: int):
    db_flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()
    if db_flouring_activity:
        db.delete(db_flouring_activity)
        db.commit()
    return db_flouring_activity

# SHIPMENTS
def add_shipment(db: Session, shipment_data: schemas.ShipmentCreate):
    db_shipment_data = models.Shipment(
        batch_id=shipment_data.batch_id,
        description=shipment_data.description,
        status=shipment_data.status,
        weight=shipment_data.weight,
        issue_description=shipment_data.issue_description
        
    )
    db.add(db_shipment_data)
    db.commit()
    db.refresh(db_shipment_data)
    return db_shipment_data

def update_shipment(db: Session, shipment_id: int, shipment_update: schemas.ShipmentUpdate):
    db_shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if db_shipment:
        update_data = shipment_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_shipment, key, value)
        db.commit()
        db.refresh(db_shipment)
    else:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return db_shipment


def get_all_shipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Shipment).offset(skip).limit(limit).all()

def get_shipment_details(db: Session, shipment_id: str):
    return db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()

def delete_shipment(db: Session, shipment_id: str):
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if shipment:
        db.delete(shipment)
        db.commit()
    return shipment

def confirm_shipment(db: Session, shipment_id: int, weight: int):
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if shipment:
        shipment.status = 'Confirmed'
        shipment.weight = weight
        db.commit()
        return shipment
    return None


def report_shipment_issue(db: Session, shipment_id: int, description: str):
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if shipment:
        shipment.issue_description = description
        db.commit()
        return shipment
    return None

def rescale_shipment(db: Session, shipment_id: int, new_weight: float):
    shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
    if shipment:
        shipment.weight = new_weight
        db.commit()
        db.refresh(shipment)
        return True
    return False

# STOCKS
def get_all_stocks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Stock).offset(skip).limit(limit).all()

def get_stock_detail(db: Session, location_id: int):
    return db.query(models.Stock).filter(models.Stock.location_id == location_id).first()

# LOCATIONS
def get_location_details(db: Session, location_id: int):
    return db.query(models.Location).filter(models.Location.id == location_id).first()

# SHIPMENT HISTORY
def get_shipment_history(db: Session, location_id: int):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if location:
        return location.shipment_history  # Make sure 'shipment_history' is correctly modeled
    return []

def validate_shipment_id(db: Session, shipment_id: int):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    return bool(shipment)

def schedule_pickup(db: Session, pickup_data: ShipmentPickupSchedule):
    pickup = models.PickupDetails(
        shipment_id=pickup_data.shipment_id,
        pickup_time=pickup_data.pickup_time,
        location=pickup_data.location
    )
    db.add(pickup)
    db.commit()
    return True

# CENTRA 
def get_all_centras(db: Session):
    return db.query(models.Centra).all()

def get_centra_by_id(db: Session, CentralID: int):
    centra = db.query(models.Centra).filter(models.Centra.CentralID == CentralID).first()
    if not centra:
        raise HTTPException(status_code=404, detail="Centra not found")
    return centra

def add_new_centra(db: Session, centra: schemas.CentraCreate):
    db_centra = models.Centra(
        # CentralID=centra.CentralID,
        Address=centra.Address
    )
    db.add(db_centra)
    db.commit()
    db.refresh(db_centra)
    return db_centra

def update_centra(db: Session, CentralID: int, centra_update: schemas.CentraUpdate):
    db_centra = db.query(models.Centra).filter(models.Centra.CentralID == CentralID).first()
    if db_centra:
        for key, value in centra_update.dict(exclude_unset=True).items():
            setattr(db_centra, key, value)
        db.commit()
        db.refresh(db_centra)
    else:
        raise HTTPException(status_code=404, detail="Centra not found")
    return db_centra

def delete_centra(db: Session, CentralID: int):
    db_centra = db.query(models.CentraDetails).filter(models.CentraDetails.CentralID == CentralID).first()
    if db_centra:
        db.delete(db_centra)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Centra not found")
    return {"message": "Centra deleted successfully"}

#HARBOUR GUARD

def get_all_harbor_guards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.HarborGuard).offset(skip).limit(limit).all()

def get_harbor_guard(db: Session, HarborID: int):
    guard = db.query(models.HarborGuard).filter(models.HarborGuard.HarborID == HarborID).first()
    if not guard:
        raise HTTPException(status_code=404, detail="Harbor guard not found")
    return guard

def create_harbor_guard(db: Session, guard_data: schemas.HarborGuardCreate):
    db_guard = models.HarborGuard(
        PIC_name=guard_data.PIC_name,
        email=guard_data.email,
        phone=guard_data.phone
    )
    db.add(db_guard)
    db.commit()
    db.refresh(db_guard)
    return db_guard

def update_harbor_guard(db: Session, HarborID: int, guard_data: schemas.HarborGuardUpdate):
    db_guard = db.query(models.HarborGuard).filter(models.HarborGuard.HarborID == HarborID).first()
    if db_guard:
        for key, value in guard_data.dict(exclude_unset=True).items():
            setattr(db_guard, key, value)
        db.commit()
        return db_guard
    raise HTTPException(status_code=404, detail="Harbor guard not found")

def delete_harbor_guard(db: Session, guard_id: int):
    db_guard = db.query(models.HarborGuard).filter(models.HarborGuard.id == guard_id).first()
    if db_guard:
        db.delete(db_guard)
        db.commit()
        return {"message": "Harbor guard deleted successfully"}
    raise HTTPException(status_code=404, detail="Harbor guard not found")

# WAREHOUSE LOCATION
def create_warehouse(db: Session, warehouse_data: schemas.WarehouseCreate):
    db_warehouse = models.Warehouse(
        PIC_name=warehouse_data.PIC_name,
        email=warehouse_data.email,
        phone=warehouse_data.phone
    )
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def get_all_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Warehouse]:
    return db.query(models.Warehouse).offset(skip).limit(limit).all()

def get_warehouse(db: Session, warehouse_id: str) -> Optional[models.Warehouse]:
    return db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()

def update_warehouse(db: Session, warehouse_id: str, update_data: schemas.WarehouseUpdate) -> Optional[models.Warehouse]:
    db_warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
    if db_warehouse:
        for key, value in update_data.dict().items():
            setattr(db_warehouse, key, value)
        db.commit()
        db.refresh(db_warehouse)
    return db_warehouse

def delete_warehouse(db: Session, warehouse_id: str) -> Optional[models.Warehouse]:
    db_warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
    if db_warehouse:
        db.delete(db_warehouse)
        db.commit()
    return db_warehouse


# WET LEAVES COLLECTIONS
def add_new_wet_leaves_collection(db: Session, wet_leaves_collection: schemas.WetLeavesCollectionCreate):
    db_wet_leaves_collection = models.WetLeavesCollection(
        # WetLeavesBatchID=wet_leaves_collection.WetLeavesBatchID,
        # UserID=wet_leaves_collection.UserID,
        CentralID=wet_leaves_collection.CentralID,
        Date=wet_leaves_collection.Date,
        Weight=wet_leaves_collection.Weight,
        Expired=wet_leaves_collection.Expired,
        ExpirationTime=wet_leaves_collection.ExpirationTime
    )
    db.add(db_wet_leaves_collection)
    db.commit()
    db.refresh(db_wet_leaves_collection)
    return db_wet_leaves_collection

def get_all_wet_leaves_collections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WetLeavesCollection).offset(skip).limit(limit).all()

def get_wet_leaves_collection(db: Session, wet_leaves_batch_id: str):
    return db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()

def update_wet_leaves_collection(db: Session, wet_leaves_batch_id: str, update_data: schemas.WetLeavesCollectionUpdate):
    db_wet_leaves_collection = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()
    if db_wet_leaves_collection:
        for key, value in update_data.dict().items():
            setattr(db_wet_leaves_collection, key, value)
        db.commit()
        db.refresh(db_wet_leaves_collection)
    return db_wet_leaves_collection

def delete_wet_leaves_collection(db: Session, wet_leaves_batch_id: str):
    db_wet_leaves_collection = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()
    if db_wet_leaves_collection:
        db.delete(db_wet_leaves_collection)
        db.commit()
    return db_wet_leaves_collection

# DRYING MACHINE
def create_drying_machine(db: Session, drying_machine: schemas.DryingMachineCreate):
    db_drying_machine = models.DryingMachine(
        # MachineID=drying_machine.MachineID,
        Capacity=drying_machine.Capacity,
        Status=drying_machine.Status
    )
    db.add(db_drying_machine)
    db.commit()
    db.refresh(db_drying_machine)
    return db_drying_machine

def get_all_drying_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DryingMachine).offset(skip).limit(limit).all()

def get_drying_machine(db: Session, machine_id: str):
    return db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()

def update_drying_machine(db: Session, machine_id: str, update_data: schemas.DryingMachineUpdate):
    db_drying_machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    if db_drying_machine:
        for key, value in update_data.dict().items():
            setattr(db_drying_machine, key, value)
        db.commit()
        db.refresh(db_drying_machine)
    return db_drying_machine

def delete_drying_machine(db: Session, machine_id: str):
    db_drying_machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    if db_drying_machine:
        db.delete(db_drying_machine)
        db.commit()
    return db_drying_machine

def get_drying_machine_status(db: Session, machine_id: int):
    # Convert machine_id to string
    machine_id_str = str(machine_id)
    
    db_drying_machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id_str).first()
    if db_drying_machine:
        return db_drying_machine.Status
    return None

def start_drying_machine(db: Session, machine_id: str) -> bool:
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    if machine.Status != 'running':
        machine.Status = 'running'
        db.commit()
        db.refresh(machine)
        return True
    return False

def stop_drying_machine(db: Session, machine_id: str) -> bool:
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    if machine and machine.Status != 'idle':
        machine.Status = 'idle'
        db.commit()
        db.refresh(machine)
        return True
    return False

#expedition
def get_expedition(db: Session, expedition_id: int):
    return db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()

def get_expeditions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Expedition).offset(skip).limit(limit).all()

def create_expedition(db: Session, expedition: schemas.ExpeditionCreate):
    db_expedition = models.Expedition(**expedition.dict())
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)
    return db_expedition

def update_expedition(db: Session, expedition_id: int, expedition: schemas.ExpeditionUpdate):
    db_expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if not db_expedition:
        return None
    for key, value in expedition.dict(exclude_unset=True).items():
        setattr(db_expedition, key, value)
    db.commit()
    db.refresh(db_expedition)
    return db_expedition

def delete_expedition(db: Session, expedition_id: int):
    db_expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if not db_expedition:
        return None
    db.delete(db_expedition)
    db.commit()
    return db_expedition


#receveid packages
def get_received_package(db: Session, package_id: int):
    return db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()

def get_received_packages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ReceivedPackage).offset(skip).limit(limit).all()

def create_received_package(db: Session, received_package: schemas.ReceivedPackageCreate):
    db_received_package = models.ReceivedPackage(**received_package.dict())
    db.add(db_received_package)
    db.commit()
    db.refresh(db_received_package)
    return db_received_package

def update_received_package(db: Session, package_id: int, received_package: schemas.ReceivedPackageUpdate):
    db_received_package = db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()
    if not db_received_package:
        return None
    for key, value in received_package.dict(exclude_unset=True).items():
        setattr(db_received_package, key, value)
    db.commit()
    db.refresh(db_received_package)
    return db_received_package

def delete_received_package(db: Session, package_id: int):
    db_received_package = db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()
    if not db_received_package:
        return None
    db.delete(db_received_package)
    db.commit()
    return db_received_package


#package receipt

def get_package_receipt(db: Session, receipt_id: int):
    return db.query(models.PackageReceipt).filter(models.PackageReceipt.ReceiptID == receipt_id).first()

def get_package_receipts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PackageReceipt).offset(skip).limit(limit).all()

def create_package_receipt(db: Session, package_receipt: schemas.PackageReceiptCreate):
    db_package_receipt = models.PackageReceipt(**package_receipt.dict())
    db.add(db_package_receipt)
    db.commit()
    db.refresh(db_package_receipt)
    return db_package_receipt

def update_package_receipt(db: Session, receipt_id: int, package_receipt_update: schemas.PackageReceiptUpdate):
    db_package_receipt = db.query(models.PackageReceipt).filter(models.PackageReceipt.ReceiptID == receipt_id).first()
    if db_package_receipt:
        update_data = package_receipt_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_package_receipt, key, value)
        db.commit()
        db.refresh(db_package_receipt)
    return db_package_receipt

def delete_package_receipt(db: Session, receipt_id: int):
    db_package_receipt = db.query(models.PackageReceipt).filter(models.PackageReceipt.ReceiptID == receipt_id).first()
    if db_package_receipt:
        db.delete(db_package_receipt)
        db.commit()
    return db_package_receipt


#product receipt

def create_product_receipt(db: Session, product_receipt: schemas.ProductReceiptCreate):
    db_product_receipt = models.ProductReceipt(**product_receipt.dict())
    db.add(db_product_receipt)
    db.commit()
    db.refresh(db_product_receipt)
    return db_product_receipt

def get_product_receipt(db: Session, product_receipt_id: int):
    return db.query(models.ProductReceipt).filter(models.ProductReceipt.ProductReceiptID == product_receipt_id).first()

def get_product_receipts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProductReceipt).offset(skip).limit(limit).all()

def update_product_receipt(db: Session, product_receipt_id: int, product_receipt_update: schemas.ProductReceiptUpdate):
    db_product_receipt = db.query(models.ProductReceipt).filter(models.ProductReceipt.ProductReceiptID == product_receipt_id).first()
    if db_product_receipt:
        update_data = product_receipt_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product_receipt, key, value)
        db.commit()
        db.refresh(db_product_receipt)
    return db_product_receipt

def delete_product_receipt(db: Session, product_receipt_id: int):
    db_product_receipt = db.query(models.ProductReceipt).filter(models.ProductReceipt.ProductReceiptID == product_receipt_id).first()
    if db_product_receipt:
        db.delete(db_product_receipt)
        db.commit()
    return db_product_receipt

