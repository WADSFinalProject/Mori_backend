from sqlalchemy.orm import Session, joinedload, aliased
import models, schemas
from fastapi import HTTPException
from typing import List, Optional
from passlib.context import CryptContext
from security import get_hash, generate_key,  decrypt_token, encrypt_token
import traceback
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_
from datetime import datetime
from collections import defaultdict

from datetime import datetime, timedelta, time

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
    # flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == batch.FlouringID).first()
    dried_leaves = db.query(models.DriedLeaves).filter(models.DriedLeaves.id == batch.DriedID).first()
    
    db_batch = models.ProcessedLeaves(
        CentraID=batch.CentraID,
        Weight=batch.Weight,
        # DriedID=batch.DriedID,
        # DryingID=batch.DryingID,
        # FlouringID=batch.FlouringID,
        DriedID=dried_leaves.id if dried_leaves else None,
        FlouredDate=batch.FlouredDate,
        Shipped=batch.Shipped
        # dried_leaf=dried_leaves  # Assign the fetched DriedLeaves instance
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

# def get_all_batches(db: Session, skip: int = 0, limit: int = 100):
#     query = db.query(models.ProcessedLeaves)
#     return query.offset(skip).limit(limit).all()

def get_all_batches(db: Session, central_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(
        models.ProcessedLeaves,
        models.DriedLeaves.DriedDate
    ).join(
        models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id
    )
    
    if central_id is not None:
        query = query.filter(models.ProcessedLeaves.CentraID == central_id)
        
    result = query.offset(skip).limit(limit).all()
    
    # Format the result to include DriedDate in the response
    formatted_result = []
    for processed_leaves, dried_date in result:
        processed_leaves_dict = {
            "ProductID": processed_leaves.ProductID,
            "CentraID": processed_leaves.CentraID,
            "DriedID": processed_leaves.DriedID,
            "Weight": processed_leaves.Weight,
            "FlouredDate": processed_leaves.FlouredDate,
            "Shipped": processed_leaves.Shipped,
            "DriedDate": dried_date  # Add DriedDate to the dictionary
        }
        formatted_result.append(processed_leaves_dict)
    
    return formatted_result



def get_batches_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.user_id == user_id).offset(skip).limit(limit).all()

def get_batch_by_id(db: Session, batch_id: int):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()

#update batch
def update_batch_shipped(db: Session, batch_ids: List[int]):
    batches = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID.in_(batch_ids)).all()
    for batch in batches:
        batch.Shipped = True  # Assuming you want to update the 'Shipped' attribute
    db.commit()
    return batches

def delete_batch(db: Session, batch_id: int):
    batch = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == batch_id).first()
    if batch:
        db.delete(batch)
        db.commit()
        return {"message": "Batch successfully deleted"}
    return None

def batch_get_dried_date(db: Session, productId: str):
    activity = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == productId).first()
    if activity:
        db.query(models.DriedLeaves.DriedDate).join(models.ProcessedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id).filter(models.ProcessedLeaves.ProductID == productId).first()
    return None

def batch_get_floured_date(db: Session, productId: str):
    activity = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == productId).first()
    if activity:
        return activity.FlouredDate
    return None

# DRYING MACHINE
def create_drying_machine(db: Session, drying_machine: schemas.DryingMachineCreate):
    db_drying_machine = models.DryingMachine(
        # MachineID=drying_machine.MachineID,
        CentraID=drying_machine.CentraID,
        Capacity=drying_machine.Capacity,
        # Load=drying_machine.Load,
        Status=drying_machine.Status,
        Duration=drying_machine.Duration
    )
    db.add(db_drying_machine)
    db.commit()
    db.refresh(db_drying_machine)
    return db_drying_machine

def get_all_drying_machines(db: Session, centra_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.DryingMachine)
    if centra_id is not None:
        query = query.filter(models.DryingMachine.CentraID == centra_id)
    return query.offset(skip).limit(limit).all()

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

def update_drying_machine_status(db: Session, machine_id: int, new_status: str):
    # Fetch the drying machine record by ID
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Drying Machine not found")

    # Validate the new status
    valid_statuses = ['idle', 'running', 'finished']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Update the status
    machine.Status = new_status
    db.commit()
    db.refresh(machine)
    return machine

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
        machine.Status = 'finished'
        db.commit()
        db.refresh(machine)
        return True
    return False

def add_new_drying_activity(db: Session, drying_activity: schemas.DryingActivityCreate, user: dict):
    db_drying_activity = models.DryingActivity(
        # DryingID=drying_activity.DryingID,
        # UserID=drying_activity.UserID,
        CentralID=user["centralID"],
        # Date=drying_activity.Date,
        Weight=drying_activity.Weight,
        DryingMachineID=drying_activity.DryingMachineID,
        EndTime=drying_activity.EndTime,
        InUse=drying_activity.InUse
    )

    db.add(db_drying_activity)
    db.commit()
    db.refresh(db_drying_activity)
    return db_drying_activity

def get_all_drying_activity(db: Session, central_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.DryingActivity)
    if central_id is not None:
        query = query.filter(models.DryingActivity.CentralID == central_id)
    return query.offset(skip).limit(limit).all()

def get_drying_activity(db: Session, drying_id: int):
    drying= db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if not drying:
        raise HTTPException(status_code=404, detail="Drying Activity not found")
    return drying

def get_drying_activities_by_machine_id(db: Session, machine_id: int):
    return db.query(models.DryingActivity).filter(models.DryingActivity.DryingMachineID == machine_id).all()

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

def get_all_dried_leaves(db: Session, central_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.DriedLeaves)
    
    if central_id is not None:
        query = query.filter(models.DriedLeaves.CentraID == central_id)
    
    return query.offset(skip).limit(limit).all()

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

def update_in_machine_status(db: Session, leaf_id: int, in_machine: bool):
    dried_leaves = db.query(models.DriedLeaves).filter(models.DriedLeaves.id == leaf_id).first()
    if not dried_leaves:
        raise Exception(f"No dried leaves found with id {id}")
    
    dried_leaves.InMachine = in_machine
    db.commit()
    db.refresh(dried_leaves)
    return dried_leaves

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
        Load=flouring_machine.Load,
        Status=flouring_machine.Status,
        Duration=flouring_machine.Duration
    )
    db.add(db_flouring_machine)
    db.commit()
    db.refresh(db_flouring_machine)
    return db_flouring_machine

def get_all_flouring_machines(db: Session, centra_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.FlouringMachine)
    if centra_id is not None:
        query = query.filter(models.FlouringMachine.CentraID == centra_id)
    return query.offset(skip).limit(limit).all()

def get_flouring_machine_status(db: Session, machine_id: str):
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if machine:
        return machine.Status
    return None

def update_flouring_machine(db: Session, machine_id: int, machine_update: schemas.FlouringMachineUpdate):
    # Fetch the FlouringMachine record by ID
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail="Flouring Machine not found")

    # Update the fields
    if machine_update.Capacity is not None:
        machine.Capacity = machine_update.Capacity
    machine.Load = machine_update.Load

    db.commit()
    db.refresh(machine)
    return machine
    
def update_flouring_machine_status(db: Session, machine_id: int, new_status: str):
    machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Flouring Machine not found")

    valid_statuses = ['idle', 'running', 'finished']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    machine.Status = new_status
    db.commit()
    db.refresh(machine)
    return machine

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
        machine.Status = 'finished'
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
        Weight=flouring_activity.Weight,
        FlouringMachineID=flouring_activity.FlouringMachineID,
        EndTime=flouring_activity.EndTime,
        DriedDate=flouring_activity.DriedDate,
        InUse=flouring_activity.InUse
    )
    db.add(db_flouring_activity)
    db.commit()
    db.refresh(db_flouring_activity)
    return db_flouring_activity

# def get_all_flouring_activity(db: Session, CentralID: int, skip: int = 0, limit: int = 100):
#     return db.query(models.FlouringActivity).filter(models.FlouringActivity.CentralID == CentralID).offset(skip).limit(limit).all()

def get_all_flouring_activity(db: Session, central_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.FlouringActivity)
    
    if central_id is not None:
        query = query.filter(models.FlouringActivity.CentralID == central_id)
    
    return query.offset(skip).limit(limit).all()

def get_flouring_activity_by_creator(db: Session, creator_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.CentralID == creator_id).offset(skip).limit(limit).all()

def get_flouring_activities_by_machine_id(db: Session, machine_id: int):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringMachineID == machine_id).all()

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

def get_flouring_activity_by_id(flouring_id: int, db: Session):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()

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

def create_pickup_by_airwaybill(db: Session, airwaybill: str, pickup: schemas.PickupCreateAirway):
    expedition = db.query(models.Expedition).filter(models.Expedition.AirwayBill == airwaybill).first()

    if not expedition:
        raise HTTPException(status_code=404, detail=f"No expedition found with AirwayBill {airwaybill}")

    new_pickup = models.Pickup(
        expeditionID=expedition.ExpeditionID,
        warehouseid=pickup.warehouseid,
        pickup_time=pickup.pickup_time
    )

    db.add(new_pickup)
    db.commit()
    db.refresh(new_pickup)
    return new_pickup

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
        # FlouringSchedule=centra.FlouringSchedule
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
def get_all_notifications(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.Notification]:
    return db.query(models.Notification).offset(skip).limit(limit).all()

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


#expeditionNotif

def get_all_expnotifications(db: Session, skip: int = 0, limit: int = 100) -> List[models.ExpeditionNotification]:
    return db.query(models.ExpeditionNotification).offset(skip).limit(limit).all()

def get_expedition_notifications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ExpeditionNotification).offset(skip).limit(limit).all()

#userCentra

def get_all_user_centra_with_user(db: Session) -> List[schemas.UserCentraWithUser]:
    results = db.query(models.UserCentra, models.User) \
                .join(models.User, models.UserCentra.userID == models.User.UserID) \
                .all()
    
    user_centra_with_users = []
    for user_centra, user in results:
        user_centra_dict = {**user_centra.__dict__}
        user_dict = {**user.__dict__}

        # Remove SQLAlchemy-specific attribute
        user_centra_dict.pop('_sa_instance_state', None)
        user_dict.pop('_sa_instance_state', None)

        # Extract only necessary fields for UserCentra and UserforCentra
        user_centra_data = schemas.UserCentra(**user_centra_dict)
        user_data = schemas.UserforCentra(**user_dict)

        user_centra_with_user = schemas.UserCentraWithUser(usercentra=user_centra_data, user=user_data)
        user_centra_with_users.append(user_centra_with_user)

    return user_centra_with_users

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
    # Ensure created_at is set to the current date if it's not provided
    if warehouse_data.created_at is None:
        warehouse_data.created_at = datetime.utcnow().date()

    # Create the Warehouse instance
    db_warehouse = models.Warehouse(
        email=warehouse_data.email,
        phone=warehouse_data.phone,
        TotalStock=warehouse_data.TotalStock,
        Capacity=500,  # Set capacity to a fixed value of 500
        location=warehouse_data.location,
        created_at=warehouse_data.created_at
    )

    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

# def get_all_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Warehouse]:
#     return db.query(models.Warehouse).offset(skip).limit(limit).all()

def get_all_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.Warehouse]:
    warehouses = (
        db.query(models.Warehouse)
        .options(joinedload(models.Warehouse.stock_history))
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convert SQLAlchemy models to Pydantic models
    warehouses_data = []
    for warehouse in warehouses:
        stock_history_data = [
            schemas.WarehouseStockHistoryBase.from_orm(history) for history in warehouse.stock_history
        ]
        warehouse_data = schemas.Warehouse.from_orm(warehouse).dict()
        warehouse_data['stock_history'] = stock_history_data
        warehouses_data.append(schemas.Warehouse(**warehouse_data))

    return warehouses_data

def get_warehouse(db: Session, warehouse_id: int) -> Optional[models.Warehouse]:
    return db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()

def update_warehouse_id_by_airway_bill(db: Session, airway_bill: str, warehouse_id: int):
    # Query the Expedition based on AirwayBill
    expedition = db.query(models.Expedition).filter(models.Expedition.AirwayBill == airway_bill).first()
    
    if not expedition:
        # Handle case where Expedition with given AirwayBill is not found
        return None
    
    # Update the WarehouseID
    expedition.WarehouseID = warehouse_id
    
    # Commit the transaction to persist the changes
    db.commit()
    
    # Refresh the expedition object to reflect the updated state
    db.refresh(expedition)
    
    return expedition
    
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

def update_warehouse_stock(db: Session, warehouse_id: int, new_stock: int):
    # Fetch the warehouse
    warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise ValueError("Warehouse not found")

    # Calculate the change amount
    change_amount = new_stock - warehouse.TotalStock

    # Format the change amount to include + or - sign
    formatted_change_amount = f"{change_amount:+d}"

    # Log the old and new stock in the history table
    stock_history_entry = models.WarehouseStockHistory(
        warehouse_id=warehouse.id,
        old_stock=warehouse.TotalStock,
        new_stock=new_stock,
        change_amount=formatted_change_amount,
        change_date=datetime.utcnow()
    )
    db.add(stock_history_entry)

    # Update the total stock
    warehouse.TotalStock = new_stock

    # Commit the transaction
    db.commit()
    db.refresh(warehouse)

    return warehouse

def get_warehouse_stock_history(db: Session, warehouse_id: int):
    # Fetch the stock history for the warehouse
    stock_history = db.query(models.WarehouseStockHistory).filter(models.WarehouseStockHistory.warehouse_id == warehouse_id).all()
    return stock_history

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





from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import models, schemas

# def get_expedition_with_batches_by_airwaybill(db: Session, airwaybill: str) -> Optional[schemas.ExpeditionWithBatches]:
#     results = (
#         db.query(
#             models.Expedition,
#             models.ExpeditionContent.BatchID,
#             models.ProcessedLeaves.Weight,
#             models.DriedLeaves.DriedDate,
#             models.ProcessedLeaves.FlouredDate,
#             models.CheckpointStatus.status,
#             models.CheckpointStatus.statusdate
#         )
#         .join(models.Expedition.content)  # Join with ExpeditionContent
#         .join(models.ExpeditionContent.batch)  # Join with ProcessedLeaves
#         .join(models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id)  # Join with DriedLeaves
#         .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)  # Outer join with CheckpointStatus
#         .filter(models.Expedition.AirwayBill == airwaybill)  # Filter by AirwayBill
#         .options(joinedload(models.Expedition.content))  # Optimize loading of related content
#         .all()
#     )

#     if not results:
#         return None

#     expedition_data = None
#     batches = []

#     for result in results:
#         expedition, batch_id, weight, dried_date, floured_date, status, statusdate = result

#         if not expedition_data:
#             expedition_data = schemas.Expedition(
#                 ExpeditionID=expedition.ExpeditionID,
#                 AirwayBill=expedition.AirwayBill,
#                 EstimatedArrival=expedition.EstimatedArrival,
#                 TotalPackages=expedition.TotalPackages,
#                 TotalWeight=expedition.TotalWeight,
#                 Status=expedition.Status,
#                 ExpeditionDate=expedition.ExpeditionDate,
#                 ExpeditionServiceDetails=expedition.ExpeditionServiceDetails,
#                 CentralID=expedition.CentralID,
#             )

#         if not any(batch.BatchID == batch_id):
#             batches.append(
#                 schemas.Batch(
#                     BatchID=batch_id,
#                     Weight=weight,
#                     DriedDate=dried_date,
#                     FlouredDate=floured_date
#                 )
#             )

#     return schemas.ExpeditionWithBatches(
#         expedition=expedition_data,
#         batches=batches,
#         checkpoint_status=status,
#         checkpoint_statusdate=statusdate
#     )

def get_expedition_with_batches_by_airwaybill(db: Session, airwaybill: str) -> Optional[schemas.ExpeditionWithBatches]:
    # Subquery to get the latest statusdate for each expeditionid
    latest_status_subquery = (
        db.query(
            models.CheckpointStatus.expeditionid,
            func.max(models.CheckpointStatus.statusdate).label("latest_statusdate")
        )
        .group_by(models.CheckpointStatus.expeditionid)
        .subquery()
    )

    # Subquery to get the latest CheckpointStatus based on the latest statusdate
    latest_status = (
        db.query(
            models.CheckpointStatus
        )
        .join(
            latest_status_subquery,
            and_(
                models.CheckpointStatus.expeditionid == latest_status_subquery.c.expeditionid,
                models.CheckpointStatus.statusdate == latest_status_subquery.c.latest_statusdate
            )
        )
        .subquery()
    )

    # Main query to get the expeditions with batches and the latest checkpoint status
    results = (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.DriedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            latest_status.c.status,
            latest_status.c.statusdate
        )
        .join(models.Expedition.content)  # Join with ExpeditionContent
        .join(models.ExpeditionContent.batch)  # Join with ProcessedLeaves
        .join(models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id)  # Join with DriedLeaves
        .outerjoin(latest_status, latest_status.c.expeditionid == models.Expedition.ExpeditionID)  # Join with the latest CheckpointStatus
        .filter(models.Expedition.AirwayBill == airwaybill)  # Filter by AirwayBill
        .options(joinedload(models.Expedition.content))  # Optimize loading of related content
        .all()
    )

    if not results:
        return None

    expeditions_dict = defaultdict(lambda: {
        "expedition": None,
        "batches": [],
        "checkpoint_status": None,
        "checkpoint_statusdate": None
    })

    for result in results:
        expedition, batch_id, weight, dried_date, floured_date, status, statusdate = result
        expedition_id = expedition.ExpeditionID

        if expeditions_dict[expedition_id]["expedition"] is None:
            expeditions_dict[expedition_id]["expedition"] = schemas.Expedition(
                ExpeditionID=expedition.ExpeditionID,
                AirwayBill=expedition.AirwayBill,
                EstimatedArrival=expedition.EstimatedArrival,
                TotalPackages=expedition.TotalPackages,
                TotalWeight=expedition.TotalWeight,
                Status=expedition.Status,
                ExpeditionDate=expedition.ExpeditionDate,
                ExpeditionServiceDetails=expedition.ExpeditionServiceDetails,
                CentralID=expedition.CentralID,
                WarehouseID=expedition.WarehouseID
            )

        if status is not None:
            expeditions_dict[expedition_id]["checkpoint_status"] = status
            expeditions_dict[expedition_id]["checkpoint_statusdate"] = statusdate

        # Check if the batch is already in the list before appending
        if not any(batch.BatchID == batch_id for batch in expeditions_dict[expedition_id]["batches"]):
            expeditions_dict[expedition_id]["batches"].append(schemas.Batch(
                BatchID=batch_id,
                Weight=weight,
                DriedDate=dried_date,
                FlouredDate=floured_date
            ))

    return next(iter([schemas.ExpeditionWithBatches(**data) for data in expeditions_dict.values()]), None)
    
def get_all_expedition_with_batches(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.ExpeditionWithBatches]:
    results = (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.DriedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            models.CheckpointStatus.status,
            models.CheckpointStatus.statusdate
        )
        .join(models.Expedition.content)  # Join with ExpeditionContent
        .join(models.ExpeditionContent.batch)  # Join with ProcessedLeaves
        .join(models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id)  # Join with DriedLeaves
        .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)  # Optional join with CheckpointStatus
        .options(joinedload(models.Expedition.content))  # Optimize loading of related content
        .offset(skip)
        .limit(limit)
        .all()
    )

    expeditions_dict = {}

    for result in results:
        expedition, batch_id, weight, dried_date, floured_date, status, statusdate = result

        if expedition.ExpeditionID not in expeditions_dict:
            expeditions_dict[expedition.ExpeditionID] = {
                "expedition": schemas.Expedition(
                    ExpeditionID=expedition.ExpeditionID,
                    AirwayBill=expedition.AirwayBill,
                    EstimatedArrival=expedition.EstimatedArrival,
                    TotalPackages=expedition.TotalPackages,
                    TotalWeight=expedition.TotalWeight,
                    Status=expedition.Status,
                    ExpeditionDate=expedition.ExpeditionDate,
                    ExpeditionServiceDetails=expedition.ExpeditionServiceDetails,
                    CentralID=expedition.CentralID,
                    # Destination=expedition.Destination  # Assuming this field exists
                ),
                "batches": [],
                "checkpoint_status": status if status else None,
                "checkpoint_statusdate": statusdate if statusdate else None
            }

        expeditions_dict[expedition.ExpeditionID]["batches"].append(
            schemas.Batch(
                BatchID=batch_id,
                Weight=weight,
                DriedDate=dried_date,
                FlouredDate=floured_date
            )
        )

    return [schemas.ExpeditionWithBatches(**data) for data in expeditions_dict.values()]




def get_all_expedition_with_batches(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.ExpeditionWithBatches]:
    results = (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.DriedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            models.CheckpointStatus.status,
            models.CheckpointStatus.statusdate
        )
        .join(models.Expedition.content)  # Join with ExpeditionContent
        .join(models.ExpeditionContent.batch)  # Join with ProcessedLeaves
        .join(models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id)  # Join with DriedLeaves
        .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)  # Optional join with CheckpointStatus
        .options(joinedload(models.Expedition.content))  # Optimize loading of related content
        .offset(skip)
        .limit(limit)
        .all()
    )

    expeditions_dict = defaultdict(lambda: {
        "expedition": None,
        "batches": [],
        "checkpoint_status": None,
        "checkpoint_statusdate": None
    })

    for result in results:
        expedition, batch_id, weight, dried_date, floured_date, status, statusdate = result
        expedition_id = expedition.ExpeditionID

        if expeditions_dict[expedition_id]["expedition"] is None:
            expeditions_dict[expedition_id]["expedition"] = schemas.Expedition(
                ExpeditionID=expedition.ExpeditionID,
                AirwayBill=expedition.AirwayBill,
                EstimatedArrival=expedition.EstimatedArrival,
                TotalPackages=expedition.TotalPackages,
                TotalWeight=expedition.TotalWeight,
                Status=expedition.Status,
                ExpeditionDate=expedition.ExpeditionDate,
                ExpeditionServiceDetails=expedition.ExpeditionServiceDetails,
                WarehouseID=expedition.WarehouseID,
                CentralID=expedition.CentralID,
            )

        if status is not None:
            expeditions_dict[expedition_id]["checkpoint_status"] = status
            expeditions_dict[expedition_id]["checkpoint_statusdate"] = statusdate

        # Check if the batch is already in the list before appending
        if not any(batch.BatchID == batch_id for batch in expeditions_dict[expedition_id]["batches"]):
            expeditions_dict[expedition_id]["batches"].append(schemas.Batch(
                BatchID=batch_id,
                Weight=weight,
                DriedDate=dried_date,
                FlouredDate=floured_date
            ))

    return [schemas.ExpeditionWithBatches(**data) for data in expeditions_dict.values()]



def get_expeditions_with_batches_by_centra(db: Session, centra_id: int, skip: int = 0, limit: int = 100) -> List[schemas.ExpeditionWithBatches]:
    results = (
        db.query(
            models.Expedition,
            models.ExpeditionContent.BatchID,
            models.ProcessedLeaves.Weight,
            models.DriedLeaves.DriedDate,
            models.ProcessedLeaves.FlouredDate,
            models.CheckpointStatus.status,
            models.CheckpointStatus.statusdate
        )
        .join(models.Expedition.content)  # Join with ExpeditionContent
        .join(models.ExpeditionContent.batch)  # Join with ProcessedLeaves
        .join(models.DriedLeaves, models.ProcessedLeaves.DriedID == models.DriedLeaves.id)  # Join with DriedLeaves
        .outerjoin(models.CheckpointStatus, models.CheckpointStatus.expeditionid == models.Expedition.ExpeditionID)  # Optional join with CheckpointStatus
        .filter(models.Expedition.CentralID == centra_id)  # Filter by CentralID
        .options(joinedload(models.Expedition.content))  # Optimize loading of related content
        .offset(skip)
        .limit(limit)
        .all()
    )

    expeditions_dict = {}

    for result in results:
        expedition, batch_id, weight, dried_date, floured_date, status, statusdate = result

        if expedition.ExpeditionID not in expeditions_dict:
            expeditions_dict[expedition.ExpeditionID] = {
                "expedition": schemas.Expedition(
                    ExpeditionID=expedition.ExpeditionID,
                    AirwayBill=expedition.AirwayBill,
                    EstimatedArrival=expedition.EstimatedArrival,
                    TotalPackages=expedition.TotalPackages,
                    TotalWeight=expedition.TotalWeight,
                    Status=expedition.Status,
                    ExpeditionDate=expedition.ExpeditionDate,
                    ExpeditionServiceDetails=expedition.ExpeditionServiceDetails,
                    CentralID=expedition.CentralID,
                    # Destination=expedition.Destination  # Assuming this field exists
                ),
                "batches": [],
                "checkpoint_status": status if status else None,
                "checkpoint_statusdate": statusdate if statusdate else None
            }

        expeditions_dict[expedition.ExpeditionID]["batches"].append(
            schemas.Batch(
                BatchID=batch_id,
                Weight=weight,
                DriedDate=dried_date,
                FlouredDate=floured_date
            )
        )

    return [schemas.ExpeditionWithBatches(**data) for data in expeditions_dict.values()]




def get_expeditions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Expedition).offset(skip).limit(limit).all()


def create_expedition(db: Session, expedition: schemas.ExpeditionCreate, user: dict ):
    # Fetch the user including their related Centra
    
    
    # Assuming you have a direct relationship to Centra or a method to fetch it
    
    centra_id = user["centralID"] 
    # Create the expedition object with CentraID included
    db_expedition = models.Expedition(**expedition.dict(), CentralID=centra_id,  Status ='PKG_Delivering')
    # Add to session, commit, and refresh
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)
    
    return db_expedition


def update_expedition(db: Session, expedition_id: int, expedition: schemas.ExpeditionUpdate):
    db_expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if not db_expedition:
        return None
    
    # Update the fields
    for key, value in expedition.dict(exclude_unset=True).items():
        # Handle 'warehouseid' to 'WarehouseID' mapping
        if key == 'warehouseid':
            key = 'WarehouseID'
        setattr(db_expedition, key, value)
    
    db.commit()
    db.refresh(db_expedition)
    return db_expedition

def update_expedition_status(db: Session, awb:str, new_status: str):
    # Fetch the expedition record by ID
    expedition = db.query(models.Expedition).filter(models.Expedition.AirwayBill == awb).first()
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    # Validate the new status
    valid_statuses = ['PKG_Delivered', 'PKG_Delivering', 'XYZ_PickingUp', 'XYZ_Completed', 'Missing']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Update the status
    expedition.Status = new_status
    db.commit()
    db.refresh(expedition)
    return {"New status" : new_status}

def delete_expedition(db: Session, expedition_id: int):
    db_expedition = db.query(models.Expedition).filter(models.Expedition.ExpeditionID == expedition_id).first()
    if db_expedition:
        db.delete(db_expedition)
        db.commit()
        return {"message": "Expedition deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Expedition not found")

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

def get_checkpoints_statuses_by_airwaybill(db: Session, airwaybill: str):
    # First, get the expedition ID based on the provided airway bill
    expedition = db.query(models.Expedition).filter(models.Expedition.AirwayBill == airwaybill).first()
    
    if not expedition:
        return None  # or raise an exception if the expedition is not found
    
    # Get all checkpoint statuses for the found expedition ID
    checkpoint_statuses = db.query(models.CheckpointStatus).filter(models.CheckpointStatus.expeditionid == expedition.ExpeditionID).all()
    
    return checkpoint_statuses

def create_checkpoint_status_by_airwaybill(db: Session, airwaybill: str, checkpoint_status_data: schemas.CheckpointStatusCreateAirway):
    # First, get the expedition ID based on the provided airway bill
    expedition = db.query(models.Expedition).filter(models.Expedition.AirwayBill == airwaybill).first()
    
    if not expedition:
        return None  # or raise an exception if the expedition is not found
    
    # Create a new CheckpointStatus entry for the found expedition ID
    new_checkpoint_status = models.CheckpointStatus(
        expeditionid=expedition.ExpeditionID,
        status=checkpoint_status_data.status,
        statusdate=checkpoint_status_data.statusdate or datetime.utcnow()
    )
    
    db.add(new_checkpoint_status)
    db.commit()
    db.refresh(new_checkpoint_status)
    
    return new_checkpoint_status

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
        return {"message": "Reception deleted successfully"}
    return db_package_receipt

def delete_package_receipt_by_expeditionid(db: Session, expedition_id: int):
    package_receipt = db.query(models.PackageReceipt).filter(models.PackageReceipt.ExpeditionID == expedition_id).first()
    
    if package_receipt:
        db.delete(package_receipt)
        db.commit()
    return package_receipt

def get_package_receipts_by_expeditionid(db: Session, expedition_id: int):
    return db.query(models.PackageReceipt).filter(models.PackageReceipt.ExpeditionID == expedition_id).all()

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

def get_leaves_summary(db: Session, centra_id: int):
    # Wet leaves
    total_wet_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
        models.WetLeavesCollection.CentralID == centra_id,
        models.WetLeavesCollection.Status.in_(['Fresh', 'Processed', 'Near expiry'])
    ).scalar() or 0

    fresh_wet_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
        models.WetLeavesCollection.CentralID == centra_id,
        models.WetLeavesCollection.Status == 'Fresh'
    ).scalar() or 0

    drying_wet_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
        models.WetLeavesCollection.CentralID == centra_id,
        models.WetLeavesCollection.Status == 'Processed'
    ).scalar() or 0

    near_expiry_wet_weight = db.query(func.sum(models.WetLeavesCollection.Weight)).filter(
        models.WetLeavesCollection.CentralID == centra_id,
        models.WetLeavesCollection.Status == 'Near expiry'
    ).scalar() or 0

    wet_proportions = [
        fresh_wet_weight / total_wet_weight if total_wet_weight else 0,
        drying_wet_weight / total_wet_weight if total_wet_weight else 0,
        near_expiry_wet_weight / total_wet_weight if total_wet_weight else 0
    ]

    # Dried leaves
    total_dried_weight = db.query(func.sum(models.DriedLeaves.Weight)).filter(
        models.DriedLeaves.CentraID == centra_id
    ).scalar() or 0

    floured_dried_weight = db.query(func.sum(models.DriedLeaves.Weight)).filter(
        models.DriedLeaves.CentraID == centra_id,
        models.DriedLeaves.Floured == True
    ).scalar() or 0

    dried_proportions = [
        (total_dried_weight - floured_dried_weight) / total_dried_weight if total_dried_weight else 0,
        floured_dried_weight / total_dried_weight if total_dried_weight else 0
    ]

    # Floured leaves
    total_floured_weight = db.query(func.sum(models.ProcessedLeaves.Weight)).filter(
        models.ProcessedLeaves.CentraID == centra_id
    ).scalar() or 0

    shipped_floured_weight = db.query(func.sum(models.ProcessedLeaves.Weight)).filter(
        models.ProcessedLeaves.CentraID == centra_id,
        models.ProcessedLeaves.Shipped == True
    ).scalar() or 0

    floured_proportions = [
        (total_floured_weight - shipped_floured_weight) / total_floured_weight if total_floured_weight else 0,
        shipped_floured_weight / total_floured_weight if total_floured_weight else 0
    ]

    return {
        "wetLeaves": {
            "totalWeight": total_wet_weight,
            "proportions": [round(p, 2) for p in wet_proportions],
        },
        "driedLeaves": {
            "totalWeight": total_dried_weight,
            "proportions": [round(p, 2) for p in dried_proportions],
        },
        "flouredLeaves": {
            "totalWeight": total_floured_weight,
            "proportions": [round(p, 2) for p in floured_proportions],
        }
    }


def get_centra_id(db: Session, user_id: int) -> Optional[int]:
    centra_user = db.query(models.UserCentra).filter(models.UserCentra.userID == user_id, models.UserCentra.Active == True).first()
    if centra_user:
        return centra_user.CentraID
    return None

def get_warehouse_id(db: Session, user_id: int) -> Optional[int]:
    xyz_user = db.query(models.XYZuser).filter(models.XYZuser.userID == user_id).first()
    if xyz_user:
        return xyz_user.WarehouseID
    return None
def calculate_conversion_rates(db: Session, centra_id: int) -> schemas.ConversionRateResponse:
    wet_leaves = db.query(models.WetLeavesCollection).filter(models.WetLeavesCollection.CentralID == centra_id).all()
    dried_leaves = db.query(models.DriedLeaves).filter(models.DriedLeaves.CentraID == centra_id).all()
    processed_leaves = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.CentraID == centra_id).all()

    total_wet_weight = sum(wet.Weight for wet in wet_leaves)
    total_dried_weight = sum(dried.Weight for dried in dried_leaves)
    total_floured_weight = sum(processed.Weight for processed in processed_leaves)
    total_weight = total_wet_weight + total_dried_weight + total_floured_weight

    wet_to_dried_rate = round((total_dried_weight / total_weight)*100, 2) if total_weight else 0
    wet_to_floured_rate = round((total_floured_weight / total_weight)*100, 2) if total_weight else 0
    conversion_rate = wet_to_dried_rate + wet_to_floured_rate

    return schemas.ConversionRateResponse(
        id=centra_id,
        conversionRate=conversion_rate,
        wetToDry=wet_to_dried_rate,
        dryToFloured=wet_to_floured_rate
    )
