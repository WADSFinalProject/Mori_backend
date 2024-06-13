from fastapi import FastAPI, Path, Depends, HTTPException, Cookie
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import crud, models, schemas  
from database import SessionLocal, engine 
from security import create_access_token,verify_otp, create_refresh_token, verify_token
# from .crud import (get_all_centras, add_new_centra, get_all_harbor_guards, get_harbor_guard, create_harbor_guard, update_harbor_guard, delete_harbor_guard)
# from .schemas import HarborGuardCreate, HarborGuardUpdate

import SMTP
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

#Handling CORS
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/")
async def welcome():
    return {"message": "Welcome to our API!"}

# Users
@app.post("/users/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    db_user = crud.create_user(db, user)

    if db_user is None:
        raise HTTPException(status_code=400, detail="User already registered or integrity error")
    
    SMTP.send_setPassEmail(db_user,db)
    return {"message": "User registered successfully"}
    
@app.get("/users/validate-link") #for setpass
async def validate_token(token:str, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_token(db, token)
        return {"valid": True}
    except HTTPException as e:
        return {"valid": False, "error": str(e)}

@app.post("/users/setpassword")
async def set_password(response_model: schemas.UserSetPassword, db: Session = Depends(get_db)):
    print(response_model.token)
    print(response_model.new_password)
    try:
        db_user = crud.get_user_by_token(db,response_model.token)
        pass_user =crud.set_user_password(db,Email= db_user.Email, new_password= response_model.new_password)

        if pass_user:
            crud.delete_token(db, response_model.token)
            return {"message": "Password set successfully"}
        raise HTTPException(status_code=404, detail="User not found or error setting password")
    
    except HTTPException as e:
        return { "error": str(e)}


@app.post("/users/login")
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    
    db_user = crud.authenticate_user(db, user.Email, user.Password)  # Call with positional arguments
    
    if db_user:

        SMTP.send_OTP(db_user, db)
        return {"message": "Credentials valid, OTP Sent!"}
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/users/verify")
async def verify_user(verification: schemas.UserVerification,  db: Session = Depends(get_db)):
    
    db_user = crud.get_user_by_email(db,verification.Email)
    verified = verify_otp(db_user.secret_key, verification.Code)
    if verified:
        access_token = create_access_token(db_user.UserID,db_user.IDORole,db_user.FullName)
        refresh_token = create_refresh_token(db_user.UserID,db_user.IDORole,db_user.FullName)
        response = JSONResponse(content={"access_token": access_token})
        response.set_cookie(key="refresh_token",max_age= 720, value=refresh_token, httponly=True, secure=False)
        response.headers["Set-Cookie"] += "; SameSite=None"
      
        return response
        # response.headers["Set-cookie"] += "; SameSite=None"
        # return response
        
    raise HTTPException(status_code=404, detail="Verification failed")

@app.post("/token/refresh")
async def refresh_token(refresh_token: str = Cookie(None)):
    if refresh_token is None:
        return HTTPException(status_code=401, detail="No refresh token found")
    try:
        payload = verify_token(refresh_token)
        new_access_token = create_access_token(payload["sub"],payload["role"],payload["name"])
        return {"access_token": new_access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.get("/protected-route")
async def protected_route(access_token: str = Depends(verify_token)):
    return {"message": "You are authenticated", "user": access_token["sub"]}


@app.post("/users/resend_code")
async def resend_code(data: dict, db: Session = Depends(get_db)):
    print(data.get("theEmail"))
    db_user = crud.get_user_by_email(db,data.get("theEmail"))
    resent = SMTP.send_OTP(db_user, db)
    if resent:
        return {"message": "Verification code resent"}
    raise HTTPException(status_code=404, detail="Failed to resend code")


@app.post("/users/logout")
async def logout():
    response = JSONResponse(content={"message": "Logout successful"}, status_code=200)
    response.delete_cookie(key="refresh_token")
    return response

# Batches
@app.post("/batches/", response_model=schemas.ProcessedLeaves)
def create_new_batch(batch: schemas.ProcessedLeavesCreate, db: Session = Depends(get_db)):
    return crud.create_batch(db=db, batch=batch)

@app.get("/batches/", response_model=List[schemas.ProcessedLeaves])
def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    batches = crud.get_all_batches(db=db, skip=skip, limit=limit)
    return batches

@app.get("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def read_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = crud.get_batch_by_id(db=db, batch_id=batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@app.put("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def update_existing_batch(batch_id: int, update_data: schemas.ProcessedLeavesUpdate, db: Session = Depends(get_db)):
    batch = crud.update_batch(db=db, batch_id=batch_id, update_data=update_data)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@app.delete("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def delete_existing_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = crud.delete_batch(db=db, batch_id=batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@app.get("/drying-activities/{drying_id}/date", response_model=schemas.DryingActivityBase)
def get_dried_date(drying_id: str, db: Session = Depends(get_db)):
    date = crud.batch_get_dried_date(db=db, drying_id=drying_id)
    if date is None:
        raise HTTPException(status_code=404, detail="Drying activity not found")
    return {"date": date}

@app.get("/flouring-activities/{flouring_id}/date", response_model=schemas.FlouringActivityBase)
def get_floured_date(flouring_id: str, db: Session = Depends(get_db)):
    date = crud.batch_get_floured_date(db=db, flouring_id=flouring_id)
    if date is None:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    return {"date": date}


# Machines

#DRYING
@app.post("/drying_machines/{machine_id}/start", response_model=schemas.DryingMachine)
def start_machine(machine_id: str, db: Session = Depends(get_db)):
    success = crud.start_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be started")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@app.post("/drying_machines/{machine_id}/stop", response_model=schemas.DryingMachine)
def stop_machine(machine_id: str, db: Session = Depends(get_db)):
    success = crud.stop_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be stopped")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@app.get("/drying_machines/{machine_id}/status", response_model=str)
def read_machine_status(machine_id: int, db: Session = Depends(get_db)):
    status = crud.get_drying_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status

#FLOURING
@app.get("/flouring_machines/{machine_id}/status", response_model=str)
def read_flouring_machine_status(machine_id: str, db: Session = Depends(get_db)):
    status = crud.get_flouring_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status

@app.post("/flouring_machines/{machine_id}/start")
def start_flouring_machine(machine_id: str, db: Session = Depends(get_db)):
    success = crud.start_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start the machine or machine already running")
    return {"message": "Machine started successfully"}

@app.post("/flouring_machines/{machine_id}/stop")
def stop_flouring_machine(machine_id: str, db: Session = Depends(get_db)):
    success = crud.stop_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop the machine or machine already idle")
    return {"message": "Machine stopped successfully"}



#WET LEAVES COLLECTIONS
@app.post("/wet-leaves-collections/", response_model=schemas.WetLeavesCollection)
def create_wet_leaves_collection(wet_leaves_collection: schemas.WetLeavesCollectionCreate, db: Session = Depends(get_db)):
    return crud.create_wet_leaves_collection(db=db, wet_leaves_collection=wet_leaves_collection)

@app.get("/wet-leaves-collections/", response_model=list[schemas.WetLeavesCollection])
def read_wet_leaves_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_wet_leaves_collections(db=db, skip=skip, limit=limit)

@app.get("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def read_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db)):
    db_wet_leaves_collection = crud.get_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

@app.put("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def update_wet_leaves_collection(wet_leaves_batch_id: str, update_data: schemas.WetLeavesCollectionUpdate, db: Session = Depends(get_db)):
    db_wet_leaves_collection = crud.update_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id, update_data=update_data)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

@app.delete("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def delete_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db)):
    db_wet_leaves_collection = crud.delete_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

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
async def schedule_pickup(pickup_data: schemas.ShipmentPickupSchedule, db: Session = Depends(get_db)):
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
    centras = crud.get_all_centras(db)
    return centras

@app.post("/centras", response_model=schemas.CentraDetails)
async def add_new_centra(centra_data: schemas.CentraDetails, db: Session = Depends(get_db)):
    new_centra = add_new_centra(db, centra_data)
    return new_centra

# Shipment (XYZ)

# @app.put("/shipments/{shipment_id}")
# async def update_shipment_details(shipment_id: str, shipment_update: ShipmentUpdate, db: Session = Depends(get_db)):
#     updated = update_shipment(db, shipment_id, shipment_update)
#     if updated:
#         return updated
#     raise HTTPException(status_code=404, detail="Shipment not found")


@app.delete("/shipments/{shipment_id}")
async def remove_shipment(shipment_id: str, db: Session = Depends(get_db)):
    deleted = delete_shipment(db, shipment_id)
    if deleted:
        return {"message": "Shipment deleted successfully"}
    raise HTTPException(status_code=404, detail="Shipment not found")

# Harborguards
@app.get("/harborguards")
async def show_all_harbor_guards(db: Session = Depends(get_db)):
    guards = crud.get_all_harbor_guards(db)
    return guards

@app.get("/harborguards/{guard_id}")
async def show_harbor_guard(guard_id: int, db: Session = Depends(get_db)):
    guard = crud.get_harbor_guard(db, guard_id)
    return guard

@app.post("/harborguards", response_model=schemas.HarborGuardCreate)
async def add_harbor_guard(guard_data: schemas.HarborGuardCreate, db: Session = Depends(get_db)):
    new_guard = crud.create_harbor_guard(db, guard_data)
    return new_guard

@app.put("/harborguards/{guard_id}", response_model=schemas.HarborGuardUpdate)
async def modify_harbor_guard(guard_id: int, guard_data: schemas.HarborGuardUpdate, db: Session = Depends(get_db)):
    updated_guard = crud.update_harbor_guard(db, guard_id, guard_data)
    return updated_guard

@app.delete("/harborguards/{guard_id}")
async def remove_harbor_guard(guard_id: int, db: Session = Depends(get_db)):
    result = crud.delete_harbor_guard(db, guard_id)
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

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

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