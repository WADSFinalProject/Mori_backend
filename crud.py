from sqlalchemy.orm import Session
from . import models, schemas
import secrets
import string

# USERS

def create_user(db: Session, user: schemas.UserCreate):
    # fake_hashed_pass = user.password + "examplehash"
    db_user = models.User(
        UserID=user.userID,
        IDORole=user.IDORole, 
        Email=user.email, 
        FullName=user.IDORole, 
        Role=user.Role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def set_user_password(db: Session, user_id: str, password: str):
    user = db.query(models.User).filter(models.User.UserID == user_id).first()
    if user:
        fake_hashed_pass = password + "examplehash"
        user.hashed_password = fake_hashed_pass
        db.commit()
        db.refresh(user)
        return user
    return None

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db:Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


#PROCESSED LEAVES

def create_processed_leaf(db: Session, processed_leaf: schemas.ProcessedLeavesCreate):
    db_processed_leaf = models.ProcessedLeaves(
        Description=processed_leaf.Description,
        FlouringID=processed_leaf.FlouringID,
        DryingID=processed_leaf.DryingID
    )
    db.add(db_processed_leaf)
    db.commit()
    db.refresh(db_processed_leaf)
    return db_processed_leaf


def get_all_processed_leaves(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProcessedLeaves).offset(skip).limit(limit).all()

def get_processed_leaf(db: Session, product_id: int):
    return db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == product_id).first()


def update_processed_leaf(db: Session, product_id: int, update_data: schemas.ProcessedLeavesUpdate):
    db_processed_leaf = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == product_id).first()
    if db_processed_leaf:
        for key, value in update_data.dict().items():
            setattr(db_processed_leaf, key, value)
        db.commit()
        db.refresh(db_processed_leaf)
    return db_processed_leaf


def delete_processed_leaf(db: Session, product_id: int):
    db_processed_leaf = db.query(models.ProcessedLeaves).filter(models.ProcessedLeaves.ProductID == product_id).first()
    if db_processed_leaf:
        db.delete(db_processed_leaf)
        db.commit()
    return db_processed_leaf


#WET LEAVES COLLECTION

def create_wet_leaves_collection(db: Session, wet_leaves_collection: schemas.WetLeavesCollectionCreate):
    db_wet_leaves_collection = models.WetLeavesCollection(
        WetLeavesBatchID=wet_leaves_collection.WetLeavesBatchID,
        UserID=wet_leaves_collection.UserID,
        CentralID=wet_leaves_collection.CentralID,
        Date=wet_leaves_collection.Date,
        Time=wet_leaves_collection.Time,
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

#DRYING MACHINE

def create_drying_machine(db: Session, drying_machine: schemas.DryingMachineCreate):
    db_drying_machine = models.DryingMachine(
        MachineID=drying_machine.MachineID,
        Capacity=drying_machine.Capacity
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


#DRYING ACTIVITY

def create_drying_activity(db: Session, drying_activity: schemas.DryingActivityCreate):
    db_drying_activity = models.DryingActivity(
        DryingID=drying_activity.DryingID,
        UserID=drying_activity.UserID,
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


def get_all_drying_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DryingActivity).offset(skip).limit(limit).all()


def get_drying_activity(db: Session, drying_id: str):
    return db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()


def update_drying_activity(db: Session, drying_id: str, update_data: schemas.DryingActivityUpdate):
    db_drying_activity = db.query(models.DryingActivity).filter(models.DryingActivity.DryingID == drying_id).first()
    if db_drying_activity:
        for key, value in update_data.dict().items():
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

#FLOURING MACHINE
def create_flouring_machine(db: Session, flouring_machine: schemas.FlouringMachineCreate):
    db_flouring_machine = models.FlouringMachine(
        MachineID=flouring_machine.MachineID,
        Capacity=flouring_machine.Capacity
    )
    db.add(db_flouring_machine)
    db.commit()
    db.refresh(db_flouring_machine)
    return db_flouring_machine

# Get all flouring machines with optional pagination
def get_all_flouring_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringMachine).offset(skip).limit(limit).all()

# Get a flouring machine by its MachineID
def get_flouring_machine(db: Session, machine_id: str):
    return db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()

# Update a flouring machine by its MachineID
def update_flouring_machine(db: Session, machine_id: str, update_data: schemas.FlouringMachineUpdate):
    db_flouring_machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if db_flouring_machine:
        for key, value in update_data.dict().items():
            setattr(db_flouring_machine, key, value)
        db.commit()
        db.refresh(db_flouring_machine)
    return db_flouring_machine

# Delete a flouring machine by its MachineID
def delete_flouring_machine(db: Session, machine_id: str):
    db_flouring_machine = db.query(models.FlouringMachine).filter(models.FlouringMachine.MachineID == machine_id).first()
    if db_flouring_machine:
        db.delete(db_flouring_machine)
        db.commit()
    return db_flouring_machine


#FLOURING ACTIVITY
def create_flouring_activity(db: Session, flouring_activity: schemas.FlouringActivityCreate):
    db_flouring_activity = models.FlouringActivity(
        FlouringID=flouring_activity.FlouringID,
        UserID=flouring_activity.UserID,
        CentralID=flouring_activity.CentralID,
        Date=flouring_activity.Date,
        Weight=flouring_activity.Weight,
        FlouringMachineID=flouring_activity.FlouringMachineID,
        DryingID=flouring_activity.DryingID
    )
    db.add(db_flouring_activity)
    db.commit()
    db.refresh(db_flouring_activity)
    return db_flouring_activity

# Get all flouring activities with optional pagination
def get_all_flouring_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FlouringActivity).offset(skip).limit(limit).all()

# Get a flouring activity by its FlouringID
def get_flouring_activity(db: Session, flouring_id: str):
    return db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()

# Update a flouring activity by its FlouringID
def update_flouring_activity(db: Session, flouring_id: str, update_data: schemas.FlouringActivityUpdate):
    db_flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()
    if db_flouring_activity:
        for key, value in update_data.dict().items():
            setattr(db_flouring_activity, key, value)
        db.commit()
        db.refresh(db_flouring_activity)
    return db_flouring_activity

# Delete a flouring activity by its FlouringID
def delete_flouring_activity(db: Session, flouring_id: str):
    db_flouring_activity = db.query(models.FlouringActivity).filter(models.FlouringActivity.FlouringID == flouring_id).first()
    if db_flouring_activity:
        db.delete(db_flouring_activity)
        db.commit()
    return db_flouring_activity