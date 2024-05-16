from fastapi import FastAPI, Path, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from . import crud, models, schemas  
from .database import SessionLocal  

app = FastAPI()

# Mock database example
batches = {}
machines = {}
shipments = {}
locations = {}
users = {}
centras = {}
harbor_guards = {}
warehouses = {}
notifications = {}
stocks = {}


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
    db_user = crud.authenticate_user(db, email=user.email, password=user.password) #authenticate user function nya gada
    if db_user:
        return {"jwt_token": "YourTokenHere"}  # Replace with actual JWT token generation
    raise HTTPException(status_code=404, detail="User not authenticated")

@app.post("/users/verify")
async def verify_user(verification: schemas.UserVerification, db: Session = Depends(get_db)):
    verified = crud.verify_user(db, verification.code) # verify user function nya gada
    if verified:
        return {"message": "User verified successfully"}
    raise HTTPException(status_code=404, detail="Verification failed")

@app.post("/users/resend_code")
async def resend_code(user: schemas.UserRegistration, db: Session = Depends(get_db)):
    resent = crud.resend_verification_code(db, email=user.email) #resend verification code function nya gada
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

@app.get("/batches/{batch_id}/dried_date") # ambil dari drying activity apa gimana nih?
async def get_dried_date(batch_id: str):
    if batch_id in batches:
        return {"dried_date": batches[batch_id].get("dried_date")}
    raise HTTPException(status_code=404, detail="Batch not found")

@app.get("/batches/{batch_id}/floured_date") # ambil dari flouring activity atau yg mana? nama function tolong yg jelas
async def get_floured_date(batch_id: str):
    if batch_id in batches:
        return {"floured_date": batches[batch_id].get("floured_date")}
    raise HTTPException(status_code=404, detail="Batch not found")

# Machines
@app.get("/machines/{machine_id}") #ini machine ada 2 biji, machine flouring sama drying, jdi yg mana nih?
async def get_machine_status(machine_id: int, db: Session = Depends(get_db)):
    machine = crud.get_machine(db, machine_id=machine_id)
    if machine:
        return {"status": machine.get("status")}
    raise HTTPException(status_code=404, detail="Machine not found")

@app.post("/machines/{machine_id}/start")
async def start_machine(machine_id: int, db: Session = Depends(get_db)):
    started = crud.start_machine(db, machine_id=machine_id)
    if started:
        return {"message": "Machine started"}
    raise HTTPException(status_code=404, detail="Machine not found")

@app.post("/machines/{machine_id}/stop")
async def stop_machine(machine_id: int, db: Session = Depends(get_db)):
    stopped = crud.stop_machine(db, machine_id=machine_id)
    if stopped:
        return {"message": "Machine stopped"}
    raise HTTPException(status_code=404, detail="Machine not found")

@app.put("/shipments/{shipment_id}")
async def add_shipment(shipment_id: str):
    # Logic to add shipment
    return {"message": "Shipment added"}

@app.put("/shipments/{shipment_id}", response_model=ShipmentStatusUpdate)
async def update_shipment(shipment_id: str, shipment_update: ShipmentStatusUpdate):
    if shipment_id in shipments:
        shipments[shipment_id].update(shipment_update.dict())
        return shipments[shipment_id]
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.get("/notifications")
async def show_notifications():
    return notifications

@app.get("/shipments")
async def get_all_shipments():
    return list(shipments.values())

@app.get("/shipments/{shipment_id}")
async def get_shipment_details(shipment_id: str):
    shipment = shipments.get(shipment_id)
    if shipment:
        return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.delete("/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str):
    if shipment_id in shipments:
        del shipments[shipment_id]
        return {"message": "Shipment deleted"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.post("/shipments/{shipment_id}/confirm")
async def confirm_shipment(confirmation: ShipmentConfirmation):
    # Logic to confirm shipment
    return {"message": "Shipment confirmed"}

@app.post("/shipments/{shipment_id}/report")
async def report_shipment_issue(shipment_id: int, issue: ShipmentIssue):
    # Add logic to handle reporting an issue with a shipment
    if shipment_id in shipments:
        shipments[shipment_id].update(issue.dict())
        return {"message": "Issue reported successfully"}
    return {"error": "Shipment not found"}

@app.post("/shipments/{shipment_id}/confirm")
async def confirm_shipment_arrival(shipment_id: int, confirmation: ShipmentConfirmation):
    # Logic to confirm shipment arrival
    if shipment_id in shipments:
        shipments[shipment_id].update(confirmation.dict())
        return {"message": "Shipment confirmed"}
    return {"error": "Shipment not found"}

@app.put("/shipments/{shipment_id}/rescale")
async def rescale_shipment(shipment_id: int, rescale: ShipmentRescale):
    # Logic to update the weight of a shipment
    if shipment_id in shipments:
        shipments[shipment_id].update(rescale.dict())
        return shipments[shipment_id]
    return {"error": "Shipment not found"}

@app.get("/stocks")
async def show_all_stock_details():
    # Logic to retrieve stock details from all locations
    return stocks

@app.get("/stocks/{location_id}")
async def show_stock_detail(location_id: int):
    # Logic to retrieve stock details for a specific location
    if location_id in stocks:
        return stocks[location_id]
    return {"error": "Location not found"}

@app.get("/location/{location_id}")
async def show_location_details(location_id: int):
    # Logic to retrieve details for a specific location
    if location_id in locations:
        return locations[location_id]
    return {"error": "Location not found"}

@app.get("/shipments/{location_id}/history")
async def show_shipment_history(location_id: int):
    # Logic to retrieve all shipment history for a specific location
    if location_id in locations:
        return locations[location_id].get('shipment_history', [])
    return {"error": "Location not found"}

@app.post("/shipments/schedule-pickup")
async def schedule_pickup(pickup_data: ShipmentPickupSchedule):
    # This assumes there is a mechanism to validate shipment_id
    if pickup_data.shipment_id in shipments:
        shipments[pickup_data.shipment_id]['pickup_details'] = pickup_data.dict()
        return {"message": "Pickup scheduled successfully"}
    return {"error": "Shipment not found"}

@app.get("/centras")
async def show_all_centras():
    return list(centras.values())

@app.post("/centras")
async def add_new_centra(centra_data: CentraDetails):
    centra_id = len(centras) + 1  # Simple ID generation strategy
    centras[str(centra_id)] = centra_data.dict()
    return centras[str(centra_id)]

@app.put("/shipments/{shipment_id}")
async def update_shipment(shipment_id: str, shipment_update: ShipmentUpdate):
    if shipment_id in shipments:
        shipments[shipment_id].update(shipment_update.dict())
        return shipments[shipment_id]
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.delete("/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str):
    if shipment_id in shipments:
        del shipments[shipment_id]
        return {"message": "Shipment deleted successfully"}
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.get("/harborguards")
async def show_all_harbor_guards():
    return list(harbor_guards.values())

@app.get("/harborguards/{guard_id}")
async def get_harbor_guard(guard_id: str):
    guard = harbor_guards.get(guard_id)
    if guard:
        return guard
    raise HTTPException(status_code=404, detail="Harbor guard not found")

@app.post("/harborguards")
async def create_harbor_guard(guard_data: HarborGuard):
    guard_id = str(len(harbor_guards) + 1)
    harbor_guards[guard_id] = guard_data.dict()
    return harbor_guards[guard_id]

@app.put("/harborguards/{guard_id}")
async def update_harbor_guard(guard_id: str, guard_data: HarborGuard):
    if guard_id in harbor_guards:
        harbor_guards[guard_id].update(guard_data.dict())
        return harbor_guards[guard_id]
    raise HTTPException(status_code=404, detail="Harbor guard not found")

@app.get("/warehouses")
async def show_all_warehouses():
    return list(warehouses.values())

@app.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str):
    warehouse = warehouses.get(warehouse_id)
    if warehouse:
        return warehouse
    raise HTTPException(status_code=404, detail="Warehouse not found")

@app.post("/warehouses")
async def create_warehouse(warehouse_data: Warehouse):
    warehouse_id = str(len(warehouses) + 1)  # Simple unique ID generation for example
    warehouses[warehouse_id] = warehouse_data.dict()
    return warehouses[warehouse_id]

@app.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, warehouse_data: Warehouse):
    if warehouse_id in warehouses:
        warehouses[warehouse_id].update(warehouse_data.dict())
        return warehouses[warehouse_id]
    raise HTTPException(status_code=404, detail="Warehouse not found")

@app.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(warehouse_id: str):
    if warehouse_id in warehouses:
        del warehouses[warehouse_id]
        return {"message": "Warehouse deleted successfully"}
    raise HTTPException(status_code=404, detail="Warehouse not found")

@app.get("/users")
async def show_all_users():
    return list(users.values())

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = users.get(user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users")
async def create_user(user_data: User):
    user_id = str(len(users) + 1)  # Simple unique ID generation for example
    users[user_id] = user_data.dict()
    return users[user_id]

@app.put("/users/{user_id}")
async def update_user(user_id: str, user_data: User):
    if user_id in users:
        users[user_id].update(user_data.dict())
        return users[user_id]
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    if user_id in users:
        del users[user_id]
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")