from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        userID=user.userID,
        IDORole=user.IDORole, 
        Email=user.email, 
        FullName=user.FullName, 
        Role=user.Role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def set_user_password(db: Session, user_id: str, password: str):
    user = db.query(models.User).filter(models.User.userID == user_id).first()
    if user:
        fake_hashed_pass = password + "examplehash"
        user.hashed_password = fake_hashed_pass
        db.commit()
        db.refresh(user)
        return user
    return None

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.userID == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.Email == email).first()

def update_user(db: Session, user_id: str, update_data: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.userID == user_id).first()
    if user:
        for key, value in update_data.dict().items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: str):
    user = db.query(models.User).filter(models.User.userID == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

# BATCHES
def create_batch(db: Session, batch: schemas.BatchCreate):
    db_batch = models.Batch(
        Description=batch.Description,
        DriedDate=batch.DriedDate,
        FlouredDate=batch.FlouredDate
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_all_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Batch).offset(skip).limit(limit).all()

def get_batch_by_id(db: Session, batch_id: int):
    return db.query(models.Batch).filter(models.Batch.id == batch_id).first()

def update_batch(db: Session, batch_id: int, update_data: schemas.BatchUpdate):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if batch:
        for key, value in update_data.dict().items():
            setattr(batch, key, value)
        db.commit()
        db.refresh(batch)
    return batch

def delete_batch(db: Session, batch_id: int):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if batch:
        db.delete(batch)
        db.commit()
    return batch

# MACHINES
def get_machine_status(db: Session, machine_id: int):
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def start_machine(db: Session, machine_id: int):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if machine:
        machine.status = 'running'
        db.commit()
        db.refresh(machine)
        return machine
    return None

def stop_machine(db: Session, machine_id: int):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if machine:
        machine.status = 'stopped'
        db.commit()
        db.refresh(machine)
        return machine
    return None

# SHIPMENTS
def add_shipment(db: Session, shipment_id: str, shipment_data: schemas.ShipmentCreate):
    db_shipment = models.Shipment(
        id=shipment_id,
        **shipment_data.dict()
    )
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def update_shipment(db: Session, shipment_id: str, shipment_update: schemas.ShipmentUpdate):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment:
        for key, value in shipment_update.dict().items():
            setattr(shipment, key, value)
        db.commit()
        db.refresh(shipment)
    return shipment

def get_all_shipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Shipment).offset(skip).limit(limit).all()

def get_shipment_details(db: Session, shipment_id: str):
    return db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()

def delete_shipment(db: Session, shipment_id: str):
    shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
    if shipment:
        db.delete(shipment)
        db.commit()
    return shipment

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
        return location.shipment_history
    return []

# WET LEAVES COLLECTIONS
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

# DRYING MACHINE
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

# WAREHOUSE LOCATION
def create_warehouse_location(db: Session, warehouse_location: schemas.WarehouseLocationCreate):
    db_warehouse_location = models.WarehouseLocation(
        LocationID=warehouse_location.LocationID,
        Capacity=warehouse_location.Capacity
    )
    db.add(db_warehouse_location)
    db.commit()
    db.refresh(db_warehouse_location)
    return db_warehouse_location

def get_all_warehouse_locations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WarehouseLocation).offset(skip).limit(limit).all()

def get_warehouse_location(db: Session, location_id: str):
    return db.query(models.WarehouseLocation).filter(models.WarehouseLocation.LocationID == location_id).first()

def update_warehouse_location(db: Session, location_id: str, update_data: schemas.WarehouseLocationUpdate):
    db_warehouse_location = db.query(models.WarehouseLocation).filter(models.WarehouseLocation.LocationID == location_id).first()
    if db_warehouse_location:
        for key, value in update_data.dict().items():
            setattr(db_warehouse_location, key, value)
        db.commit()
        db.refresh(db_warehouse_location)
    return db_warehouse_location

def delete_warehouse_location(db: Session, location_id: str):
    db_warehouse_location = db.query(models.WarehouseLocation).filter(models.WarehouseLocation.LocationID == location_id).first()
    if db_warehouse_location:
        db.delete(db_warehouse_location)
        db.commit()
    return db_warehouse_location


#HARBOUR GUARD

def get_all_harbor_guards(db: Session, skip: int = 0, limit: int = 100) -> List[models.HarborGuard]:
    return db.query(models.HarborGuard).offset(skip).limit(limit).all()

def get_harbor_guard(db: Session, guard_id: str) -> Optional[models.HarborGuard]:
    guard = db.query(models.HarborGuard).filter(models.HarborGuard.id == guard_id).first()
    if guard:
        return guard
    raise HTTPException(status_code=404, detail="Harbor guard not found")

def create_harbor_guard(db: Session, guard_data: schemas.HarborGuardCreate) -> models.HarborGuard:
    db_guard = models.HarborGuard(
        name=guard_data.name,
        rank=guard_data.rank,
        station=guard_data.station
    )
    db.add(db_guard)
    db.commit()
    db.refresh(db_guard)
    return db_guard

def update_harbor_guard(db: Session, guard_id: str, guard_data: schemas.HarborGuardUpdate) -> Optional[models.HarborGuard]:
    db_guard = db.query(models.HarborGuard).filter(models.HarborGuard.id == guard_id).first()
    if db_guard:
        for key, value in guard_data.dict().items():
            setattr(db_guard, key, value)
        db.commit()
        db.refresh(db_guard)
        return db_guard
    raise HTTPException(status_code=404, detail="Harbor guard not found")

def delete_harbor_guard(db: Session, guard_id: str) -> Optional[models.HarborGuard]:
    db_guard = db.query(models.HarborGuard).filter(models.HarborGuard.id == guard_id).first()
    if db_guard:
        db.delete(db_guard)
        db.commit()
        return db_guard
    raise HTTPException(status_code=404, detail="Harbor guard not found")