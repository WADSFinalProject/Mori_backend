from fastapi import FastAPI, Path, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from . import crud, models, schemas  
from .database import SessionLocal, engine 
from .crud import (get_all_centras, add_new_centra, get_all_harbor_guards, get_harbor_guard, create_harbor_guard, update_harbor_guard, delete_harbor_guard)
from .schemas import HarborGuardCreate, HarborGuardUpdate


models.Base.metadata.create_all(bind=engine)


app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class UserRegistration(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserVerification(BaseModel):
    code: int

class User(BaseModel):
    PIC_name: str
    email: EmailStr
    phone: str

class Batch(BaseModel):
    weight: float
    collection_date: str
    time: str

class MachineAction(BaseModel):
    machine_id: int

class ShipmentStatusUpdate(BaseModel):
    status: str

class ShipmentConfirmation(BaseModel):
    shipment_id: int
    weight: Optional[float] = None

class ShipmentSchedule(BaseModel):
    shipment_id: int
    pickup_time: str
    location: str

class ShipmentIssue(BaseModel):
    shipment_id: int
    issue_description: str

class ShipmentRescale(BaseModel):
    shipment_id: int
    new_weight: float

class ShipmentPickupSchedule(BaseModel):
    shipment_id: int
    pickup_time: datetime
    location: str

class ShipmentUpdate(BaseModel):
    status: str
    checkpoint: str
    action: str

class CentraDetails(BaseModel):
    PIC_name: str
    location: str
    email: str
    phone: int
    drying_machine_status: str
    flouring_machine_status: str
    action: str

class HarborGuard(BaseModel):
    PIC_name: str
    email: EmailStr
    phone: str

class Warehouse(BaseModel):
    PIC_name: str
    email: EmailStr
    phone: str


@app.get("/")
async def welcome():
    return {"message": "Welcome to our API!"}

# Users
@app.post("/users/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, user=user)
    return {"message": "User registered successfully"}

@app.post("/users/login")
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, email=user.email, password=user.password)
    if db_user:
        # Replace "YourTokenHere" with actual JWT token generation logic
        return {"jwt_token": "YourTokenHere"}
    raise HTTPException(status_code=404, detail="User not authenticated")

@app.post("/users/verify")
async def verify_user(verification: schemas.UserVerification, db: Session = Depends(get_db)):
    verified = crud.verify_user(db, verification.code)
    if verified:
        return {"message": "User verified successfully"}
    raise HTTPException(status_code=404, detail="Verification failed")

@app.post("/users/resend_code")
async def resend_code(user: schemas.UserRegistration, db: Session = Depends(get_db)):
    resent = crud.resend_verification_code(db, email=user.email)
    if resent:
        return {"message": "Verification code resent"}
    raise HTTPException(status_code=404, detail="Failed to resend code")


# Batches
@app.get("/batches")
async def get_all_batches(db: Session = Depends(get_db)):
    return crud.get_all_processed_leaves(db) # get_all_processed_leaves

@app.get("/batches/{batch_id}")
async def get_batch_by_id(batch_id: int, db: Session = Depends(get_db)):
    batch = crud.get_processed_leaf(db, product_id=batch_id) # get_processed_leaf
    if batch:
        return batch
    raise HTTPException(status_code=404, detail="Batch not found")

@app.post("/batches")
async def create_batch(batch: schemas.Batch, db: Session = Depends(get_db)):
    return crud.create_processed_leaf(db, batch=batch) # create_processed_leaf

@app.put("/batches/{batch_id}")
async def update_batch(batch_id: int, batch: schemas.Batch, db: Session = Depends(get_db)):
    updated_batch = crud.update_processed_leaf(db, batch_id=batch_id, batch=batch) # update_processed_leaf
    if updated_batch:
        return updated_batch
    raise HTTPException(status_code=404, detail="Batch not found")

@app.delete("/batches/{batch_id}")
async def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    result = crud.delete_processed_leaf(db, batch_id=batch_id) # delete_processed_leaf
    if result:
        return {"message": "Batch deleted successfully"}
    raise HTTPException(status_code=404, detail="Batch not found")

@app.get("/batches/{batch_id}/dried_date")
async def get_dried_date(batch_id: int, db: Session = Depends(get_db)):
    dried_date = crud.get_dried_date(db, batch_id)
    if dried_date:
        return {"dried_date": dried_date}
    raise HTTPException(status_code=404, detail="Batch not found")

@app.get("/batches/{batch_id}/floured_date")
async def get_floured_date(batch_id: int, db: Session = Depends(get_db)):
    floured_date = crud.get_floured_date(db, batch_id)
    if floured_date:
        return {"floured_date": floured_date}
    raise HTTPException(status_code=404, detail="Batch not found")

# Machines
@app.get("/machines/{machine_id}")
async def get_machine_status(machine_id: int, db: Session = Depends(get_db)):
    machine = crud.get_machine_status(db, machine_id=machine_id)
    if machine:
        return {"status": machine.status}  # Assuming the Machine model has a 'status' attribute
    raise HTTPException(status_code=404, detail="Machine not found")

@app.post("/machines/{machine_id}/start")
async def start_machine(machine_id: int, db: Session = Depends(get_db)):
    if crud.start_machine(db, machine_id=machine_id):
        return {"message": "Machine started"}
    raise HTTPException(status_code=404, detail="Machine not found")

@app.post("/machines/{machine_id}/stop")
async def stop_machine(machine_id: int, db: Session = Depends(get_db)):
    if crud.stop_machine(db, machine_id=machine_id):
        return {"message": "Machine stopped"}
    raise HTTPException(status_code=404, detail="Machine not found")

# Shipments (Centra)
@app.post("/shipments")
async def add_shipment(shipment_data: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    added_shipment = crud.add_shipment(db, shipment_data)
    return added_shipment

@app.put("/shipments/{shipment_id}")
async def update_shipment(shipment_id: str, shipment_update: schemas.ShipmentUpdate, db: Session = Depends(get_db)):
    updated_shipment = crud.update_shipment(db, shipment_id, shipment_update)
    if updated_shipment:
        return updated_shipment
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.get("/notifications")
async def show_notifications(db: Session = Depends(get_db)):
    notifications = crud.get_notifications(db)
    return {"notifications": notifications}

@app.get("/shipments")
async def get_all_shipments(db: Session = Depends(get_db)):
    shipments = crud.get_all_shipments(db)
    return shipments

@app.get("/shipments/{shipment_id}")
async def get_shipment_details(shipment_id: str, db: Session = Depends(get_db)):
    shipment = crud.get_shipment_details(db, shipment_id)
    if shipment:
        return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.delete("/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str, db: Session = Depends(get_db)):
    if crud.delete_shipment(db, shipment_id):
        return {"message": "Shipment deleted"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.post("/shipments/{shipment_id}/confirm")
async def confirm_shipment(shipment_id: int, confirmation: schemas.ShipmentConfirmation, db: Session = Depends(get_db)):
    if crud.confirm_shipment(db, shipment_id, confirmation.weight):
        return {"message": "Shipment confirmed"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.post("/shipments/{shipment_id}/report")
async def report_shipment_issue(shipment_id: str, issue: schemas.ShipmentIssue, db: Session = Depends(get_db)):
    if crud.report_shipment_issue(db, shipment_id, issue.description):
        return {"message": "Issue reported successfully"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.post("/shipments/{shipment_id}/confirm")
async def confirm_shipment_arrival(shipment_id: str, confirmation: schemas.ShipmentConfirmation, db: Session = Depends(get_db)):
    if crud.confirm_shipment(db, shipment_id, confirmation.weight):
        return {"message": "Shipment confirmed"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.put("/shipments/{shipment_id}/rescale")
async def rescale_shipment(shipment_id: str, rescale: schemas.ShipmentRescale, db: Session = Depends(get_db)):
    if crud.rescale_shipment(db, shipment_id, rescale.new_weight):
        return {"message": "Shipment weight updated"}
    raise HTTPException(status_code=404, detail="Shipment not found")


# Stocks
@app.get("/stocks")
async def show_all_stock_details(db: Session = Depends(get_db)):
    stocks = crud.get_all_stocks(db)
    return stocks

@app.get("/stocks/{location_id}")
async def show_stock_detail(location_id: int, db: Session = Depends(get_db)):
    stock = crud.get_stock_detail(db, location_id)
    if stock:
        return stock
    raise HTTPException(status_code=404, detail="Location not found")


# Locations
@app.get("/location/{location_id}")
async def show_location_details(location_id: int, db: Session = Depends(get_db)):
    location = crud.get_location_details(db, location_id)
    if location:
        return location
    raise HTTPException(status_code=404, detail="Location not found")

# Shipment History
@app.get("/shipments/{location_id}/history")
async def show_shipment_history(location_id: int, db: Session = Depends(get_db)):
    shipment_history = crud.get_shipment_history(db, location_id)
    if shipment_history:
        return shipment_history
    raise HTTPException(status_code=404, detail="Location not found")

@app.post("/shipments/schedule-pickup")
async def schedule_pickup(pickup_data: ShipmentPickupSchedule, db: Session = Depends(get_db)):
    is_valid = crud.validate_shipment_id(db, pickup_data.shipment_id)
    if is_valid:
        result = crud.schedule_pickup(db, pickup_data)
        if result:
            return {"message": "Pickup scheduled successfully"}
        return {"error": "Failed to schedule pickup"}
    raise HTTPException(status_code=404, detail="Shipment not found")

# Centra
@app.get("/centras")
async def show_all_centras(db: Session = Depends(get_db)):
    centras = get_all_centras(db)
    return centras

@app.post("/centras", response_model=CentraDetails)
async def add_new_centra(centra_data: CentraDetails, db: Session = Depends(get_db)):
    new_centra = add_new_centra(db, centra_data)
    return new_centra

# Shipment (XYZ)

@app.put("/shipments/{shipment_id}")
async def update_shipment_details(shipment_id: str, shipment_update: ShipmentUpdate, db: Session = Depends(get_db)):
    updated = update_shipment(db, shipment_id, shipment_update)
    if updated:
        return updated
    raise HTTPException(status_code=404, detail="Shipment not found")


@app.delete("/shipments/{shipment_id}")
async def remove_shipment(shipment_id: str, db: Session = Depends(get_db)):
    deleted = delete_shipment(db, shipment_id)
    if deleted:
        return {"message": "Shipment deleted successfully"}
    raise HTTPException(status_code=404, detail="Shipment not found")

# Harborguards
@app.get("/harborguards")
async def show_all_harbor_guards(db: Session = Depends(get_db)):
    guards = get_all_harbor_guards(db)
    return guards

@app.get("/harborguards/{guard_id}")
async def show_harbor_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = get_harbor_guard(db, guard_id)
    return guard

@app.post("/harborguards", response_model=HarborGuardCreate)
async def add_harbor_guard(guard_data: HarborGuardCreate, db: Session = Depends(get_db)):
    new_guard = create_harbor_guard(db, guard_data)
    return new_guard

@app.put("/harborguards/{guard_id}", response_model=HarborGuardUpdate)
async def modify_harbor_guard(guard_id: int, guard_data: HarborGuardUpdate, db: Session = Depends(get_db)):
    updated_guard = update_harbor_guard(db, guard_id, guard_data)
    return updated_guard

@app.delete("/harborguards/{guard_id}")
async def remove_harbor_guard(guard_id: int, db: Session = Depends(get_db)):
    result = delete_harbor_guard(db, guard_id)
    return result

# Warehouses
@app.get("/warehouses", response_model=List[schemas.Warehouse])
async def show_all_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    warehouses = crud.get_all_warehouses(db, skip=skip, limit=limit)
    return warehouses

@app.get("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def get_warehouse(warehouse_id: str, db: Session = Depends(get_db)):
    warehouse = crud.get_warehouse(db, warehouse_id=warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

@app.post("/warehouses", response_model=schemas.Warehouse)
async def create_warehouse(warehouse_data: schemas.WarehouseCreate, db: Session = Depends(get_db)):
    return crud.create_warehouse(db=db, warehouse_data=warehouse_data)

@app.put("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def update_warehouse(warehouse_id: str, warehouse_data: schemas.WarehouseUpdate, db: Session = Depends(get_db)):
    updated_warehouse = crud.update_warehouse(db, warehouse_id=warehouse_id, update_data=warehouse_data)
    if updated_warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return updated_warehouse

@app.delete("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def delete_warehouse(warehouse_id: str, db: Session = Depends(get_db)):
    deleted_warehouse = crud.delete_warehouse(db, warehouse_id=warehouse_id)
    if deleted_warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return {"message": "Warehouse deleted successfully"}

# User (Admin)
@app.get("/users", response_model=List[schemas.User])
async def show_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=schemas.User)
async def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user_data)

@app.put("/users/{user_id}", response_model=schemas.User)
async def update_user(user_id: str, user_data: schemas.UserUpdate, db: Session = Depends(get_db)):
    updated_user = crud.update_user(db, user_id=user_id, update_data=user_data)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@app.delete("/users/{user_id}", response_model=schemas.User)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    deleted_user = crud.delete_user(db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}