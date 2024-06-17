from sqlalchemy.orm import Session, joinedload
import models, schemas
from fastapi import HTTPException
from schemas import CentraDetails
# from .schemas import 

from typing import List, Optional
import bcrypt
from passlib.context import CryptContext
from security import get_hash, generate_key,  decrypt_token, encrypt_token
import traceback
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime


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
        FirstName=user.FirstName,
        LastName=user.LastName,
        Email=user.Email,
        Phone=user.Phone,
        Role=user.Role,
        BirthDate=user.BirthDate,
        Address=user.Address,
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

def get_all_users(db: Session, skip: int = 0, limit: int = 100, sort_by: str = 'Name', sort_order: str = 'asc', role: str = None) -> List[models.User]:
    query = db.query(models.User)
    
    if role:
        query = query.filter(models.User.Role == role)
    
    if sort_by:
        if sort_by == 'Name':
            sort_column = models.User.FirstName
        elif sort_by == 'CreatedDate':
            sort_column = models.User.CreatedDate
        if sort_order == 'desc':
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)
    
    return query.offset(skip).limit(limit).all()

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
    db_user = db.query(models.User).filter(models.User.UserID == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def create_URLToken(db: Session, userid:int): #to maintain security of the setpass URL
    try:
        token_value = generate_key("URL")

        one_day = datetime.now() + timedelta(hours=24)

        new_token = models.URLToken(
            value=token_value,
            UserID=userid,
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
    # drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == batch.DryingID).first()
    flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == batch.FlouringID).first()
    dried_leaves = db.query(models.DriedLeaves).filter(models.DriedLeaves.DriedDate == batch.DriedDate).first()
    
    db_batch = models.ProcessedLeaves(
        CentraID=batch.CentraID,
        Weight=batch.Weight,
        DryingID=batch.DryingID,
        FlouringID=batch.FlouringID,
        DriedDate=dried_leaves.DriedDate if dried_leaves else None,
        FlouredDate=flouring_activity.Date if flouring_activity else None,
        Shipped=batch.Shipped
        # dried_leaf=dried_leaves  # Assign the fetched DriedLeaves instance
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_all_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).offset(skip).limit(limit).all()

def get_batches_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.creator_id == creator_id).offset(skip).limit(limit).all()

def get_batches_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.user_id == user_id).offset(skip).limit(limit).all()

def get_batch_by_id(db: Session, batch_id: int):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()

#update batch
def update_batch(db: Session, batch_id: str, update_data: schemas.ProcessedLeavesUpdate):
    db_batch = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()
    if db_batch:
        for key, value in update_data.dict().items():
            setattr(db_batch, key, value)
        db.commit()
        db.refresh(db_batch)
    return db_batch

def delete_batch(db: Session, batch_id: int):
    batch = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()
    if batch:
        db.delete(batch)
        db.commit()
        return {"message": "Batch successfully deleted"}
    return None

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

# DRYING MACHINE
def create_drying_machine(db: Session, drying_machine: schemas.DryingMachineCreate):
    db_drying_machine = models.DryingMachine(
        # MachineID=drying_machine.MachineID,
        CentraID=drying_machine.CentraID,
        Capacity=drying_machine.Capacity,
        Status=drying_machine.Status,
        Duration=drying_machine.Duration
    )
    db.add(db_drying_machine)
    db.commit()
    db.refresh(db_drying_machine)
    return db_drying_machine

def get_all_drying_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DryingMachine).offset(skip).limit(limit).all()

def get_drying_machines_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.DryingMachine).filter(models.DryingMachine.creator_id == creator_id).offset(skip).limit(limit).all()

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

def add_new_drying_activity(db: Session, drying_activity: schemas.DryingActivityCreate):
    db_drying_activity = models.DryingActivity(
        # DryingID=drying_activity.DryingID,
        # UserID=drying_activity.UserID,
        CentralID=drying_activity.CentralID,
        # Date=drying_activity.Date,
        Weight=drying_activity.Weight,
        DryingMachineID=drying_activity.DryingMachineID,
        Time=drying_activity.Time
    )

    db.add(db_drying_activity)
    db.commit()
    db.refresh(db_drying_activity)
    return db_drying_activity

def get_all_drying_activity(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DryingActivity).offset(skip).limit(limit).all()

def get_drying_activity(db: Session, drying_id: int):
    drying= db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if not drying:
        raise HTTPException(status_code=404, detail="Drying Activity not found")
    return drying

# def get_drying_activity_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
#     return db.query(models.DryingActivity).filter(models.DryingActivity.creator_id == creator_id).offset(skip).limit(limit).all()

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

#driedleaves

def get_dried_leaves(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DriedLeaves).offset(skip).limit(limit).all()

def get_dried_leaf(db: Session, leaf_id: int):
    return db.query(models.DriedLeaves).filter(models.DriedLeaves.id == leaf_id).first()

def get_dried_leaves_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.DriedLeaves).filter(models.DriedLeaves.CentraID == creator_id).offset(skip).limit(limit).all()

def create_dried_leaf(db: Session, dried_leaf: schemas.DriedLeavesCreate):
    db_dried_leaf = models.DriedLeaves(**dried_leaf.dict())
    db.add(db_dried_leaf)
    db.commit()
    db.refresh(db_dried_leaf)
    return db_dried_leaf

def update_dried_leaf(db: Session, leaf_id: int, dried_leaf: schemas.DriedLeavesUpdate):
    db_dried_leaf = db.query(models.DriedLeaves).filter(models.DriedLeaves.id == leaf_id).first()
    if not db_dried_leaf:
        return None
    update_data = dried_leaf.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dried_leaf, key, value)
    db.commit()
    db.refresh(db_dried_leaf)
    return db_dried_leaf

def delete_dried_leaf(db: Session, leaf_id: int):
    db_dried_leaf = db.query(models.DriedLeaves).filter(models.DriedLeaves.id == leaf_id).first()
    if db_dried_leaf:
        db.delete(db_dried_leaf)
        db.commit()
        return db_dried_leaf
    return None

# MACHINES - FLOURING
def add_new_flouring_machine(db: Session, flouring_machine: schemas.FlouringMachineCreate):
    db_flouring_machine = models.FlouringMachine(
        # MachineID=flouring_machine.MachineID,
        CentraID=flouring_machine.CentraID,
        Capacity=flouring_machine.Capacity,
        Status=flouring_machine.Status,
        Duration=flouring_machine.Duration
    )
    db.add(db_flouring_machine)
    db.commit()
    db.refresh(db_flouring_machine)
    return db_flouring_machine

def get_all_flouring_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringMachine).offset(skip).limit(limit).all()

def get_flouring_machine_status(db: Session, machine_id: str):
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if machine:
        return machine.Status
    return None

def get_flouring_machines_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringMachine).filter(models.FlouringMachine.creator_id == creator_id).offset(skip).limit(limit).all()

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

def delete_flouring_machine(db: Session, machine_id: str):
    db_flouring_machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if db_flouring_machine:
        db.delete(db_flouring_machine)
        db.commit()
    return db_flouring_machine

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

def get_flouring_activity_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.creator_id == creator_id).offset(skip).limit(limit).all()

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
# def add_shipment(db: Session, shipment_data: schemas.ShipmentCreate):
#     db_shipment_data = models.Shipment(
#         batch_id=shipment_data.batch_id,
#         description=shipment_data.description,
#         status=shipment_data.status,
#         weight=shipment_data.weight,
#         issue_description=shipment_data.issue_description
        
#     )
#     db.add(db_shipment_data)
#     db.commit()
#     db.refresh(db_shipment_data)
#     return db_shipment_data

# def update_shipment(db: Session, shipment_id: int, shipment_update: schemas.ShipmentUpdate):
#     db_shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
#     if db_shipment:
#         update_data = shipment_update.dict(exclude_unset=True)
#         for key, value in update_data.items():
#             setattr(db_shipment, key, value)
#         db.commit()
#         db.refresh(db_shipment)
#     else:
#         raise HTTPException(status_code=404, detail="Shipment not found")
#     return db_shipment


# def get_all_shipments(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Shipment).offset(skip).limit(limit).all()

# def get_shipment_details(db: Session, shipment_id: str):
#     return db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()

# def delete_shipment(db: Session, shipment_id: str):
#     shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
#     if shipment:
#         db.delete(shipment)
#         db.commit()
#     return shipment

# def confirm_shipment(db: Session, shipment_id: int, weight: int):
#     shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
#     if shipment:
#         shipment.status = 'Confirmed'
#         shipment.weight = weight
#         db.commit()
#         return shipment
#     return None


# def report_shipment_issue(db: Session, shipment_id: int, description: str):
#     shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
#     if shipment:
#         shipment.issue_description = description
#         db.commit()
#         return shipment
#     return None

# def rescale_shipment(db: Session, shipment_id: int, new_weight: float):
#     shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
#     if shipment:
#         shipment.weight = new_weight
#         db.commit()
#         db.refresh(shipment)
#         return True
#     return False

#pickup
def get_pickup(db: Session, pickup_id: int):
    return db.query(models.Pickup).filter(models.Pickup.id == pickup_id).first()

def get_all_pickups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Pickup).offset(skip).limit(limit).all()

def create_pickup(db: Session, pickup: schemas.PickupCreate):
    db_pickup = models.Pickup(**pickup.dict())
    db.add(db_pickup)
    db.commit()
    db.refresh(db_pickup)
    return db_pickup

def update_pickup(db: Session, pickup_id: int, pickup: schemas.PickupBase):
    db_pickup = db.query(models.Pickup).filter(models.Pickup.id == pickup_id).first()
    if db_pickup:
        for key, value in pickup.dict(exclude_unset=True).items():
            setattr(db_pickup, key, value)
        db.commit()
        db.refresh(db_pickup)
    return db_pickup

def delete_pickup(db: Session, pickup_id: int):
    db_pickup = db.query(models.Pickup).filter(models.Pickup.id == pickup_id).first()
    if db_pickup:
        db.delete(db_pickup)
        db.commit()
    return db_pickup


# STOCKS
def get_all_stocks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Stock).offset(skip).limit(limit).all()

def get_stock_detail(db: Session, location_id: int):
    return db.query(models.Stock).filter(models.Stock.location_id == location_id).first()

# LOCATIONS
def get_location_details(db: Session, location_id: int):
    return db.query(models.Location).filter(models.Location.id == location_id).first()

# SHIPMENT HISTORY
# def get_shipment_history(db: Session, location_id: int):
#     location = db.query(models.Location).filter(models.Location.id == location_id).first()
#     if location:
#         return location.shipment_history  # Make sure 'shipment_history' is correctly modeled
#     return []

# def validate_shipment_id(db: Session, shipment_id: int):
#     shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
#     return bool(shipment)

# def schedule_pickup(db: Session, pickup_data: ShipmentPickupSchedule):
#     pickup = models.PickupDetails(
#         shipment_id=pickup_data.shipment_id,
#         pickup_time=pickup_data.pickup_time,
#         location=pickup_data.location
#     )
#     db.add(pickup)
#     db.commit()
#     return True

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
        Address=centra.Address,
        FlouringSchedule=centra.FlouringSchedule
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
    db_centra = db.query(models.Centra).filter(models.Centra.CentralID == CentralID).first()
    if db_centra:
        db.delete(db_centra)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Centra not found")
    return {"message": "Centra deleted successfully"}

#notifications
def get_notifications(db: Session, centraid: int):
    return db.query(models.Notification).filter(models.Notification.centraid == centraid).all()

def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def mark_notification_as_read(db: Session, notification_id: int):
    db_notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if db_notification:
        db_notification.read = True
        db.commit()
        db.refresh(db_notification)
    return db_notification

def update_machine_status(db: Session, machine_id: int, new_status: str, machine_type: str):
    if machine_type == "drying":
        machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    elif machine_type == "flouring":
        machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    else:
        return None

    if machine:
        machine.Status = new_status
        db.commit()
        db.refresh(machine)
    return machine

#userCentra

def get_user_centra(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.UserCentra).offset(skip).limit(limit).all()

def get_user_centra_by_id(db: Session, user_centra_id: int):
    return db.query(models.UserCentra).filter(models.UserCentra.id == user_centra_id).first()

def get_user_centra_by_user_id(db: Session, user_id: int): 
    return db.query(models.UserCentra).filter(models.UserCentra.userID == user_id).first()

def create_user_centra(db: Session, user_centra: schemas.UserCentraCreate):
    db_user_centra = models.UserCentra(**user_centra.dict())
    db.add(db_user_centra)
    db.commit()
    db.refresh(db_user_centra)
    return db_user_centra

def update_user_centra(db: Session, user_centra_id: int, user_centra: schemas.UserCentraUpdate):
    db_user_centra = db.query(models.UserCentra).filter(models.UserCentra.id == user_centra_id).first()
    if db_user_centra:
        for key, value in user_centra.dict(exclude_unset=True).items():
            setattr(db_user_centra, key, value)
        db.commit()
        db.refresh(db_user_centra)
    return db_user_centra

def delete_user_centra(db: Session, user_centra_id: int):
    db_user_centra = db.query(models.UserCentra).filter(models.UserCentra.id == user_centra_id).first()
    if db_user_centra:
        db.delete(db_user_centra)
        db.commit()
    return db_user_centra

#HARBOUR GUARD
def create_harbor_guard(db: Session, harbor_guard: schemas.HarborGuardCreate):
    db_harbor_guard = models.HarborGuard(**harbor_guard.dict())
    db.add(db_harbor_guard)
    db.commit()
    db.refresh(db_harbor_guard)
    return db_harbor_guard

def get_harbor_guard(db: Session, harbour_id: int):
    return db.query(models.HarborGuard).filter(models.HarborGuard.HarbourID == harbour_id).first()

def update_harbor_guard(db: Session, harbour_id: int, harbor_guard: schemas.HarborGuardUpdate):
    db_harbor_guard = db.query(models.HarborGuard).filter(models.HarborGuard.HarbourID == harbour_id).first()
    if db_harbor_guard:
        for attr, value in harbor_guard.dict(exclude_unset=True).items():
            setattr(db_harbor_guard, attr, value)
        db.commit()
        db.refresh(db_harbor_guard)
    return db_harbor_guard

def delete_harbor_guard(db: Session, harbour_id: int):
    db_harbor_guard = db.query(models.HarborGuard).filter(models.HarborGuard.HarbourID == harbour_id).first()
    if db_harbor_guard:
        db.delete(db_harbor_guard)
        db.commit()
    return db_harbor_guard

def get_all_harbor_guards(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.HarborGuard).offset(skip).limit(limit).all()
    
# WAREHOUSE LOCATION
def create_warehouse(db: Session, warehouse_data: schemas.WarehouseCreate):
    db_warehouse = models.Warehouse(
        # warehouseName=warehouse_data.warehouseName,
        email=warehouse_data.email,
        phone=warehouse_data.phone,
        TotalStock=warehouse_data.TotalStock,
        Capacity=warehouse_data.Capacity,
        location=warehouse_data.location,
        created_at=warehouse_data.created_at
    )
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def get_all_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Warehouse]:
    return db.query(models.Warehouse).offset(skip).limit(limit).all()

def get_warehouse(db: Session, warehouse_id: int) -> Optional[models.Warehouse]:
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

#xyzuser

def get_xyzusers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.XYZuser).offset(skip).limit(limit).all()

def get_xyzuser_by_id(db: Session, xyzuser_id: int):
    return db.query(models.XYZuser).filter(models.XYZuser.id == xyzuser_id).first()

def create_xyzuser(db: Session, xyzuser: schemas.XYZuserCreate):
    db_xyzuser = models.XYZuser(**xyzuser.dict())
    db.add(db_xyzuser)
    db.commit()
    db.refresh(db_xyzuser)
    return db_xyzuser

def update_xyzuser(db: Session, xyzuser_id: int, xyzuser: schemas.XYZuserUpdate):
    db_xyzuser = db.query(models.XYZuser).filter(models.XYZuser.id == xyzuser_id).first()
    if db_xyzuser is None:
        return None
    for key, value in xyzuser.dict().items():
        setattr(db_xyzuser, key, value)
    db.commit()
    db.refresh(db_xyzuser)
    return db_xyzuser

def delete_xyzuser(db: Session, xyzuser_id: int):
    db_xyzuser = db.query(models.XYZuser).filter(models.XYZuser.id == xyzuser_id).first()
    if db_xyzuser is None:
        return None
    db.delete(db_xyzuser)
    db.commit()
    return db_xyzuser

# WET LEAVES COLLECTIONS
def add_new_wet_leaves_collection(db: Session, wet_leaves_collection: schemas.WetLeavesCollectionCreate):
    db_wet_leaves_collection = models.WetLeavesCollection(
        # WetLeavesBatchID=wet_leaves_collection.WetLeavesBatchID,
        # UserID=wet_leaves_collection.UserID,
        CentralID=wet_leaves_collection.CentralID,
        Date=wet_leaves_collection.Date,
        Time=wet_leaves_collection.Time,
        Weight=wet_leaves_collection.Weight,
        Status=wet_leaves_collection.Status,
        Expired=wet_leaves_collection.Expired,
        Dried=wet_leaves_collection.Dried
        # Duration=wet_leaves_collection.Duration
        # ExpirationTime=wet_leaves_collection.ExpirationTime
    )
    db.add(db_wet_leaves_collection)
    db.commit()
    db.refresh(db_wet_leaves_collection)
    return db_wet_leaves_collection

def get_all_wet_leaves_collections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WetLeavesCollection).offset(skip).limit(limit).all()

def get_wet_leaves_collections_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.CentralID == creator_id).offset(skip).limit(limit).all()

def get_wet_leaves_weight_by_status(db: Session, creator_id: int):
    statuses = ['near expiry', 'drying', 'fresh']
    weights = {}
    
    for status in statuses:
        total_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
            models.WetLeavesCollection.CentralID == creator_id,
            models.WetLeavesCollection.Status == status
        ).scalar()
        
        weights[status] = total_weight or 0  # Ensure the result is zero if no records found
    
    return weights

def get_wet_conversion_rate(db: Session, centraID: int):  #based on each centra 
    # Total weight of expired wet leaves
    expired_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
        models.WetLeavesCollection.CentralID == centraID, 
        models.WetLeavesCollection.Status == 'expired'
    ).scalar() or 0

    # Total weight of dried leaves
    dried_weight = db.query(func.sum(models.DriedLeaves.Weight)).filter(
        models.DriedLeaves.CentraID == centraID
    ).scalar() or 0

    conversion_rate = (dried_weight / expired_weight) * 100 if expired_weight > 0 else 0
    return conversion_rate

def get_dry_conversion_rate(db: Session, centraID: int):
     # Total weight of expired wet leaves
    expired_weight = db.query(func.sum(models.DriedLeaves.Weight)).filter(
        models.DriedLeaves.CentraID == centraID, 
        models.DriedLeaves.Floured == False
    ).scalar() or 0

    # Total weight of dried leaves
    dried_weight = db.query(func.sum(models.ProcessedLeaves.Weight)).filter(
        models.ProcessedLeaves.CentraID == centraID
    ).scalar() or 0

    conversion_rate = (dried_weight / expired_weight) * 100 if expired_weight > 0 else 0
    return conversion_rate

def get_wet_leaves_collection(db: Session, wet_leaves_batch_id: int):
    return db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()

def update_wet_leaves_collection(db: Session, wet_leaves_batch_id: str, update_data: schemas.WetLeavesCollectionUpdate):
    db_wet_leaves_collection = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()
    if db_wet_leaves_collection:
        for key, value in update_data.dict().items():
            setattr(db_wet_leaves_collection, key, value)
        db.commit()
        db.refresh(db_wet_leaves_collection)
    return db_wet_leaves_collection

# def update_wet_leaves_collection(db: Session, wet_leaves_batch_id: int, update_data: schemas.WetLeavesCollectionUpdate):
#     db_record = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()
#     if not db_record:
#         raise HTTPException(status_code=404, detail="Record not found")
    
#     # Update fields based on the provided data
#     update_dict = update_data.dict(exclude_unset=True)
    
#     # Automatically set the status to 'Expired'
#     update_dict['Status'] = 'Expired'
    
#     for key, value in update_dict.items():
#         setattr(db_record, key, value)

#     db.commit()
#     db.refresh(db_record)
#     return db_record

def delete_wet_leaves_collection(db: Session, wet_leaves_batch_id: int):
    db_wet_leaves_collection = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.WetLeavesBatchID == wet_leaves_batch_id).first()
    if db_wet_leaves_collection:
        db.delete(db_wet_leaves_collection)
        db.commit()
    return db_wet_leaves_collection


#CentraShipment

# def create_shipment(db: Session, shipment: schemas.CentraShipmentCreate):
#     db_shipment = models.CentraShipment(
#         ShippingMethod=shipment.ShippingMethod,
#         AirwayBill=shipment.AirwayBill
#     )
#     db.add(db_shipment)
#     db.commit()
#     db.refresh(db_shipment)
    
#     if shipment.batch_ids:
#         for batch_id in shipment.batch_ids:
#             batch = db.query(models.ProcessedLeaves).get(batch_id)
#             if batch:
#                 db_shipment.batches.append(batch)
#         db.commit()
    
#     return db_shipment

# def get_shipment(db: Session, shipment_id: int):
#     return db.query(models.CentraShipment).filter(models.CentraShipment.id == shipment_id).first()

# def delete_shipment(db: Session, shipment_id: int):
#     db_shipment = db.query(models.CentraShipment).filter(models.CentraShipment.id == shipment_id).first()
#     if db_shipment:
#         db.delete(db_shipment)
#         db.commit()
#         return True
#     return False

#expedition
# def get_latest_checkpoint(db: Session, expedition_id: int):
#     return db.query(models.CheckpointStatus).filter(models.CheckpointStatus.expeditionid == expedition_id).order_by(models.CheckpointStatus.statusdate.desc()).first()

# def get_all_checkpoints(db:Session,expedition_id: int):
#     return db.query(models.CheckpointStatus).filter(models.CheckpointStatus.expeditionid==expedition_id).all()
def get_expeditions_by_central_id(db: Session, central_id: int):
    return db.query(models.Expedition).filter(models.Expedition.CentralID == central_id).all()


def get_expedition_with_batches(db: Session, expedition_id: int):
    return (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.ProcessedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            models.CheckpointStatus.status, # Include CheckpointStatus in the query
            models.CheckpointStatus.statusdate  # Include CheckpointStatus in the query
        )
        .join(models.Expedition.content)  # Join to ExpeditionContent through the relationship
        .join(models.ExpeditionContent.batch)  # Join to ProcessedLeaves through the relationship
        .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)  # Outer join to CheckpointStatus
        .filter(models.Expedition.ExpeditionID == expedition_id)
        .options(joinedload(models.Expedition.content))  # Ensure content relationship is loaded
        .all()
    )

def get_all_expedition_with_batches(db: Session, skip:int, limit:0):
 
  return (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.ProcessedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            models.CheckpointStatus.status,
            models.CheckpointStatus.statusdate
        )
        .join(models.Expedition.content)
        .join(models.ExpeditionContent.batch)
        .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)
        .options(joinedload(models.Expedition.content))
        .offset(skip)
        .limit(limit)
        .all()
    )
    

# def get_expedition_batches(db: Session, expedition_id: int):
#     return db.query(models.ExpeditionContent.BatchID, models.ProcessedLeaves.Weight).join(models.ProcessedLeaves, models.ExpeditionContent.BatchID == models.ProcessedLeaves.ProductID).filter(models.ExpeditionContent.ExpeditionID == expedition_id).all()

# def get_expedition_batches(db: Session, expedition_id: int):
#     return db.query(
#         models.Expedition.ExpeditionID,
#         models.Expedition.AirwayBill,
#         models.Expedition.EstimatedArrival,
#         models.Expedition.TotalPackages,
#         models.Expedition.TotalWeight,
#         models.Expedition.Status,
#         models.Expedition.ExpeditionDate,
#         models.Expedition.ExpeditionServiceDetails,
#         models.Expedition.CentralID,
#         models.ExpeditionContent.BatchID,
#         models.ProcessedLeaves.Weight
#     ).join(
#         models.ExpeditionContent, models.Expedition.ExpeditionID == models.ExpeditionContent.ExpeditionID
#     ).join(
#         models.ProcessedLeaves, models.ExpeditionContent.BatchID == models.ProcessedLeaves.ProductID
#     ).filter(
#         models.Expedition.ExpeditionID == expedition_id
#     ).all()

# def get_all_expeditions_with_batches(db: Session, skip: int = 0, limit: int = 100):
#     expeditions = db.query(models.Expedition).offset(skip).limit(limit).all()
#     for expedition in expeditions:
#         expedition.batches = get_expedition_batches(db, expedition.ExpeditionID)
#     return expeditions

# def get_expedition(db: Session, expedition_id: int): #only with latest checkpoint status, not complete checkpoint
#     expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
#     if expedition is None:
#         return None
#     batches = get_expedition_batches(db, expedition_id)
#     checkpoint = get_latest_checkpoint(db,expedition_id)
    
#     return {
#         "expedition": expedition,
#         "batches": [batch for batch in batches],
#         "status": checkpoint.status,
#         "checkpoint_statusdate": checkpoint.statusdate,
#         "checkpoint": f"{checkpoint.status} | {checkpoint.statusdate}"
#     }



def get_expeditions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Expedition).offset(skip).limit(limit).all()

# def get_all_expeditions_with_batches(db: Session, skip: int = 0, limit: int = 100):
#     expeditions = get_expeditions(db=db, skip=skip, limit=limit)
#     result = []
#     for expedition in expeditions:
#         expedition_data = get_expedition(db, expedition.ExpeditionID)
#         result.append(expedition_data)
#     return result


# def get_all_expeditions_with_batches_by_centra(db: Session, centra_id: int = None, skip: int = 0, limit: int = 100):
#     expeditions = get_expeditions_by_centra(db=db, centra_id=centra_id, skip=skip, limit=limit)
#     result = []
#     for expedition in expeditions:
#         expedition_data = get_expedition(db, expedition.ExpeditionID)
#         result.append(expedition_data)
#     return result

def create_expedition(db: Session, expedition: schemas.ExpeditionCreate, user: schemas.User):
    # Fetch the user including their related Centra
    
    
    # Assuming you have a direct relationship to Centra or a method to fetch it
    
    centra_id = user["centralID"]
  

    # Create the expedition object with CentraID included
    db_expedition = models.Expedition(**expedition.dict(), CentralID=centra_id)
    
    # Add to session, commit, and refresh
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
    if db_expedition:
        db.delete(db_expedition)
        db.commit()
        return {"message": "Expedition deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Expedition not found")

def change_expedition_status(db: Session, expedition_id: int, new_status: str):
    expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if expedition:
        expedition.Status = new_status
        db.commit()
        return expedition
    return None

def confirm_expedition(db: Session, expedition_id: int, TotalWeight: int):
    expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if expedition:
        expedition.Status = 'Completed'
        expedition.TotalWeight = TotalWeight 
        db.commit()
        return expedition
    return None


#expeditioncontent

def get_expedition_content(db: Session, expedition_content_id: int):
    return db.query(models.ExpeditionContent).filter(models.ExpeditionContent.id == expedition_content_id).first()

def get_expedition_contents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ExpeditionContent).offset(skip).limit(limit).all()

def create_expedition_content(db: Session, expedition_content: models.ExpeditionContent):
    db.add(expedition_content)
    db.commit()
    db.refresh(expedition_content)
    return expedition_content



def update_expedition_content(db: Session, expedition_content_id: int, expedition_content: schemas.ExpeditionContentUpdate):
    db_expedition_content = db.query(models.ExpeditionContent).filter(models.ExpeditionContent.id == expedition_content_id).first()
    if db_expedition_content:
        for key, value in expedition_content.dict(exclude_unset=True).items():
            setattr(db_expedition_content, key, value)
        db.commit()
        db.refresh(db_expedition_content)
    return db_expedition_content

def delete_expedition_content(db: Session, expedition_content_id: int):
    db_expedition_content = db.query(models.ExpeditionContent).filter(models.ExpeditionContent.id == expedition_content_id).first()
    if db_expedition_content:
        db.delete(db_expedition_content)
        db.commit()
    return db_expedition_content

#checkpointstatus
def create_checkpoint_status(db: Session, checkpoint_status: schemas.CheckpointStatusCreate):
    db_checkpoint_status = models.CheckpointStatus(**checkpoint_status.dict())
    db.add(db_checkpoint_status)
    db.commit()
    db.refresh(db_checkpoint_status)
    return db_checkpoint_status

# Read operation
def get_checkpoint_status(db: Session, checkpoint_id: int):
    return db.query(models.CheckpointStatus).filter(models.CheckpointStatus.id == checkpoint_id).first()

def get_all_checkpoint_statuses(db: Session) -> List[models.CheckpointStatus]:
    return db.query(models.CheckpointStatus).all()

# Update operation
def update_checkpoint_status(db: Session, checkpoint_id: int, checkpoint_status: schemas.CheckpointStatusCreate):
    db_checkpoint_status = db.query(models.CheckpointStatus).filter(models.CheckpointStatus.id == checkpoint_id).first()
    if db_checkpoint_status:
        for key, value in checkpoint_status.dict(exclude_unset=True).items():
            setattr(db_checkpoint_status, key, value)
        db.commit()
        db.refresh(db_checkpoint_status)
    return db_checkpoint_status

# Delete operation
def delete_checkpoint_status(db: Session, checkpoint_id: int):
    db_checkpoint_status = db.query(models.CheckpointStatus).filter(models.CheckpointStatus.id == checkpoint_id).first()
    if db_checkpoint_status:
        db.delete(db_checkpoint_status)
        db.commit()
    return db_checkpoint_status

#receveid packages
# def get_received_package(db: Session, package_id: int):
#     return db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()

# def get_received_packages(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.ReceivedPackage).offset(skip).limit(limit).all()

# def create_received_package(db: Session, received_package: schemas.ReceivedPackageCreate):
#     db_received_package = models.ReceivedPackage(**received_package.dict())
#     db.add(db_received_package)
#     db.commit()
#     db.refresh(db_received_package)
#     return db_received_package

# def update_received_package(db: Session, package_id: int, received_package: schemas.ReceivedPackageUpdate):
#     db_received_package = db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()
#     if not db_received_package:
#         return None
#     for key, value in received_package.dict(exclude_unset=True).items():
#         setattr(db_received_package, key, value)
#     db.commit()
#     db.refresh(db_received_package)
#     return db_received_package

# def delete_received_package(db: Session, package_id: int):
#     db_received_package = db.query(models.ReceivedPackage).filter(models.ReceivedPackage.PackageID == package_id).first()
#     if not db_received_package:
#         return None
#     db.delete(db_received_package)
#     db.commit()
#     return db_received_package


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

#admin
def get_admin(db: Session, admin_id: int):
    return db.query(models.Admin).filter(models.Admin.id == admin_id).first()

def get_admin_by_email(db: Session, email: str):
    return db.query(models.Admin).filter(models.Admin.email == email).first()

def get_admins(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Admin).offset(skip).limit(limit).all()

def create_admin(db: Session, admin: schemas.AdminCreate):
    db_admin = models.Admin(**admin.dict())
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def update_admin(db: Session, admin_id: int, admin: schemas.AdminUpdate):
    db_admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if db_admin:
        update_data = admin.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_admin, key, value)
        db.commit()
        db.refresh(db_admin)
    return db_admin

def delete_admin(db: Session, admin_id: int):
    db_admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if db_admin:
        db.delete(db_admin)
        db.commit()
    return db_admin