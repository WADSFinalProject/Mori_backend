from fastapi import APIRouter, Request, Depends, HTTPException, Query, Depends
from database import get_db
from sqlalchemy.orm import Session
from typing import List
import schemas, crud, models
from middleware import get_current_user

secured_router = APIRouter()

# test protected route
@secured_router.get("/protected-route")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user": user["sub"]}

# Batches
@secured_router.post("/batches/", response_model=schemas.ProcessedLeaves)
def create_new_batch(batch: schemas.ProcessedLeavesCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_batch(db=db, batch=batch)

# @secured_router.get("/batches/", response_model=List[schemas.ProcessedLeaves])
# def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     batches = crud.get_all_batches(db=db, skip=skip, limit=limit)
#     return batches

@secured_router.get("/batches/", response_model=List[schemas.ProcessedLeaves])
def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batches = crud.get_all_batches(db=db, skip=skip, limit=limit)
    return batches

@secured_router.get("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def read_batch(batch_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batch = crud.get_batch_by_id(db=db, batch_id=batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@secured_router.put("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def update_existing_batch(batch_id: int, update_data: schemas.ProcessedLeavesUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batch = crud.update_batch(db=db, batch_id=batch_id, update_data=update_data)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@secured_router.delete("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def delete_existing_batch(batch_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    result = crud.delete_batch(db=db, batch_id=batch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return result

#DRYING
@secured_router.post("/drying-machine/create/")
def add_drying_machine(drying_machine: schemas.DryingMachineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    new_machine = crud.create_drying_machine(db, drying_machine)
    if new_machine:
        return {"message": "Drying machine created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Drying machine with the same ID already exists!")

@secured_router.post("/drying_machines/{machine_id}/start", response_model=schemas.DryingMachine)
def start_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    success = crud.start_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be started")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@secured_router.post("/drying_machines/{machine_id}/stop", response_model=schemas.DryingMachine)
def stop_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    success = crud.stop_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be stopped")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@secured_router.get("/drying_machines/{machine_id}/status", response_model=str)
def read_machine_status(machine_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    status = crud.get_drying_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status

@secured_router.get("/drying_machines/", response_model=List[schemas.DryingMachine])
def read_drying_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "admin":
        drying_machines = crud.get_all_drying_machines(db=db, skip=skip, limit=limit)
    elif user["role"] == "centra":
        drying_machines = crud.get_drying_machines_by_creator(db=db, creator_id=user["id"], skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return drying_machines

@secured_router.get("/drying_machine/{machine_id}", response_model=schemas.DryingMachine)
def read_drying_machine(machine_id: str, db: Session = Depends(get_db)):
    db_drying_machine = crud.delete_drying_machine(db, machine_id)
    if db_drying_machine is None:
        raise HTTPException(status_code=404, detail="Drying machine not found")
    return db_drying_machine

@secured_router.delete("/drying-machine/{machine_id}", response_model=schemas.DryingMachine)
def delete_drying_machine(machine_id: str, db: Session = Depends(get_db)):
    db_drying_machine = crud.get_drying_machine(db, machine_id)
    if db_drying_machine is None:
        raise HTTPException(status_code=404, detail="Drying machine not found")
    
    db.delete(db_drying_machine)
    db.commit()
    return None

 #drying activity  
@secured_router.post("/drying_activity/create")
def create_drying_activity(drying_activity: schemas.DryingActivityCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    dry_activity = crud.add_new_drying_activity(db, drying_activity)
    if dry_activity:
        return {"message": "Drying activity created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Drying machine with the same ID already exists!")

@secured_router.get("/drying-activities/{drying_id}")
def show_drying_activity(drying_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    drying = crud.get_drying_activity(db, drying_id)
    return drying

@secured_router.get("/drying_activity/", response_model=List[schemas.DryingActivity])
def read_drying_activity(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    drying_activity = crud.get_all_drying_activity(db=db, skip=skip, limit=limit)
    return drying_activity

@secured_router.put("/drying-activities/{drying_id}")
def update_drying_activity(drying_id: int, drying_activity: schemas.DryingActivityUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_drying_activity = crud.update_drying_activity(db, drying_id, drying_activity)
    if db_drying_activity is None:
        raise HTTPException(status_code=404, detail="Drying activity not found")
    return db_drying_activity

@secured_router.delete("/drying-activities/{drying_id}")
def delete_drying_activity(drying_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_drying_activity = crud.delete_drying_activity(db, drying_id)
    if db_drying_activity is None:
        raise HTTPException(status_code=404, detail="Drying activity not found")
    return db_drying_activity

#driedleaves
@secured_router.post("/dried_leaves/", response_model=schemas.DriedLeaves)
def create_dried_leaf(dried_leaf: schemas.DriedLeavesCreate, db: Session = Depends(get_db)):
    return crud.create_dried_leaf(db=db, dried_leaf=dried_leaf)

# @secured_router.get("/dried_leaves/", response_model=list[schemas.DriedLeaves])
# def read_dried_leaves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     return crud.get_dried_leaves(db=db, skip=skip, limit=limit)

@secured_router.get("/dried_leaves/", response_model=List[schemas.DriedLeaves])
def read_dried_leaves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "admin":
        wet_leaves_collections = crud.get_dried_leaves(db=db, skip=skip, limit=limit)
    elif user["role"] == "centra":
        wet_leaves_collections = crud.get_dried_leaves_by_creator(db=db, creator_id=user["centralID"], skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return wet_leaves_collections

@secured_router.get("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeaves)
def read_dried_leaf(leaf_id: int, db: Session = Depends(get_db)):
    db_dried_leaf = crud.get_dried_leaf(db=db, leaf_id=leaf_id)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

@secured_router.put("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeaves)
def update_dried_leaf(leaf_id: int, dried_leaf: schemas.DriedLeavesUpdate, db: Session = Depends(get_db)):
    db_dried_leaf = crud.update_dried_leaf(db=db, leaf_id=leaf_id, dried_leaf=dried_leaf)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

@secured_router.delete("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeaves)
def delete_dried_leaf(leaf_id: int, db: Session = Depends(get_db)):
    db_dried_leaf = crud.delete_dried_leaf(db=db, leaf_id=leaf_id)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

#FLOURING
@secured_router.post("/flouring-machine/create/")
def add_flouring_machine(flouring_machine: schemas.FlouringMachineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    new_machine = crud.add_new_flouring_machine(db, flouring_machine)
    if new_machine:
        return {"message": "Flouring machine created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Flouring machine with the same ID already exists!")

@secured_router.get("/flouring_machines/{machine_id}/status", response_model=str)
def read_flouring_machine_status(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    status = crud.get_flouring_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status

@secured_router.get("/flouring_machines/", response_model=List[schemas.FlouringMachine])
def read_flouring_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    flouring_machines = crud.get_all_flouring_machines(db=db, skip=skip, limit=limit)
    return flouring_machines

@secured_router.post("/flouring_machines/{machine_id}/start")
def start_flouring_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    success = crud.start_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start the machine or machine already running")
    return {"message": "Machine started successfully"}

@secured_router.post("/flouring_machines/{machine_id}/stop")
def stop_flouring_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    success = crud.stop_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop the machine or machine already idle")
    return {"message": "Machine stopped successfully"}

@secured_router.delete("/flouring-machine/{machine_id}", response_model=schemas.FlouringMachine)
def delete_flouring_machine(machine_id: str, db: Session = Depends(get_db)):
    db_flouring_machine = crud.delete_flouring_machine(db, machine_id)
    if db_flouring_machine is None:
        raise HTTPException(status_code=404, detail="Flouring machine not found")
    
    # db.delete(db_flouring_machine)
    # db.commit()
    return {"message": "Flouring machine successfully deleted"}

#flouring activity
@secured_router.post("/flouring_activity/create")
def create_flouring_activity(flouring_activity: schemas.FlouringActivityCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    flour_activity = crud.add_new_flouring_activity(db, flouring_activity)
    if flour_activity:
        return {"message": "Flouring activity created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Flouring machine with the same ID already exists!")

    
@secured_router.get("/flouring_activity/", response_model=List[schemas.FlouringActivity])
def read_flouring_activity(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    flouring_activity = crud.get_all_flouring_activity(db=db, skip=skip, limit=limit)
    return flouring_activity

@secured_router.get("/flouring_activity/{flouring_id}", response_model=schemas.FlouringActivity)
def get_flouring_activity(flouring_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    flouring_activity = crud.get_flouring_activity(db=db, flouring_id=flouring_id)
    if not flouring_activity:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    return flouring_activity

@secured_router.put("/flouring_activity/update/{flouring_id}", response_model=schemas.FlouringActivity)
def update_flouring_activity(flouring_id: int, flouring_activity: schemas.FlouringActivityUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    updated_flouring = crud.update_flouring_activity(db, flouring_id, flouring_activity)
    if not updated_flouring:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    return updated_flouring

@secured_router.delete("/flouring_activity/delete/{flouring_id}")
def delete_flouring_activity(flouring_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    deleted_flouring_activity = crud.delete_flouring_activity(db=db, flouring_id=flouring_id)
    if not deleted_flouring_activity:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    
    return {"message": "Flouring activity successfully deleted",}



#WET LEAVES COLLECTIONS
@secured_router.post("/wet-leaves-collections/create")
def create_wet_leaves_collection(wet_leaves_collection: schemas.WetLeavesCollectionCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.add_new_wet_leaves_collection(db, wet_leaves_collection)

@secured_router.get("/wet-leaves-collections/", response_model=List[schemas.WetLeavesCollection])
def read_wet_leaves_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "admin":
        wet_leaves_collections = crud.get_all_wet_leaves_collections(db=db, skip=skip, limit=limit)
    elif user["role"] == "centra":
        wet_leaves_collections = crud.get_wet_leaves_collections_by_creator(db=db, creator_id=user["centralID"], skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return wet_leaves_collections

@secured_router.get("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def read_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_wet_leaves_collection = crud.get_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

# @secured_router.put("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
# def update_wet_leaves_collection(wet_leaves_batch_id: str, update_data: schemas.WetLeavesCollectionUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     db_wet_leaves_collection = crud.update_wet_leaves_status(db=db, wet_leaves_batch_id=wet_leaves_batch_id, update_data=update_data)
#     if db_wet_leaves_collection is None:
#         raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
#     return db_wet_leaves_collection

@secured_router.put("/wet_leaves-collection/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def update_wet_leaves_collection(wet_leaves_batch_id: int, update_data: schemas.WetLeavesCollectionUpdate, db: Session = Depends(get_db)):
    return crud.update_wet_leaves_collection(db, wet_leaves_batch_id, update_data)

@secured_router.delete("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def delete_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_wet_leaves_collection = crud.delete_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

# # Shipments (Centra)
# @secured_router.post("/shipments")
# async def add_shipment(shipment_data: schemas.ShipmentCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     added_shipment = crud.add_shipment(db, shipment_data)
#     return added_shipment

# @secured_router.put("/shipments/{shipment_id}")
# async def update_shipment(shipment_id: int, shipment_update: schemas.ShipmentUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     updated_shipment = crud.update_shipment(db, shipment_id, shipment_update)
#     if updated_shipment:
#         return updated_shipment
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.get("/notifications")
# async def show_notifications(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     notifications = crud.get_notifications(db)
#     return {"notifications": notifications}

# @secured_router.get("/shipments", response_model=List[schemas.Shipment])
# def read_shipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     shipments = crud.get_all_shipments(db=db, skip=skip, limit=limit)
#     return shipments

# @secured_router.get("/shipments/{shipment_id}")
# async def get_shipment_details(shipment_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     shipment = crud.get_shipment_details(db, shipment_id)
#     if shipment:
#         return shipment
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.delete("/shipments/{shipment_id}")
# async def delete_shipment(shipment_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     if crud.delete_shipment(db, shipment_id):
#         return {"message": "Shipment deleted"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.post("/shipments/{shipment_id}/confirm")
# async def confirm_shipment(shipment_id: int, confirmation: schemas.ShipmentConfirmation, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     if crud.confirm_shipment(db, shipment_id, confirmation.weight):
#         return {"message": "Shipment confirmed"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.post("/shipments/{shipment_id}/report")
# async def report_shipment_issue(shipment_id: int, issue: schemas.ShipmentIssue, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     if crud.report_shipment_issue(db, shipment_id, issue.description):
#         return {"message": "Issue reported successfully"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.post("/shipments/{shipment_id}/confirm")
# async def confirm_shipment_arrival(shipment_id: int, confirmation: schemas.ShipmentConfirmation, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     if crud.confirm_shipment(db, shipment_id, confirmation.weight):
#         return {"message": "Shipment confirmed"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# @secured_router.put("/shipments/{shipment_id}/rescale")
# async def rescale_shipment(shipment_id: int, rescale: schemas.ShipmentRescale, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     if crud.rescale_shipment(db, shipment_id, rescale.new_weight):
#         return {"message": "Shipment weight updated"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

#pickup
@secured_router.get("/pickup/{pickup_id}", response_model=schemas.Pickup)
def read_pickup(pickup_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_pickup = crud.get_pickup(db, pickup_id)
    if db_pickup is None:
        raise HTTPException(status_code=404, detail="Pickup not found")
    return db_pickup

@secured_router.get("/pickup/", response_model=list[schemas.Pickup])
def read_pickups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    pick_list = crud.get_all_pickups(db, skip=skip, limit=limit)
    return pick_list

@secured_router.post("/pickup/", response_model=schemas.Pickup)
def create_pickup(pickup: schemas.PickupCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_pickup(db=db, pickup=pickup)

@secured_router.put("/pickup/{pickup_id}", response_model=schemas.Pickup)
def update_pickup(pickup_id: int, pickup: schemas.PickupBase, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_pickup = crud.update_pickup(db, pickup_id, pickup)
    if db_pickup is None:
        raise HTTPException(status_code=404, detail="Pickup not found")
    return db_pickup

@secured_router.delete("/pickup/{pickup_id}", response_model=schemas.Pickup)
def delete_pickup(pickup_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_pickup = crud.delete_pickup(db, pickup_id)
    if db_pickup is None:
        raise HTTPException(status_code=404, detail="Pickup not found")
    return db_pickup

# Stocks
@secured_router.get("/stocks")
async def show_all_stock_details(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    stocks = crud.get_all_stocks(db)
    return stocks

@secured_router.get("/stocks/{location_id}")
async def show_stock_detail(location_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    stock = crud.get_stock_detail(db, location_id)
    if stock:
        return stock
    raise HTTPException(status_code=404, detail="Location not found")


# Locations
@secured_router.get("/location/{location_id}")
async def show_location_details(location_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    location = crud.get_location_details(db, location_id)
    if location:
        return location
    raise HTTPException(status_code=404, detail="Location not found")

# Shipment History
# @secured_router.get("/shipments/{location_id}/history")
# async def show_shipment_history(location_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     shipment_history = crud.get_shipment_history(db, location_id)
#     if shipment_history:
#         return shipment_history
#     raise HTTPException(status_code=404, detail="Location not found")

# @secured_router.post("/shipments/schedule-pickup")
# async def schedule_pickup(pickup_data: schemas.ShipmentPickupSchedule, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     is_valid = crud.validate_shipment_id(db, pickup_data.shipment_id)
#     if is_valid:
#         result = crud.schedule_pickup(db, pickup_data)
#         if result:
#             return {"message": "Pickup scheduled successfully"}
#         return {"error": "Failed to schedule pickup"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# Centra
@secured_router.get("/centras")
async def show_all_centras(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    centras = crud.get_all_centras(db)
    return centras

@secured_router.get("/centras/{centra_id}", response_model=schemas.Centra)
def read_centra(CentralID: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    centra = crud.get_centra_by_id(db, CentralID)
    return centra

@secured_router.post("/centras", response_model=schemas.Centra)
async def create_new_centra(centra_data: schemas.CentraCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    new_centra = crud.add_new_centra(db, centra_data)
    return new_centra

@secured_router.put("/centras/{centra_id}", response_model=schemas.Centra)
def update_centra(CentralID: int, centra_update: schemas.CentraUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.update_centra(db, CentralID, centra_update)

@secured_router.delete("/centras/{centra_id}", response_model=dict)
def delete_centra(CentralID: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.delete_centra(db, CentralID)

#userCentra
@secured_router.get("/usercentra/", response_model=List[schemas.UserCentra])
def read_user_centra(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_centra = crud.get_user_centra(db=db, skip=skip, limit=limit)
    return user_centra

@secured_router.get("/usercentra/{user_centra_id}", response_model=schemas.UserCentra)
def read_user_centra_by_id(user_centra_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_centra = crud.get_user_centra_by_id(db=db, user_centra_id=user_centra_id)
    if user_centra is None:
        raise HTTPException(status_code=404, detail="UserCentra not found")
    return user_centra

@secured_router.get('/usercentra/by-user/{user_id}', response_model=schemas.UserCentra)
def read_user_centra_by_user(user_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user_centra = crud.get_user_centra_by_user_id(db=db, user_id=user_id)
    if user_centra is None: 
        raise HTTPException(status_code=404, detail="UserCentra not found")
    return user_centra

@secured_router.post("/usercentra/", response_model=schemas.UserCentra)
def create_user_centra(user_centra: schemas.UserCentraCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_user_centra(db=db, user_centra=user_centra)

@secured_router.patch("/usercentra/{user_centra_id}", response_model=schemas.UserCentra)
def update_user_centra(user_centra_id: int, user_centra: schemas.UserCentraUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_user_centra = crud.update_user_centra(db=db, user_centra_id=user_centra_id, user_centra=user_centra)
    if db_user_centra is None:
        raise HTTPException(status_code=404, detail="UserCentra not found")
    return db_user_centra

@secured_router.delete("/usercentra/{user_centra_id}", response_model=schemas.UserCentra)
def delete_user_centra(user_centra_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_user_centra = crud.delete_user_centra(db=db, user_centra_id=user_centra_id)
    if db_user_centra is None:
        raise HTTPException(status_code=404, detail="UserCentra not found")
    return db_user_centra

# Shipment (XYZ)

# @secured_router.put("/shipments/{shipment_id}")
# async def update_shipment_details(shipment_id: str, shipment_update: ShipmentUpdate, db: Session = Depends(get_db)):
#     updated = update_shipment(db, shipment_id, shipment_update)
#     if updated:
#         return updated
#     raise HTTPException(status_code=404, detail="Shipment not found")


# @secured_router.delete("/shipments/{shipment_id}")
# async def remove_shipment(shipment_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     deleted = delete_shipment(db, shipment_id)
#     if deleted:
#         return {"message": "Shipment deleted successfully"}
#     raise HTTPException(status_code=404, detail="Shipment not found")

# Harborguards
@secured_router.post("/harborguard/", response_model=schemas.HarborGuardInDB)
def create_harbor_guard(harbor_guard: schemas.HarborGuardCreate, db: Session = Depends(get_db)):
    return crud.create_harbor_guard(db, harbor_guard)

@secured_router.get("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def read_harbor_guard(harbour_id: int, db: Session = Depends(get_db)):
    db_harbor_guard = crud.get_harbor_guard(db, harbour_id)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.put("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def update_harbor_guard(harbour_id: int, harbor_guard: schemas.HarborGuardUpdate, db: Session = Depends(get_db)):
    db_harbor_guard = crud.update_harbor_guard(db, harbour_id, harbor_guard)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.delete("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def delete_harbor_guard(harbour_id: int, db: Session = Depends(get_db)):
    db_harbor_guard = crud.delete_harbor_guard(db, harbour_id)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.get("/harborguard/", response_model=list[schemas.HarborGuardInDB])
def read_harbor_guards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    harbor_guards = crud.get_all_harbor_guards(db, skip=skip, limit=limit)
    return harbor_guards

# Warehouses
@secured_router.get("/warehouses", response_model=List[schemas.Warehouse])
async def show_all_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    warehouses = crud.get_all_warehouses(db, skip=skip, limit=limit)
    return warehouses

@secured_router.get("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def get_warehouse(warehouse_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    warehouse = crud.get_warehouse(db, warehouse_id=warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

@secured_router.post("/warehouses", response_model=schemas.Warehouse)
async def create_warehouse(warehouse_data: schemas.WarehouseCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_warehouse(db=db, warehouse_data=warehouse_data)

@secured_router.put("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def update_warehouse(warehouse_id: str, warehouse_data: schemas.WarehouseUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    updated_warehouse = crud.update_warehouse(db, warehouse_id=warehouse_id, update_data=warehouse_data)
    if updated_warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return updated_warehouse

@secured_router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(warehouse_id: str, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    deleted_warehouse = crud.delete_warehouse(db, warehouse_id=warehouse_id)
    if deleted_warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return {"message": "Warehouse deleted successfully"}

#xyzuser
@secured_router.get("/xyzusers/", response_model=List[schemas.XYZuser])
def read_xyzusers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    xyzusers = crud.get_xyzusers(db=db, skip=skip, limit=limit)
    return xyzusers

@secured_router.get("/xyzusers/{xyzuser_id}", response_model=schemas.XYZuser)
def read_xyzuser(xyzuser_id: int, db: Session = Depends(get_db)):
    xyzuser = crud.get_xyzuser_by_id(db=db, xyzuser_id=xyzuser_id)
    if xyzuser is None:
        raise HTTPException(status_code=404, detail="XYZuser not found")
    return xyzuser

@secured_router.post("/xyzusers/", response_model=schemas.XYZuser)
def create_xyzuser(xyzuser: schemas.XYZuserCreate, db: Session = Depends(get_db)):
    return crud.create_xyzuser(db=db, xyzuser=xyzuser)

@secured_router.patch("/xyzusers/{xyzuser_id}", response_model=schemas.XYZuser)
def update_xyzuser(xyzuser_id: int, xyzuser: schemas.XYZuserUpdate, db: Session = Depends(get_db)):
    db_xyzuser = crud.update_xyzuser(db=db, xyzuser_id=xyzuser_id, xyzuser=xyzuser)
    if db_xyzuser is None:
        raise HTTPException(status_code=404, detail="XYZuser not found")
    return db_xyzuser

@secured_router.delete("/xyzusers/{xyzuser_id}", response_model=schemas.XYZuser)
def delete_xyzuser(xyzuser_id: int, db: Session = Depends(get_db)):
    db_xyzuser = crud.delete_xyzuser(db=db, xyzuser_id=xyzuser_id)
    if db_xyzuser is None:
        raise HTTPException(status_code=404, detail="XYZuser not found")
    return db_xyzuser

# User (Admin)
# @secured_router.post("/admins/", response_model=schemas.Admin)
# def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
#     db_admin = crud.get_admin_by_email(db, email=admin.email)
#     if db_admin:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_admin(db=db, admin=admin)

# @secured_router.get("/admins/", response_model=List[schemas.Admin])
# def read_admins(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     admins = crud.get_admins(db, skip=skip, limit=limit)
#     return admins

# @secured_router.get("/admins/{admin_id}", response_model=schemas.Admin)
# def read_admin(admin_id: int, db: Session = Depends(get_db)):
#     db_admin = crud.get_admin(db, admin_id=admin_id)
#     if db_admin is None:
#         raise HTTPException(status_code=404, detail="Admin not found")
#     return db_admin

# @secured_router.put("/admins/{admin_id}", response_model=schemas.Admin)
# def update_admin(admin_id: int, admin: schemas.AdminUpdate, db: Session = Depends(get_db)):
#     db_admin = crud.update_admin(db, admin_id=admin_id, admin=admin)
#     if db_admin is None:
#         raise HTTPException(status_code=404, detail="Admin not found")
#     return db_admin

# @secured_router.delete("/admins/{admin_id}", response_model=schemas.Admin)
# def delete_admin(admin_id: int, db: Session = Depends(get_db)):
#     db_admin = crud.delete_admin(db, admin_id=admin_id)
#     if db_admin is None:
#         raise HTTPException(status_code=404, detail="Admin not found")
#     return db_admin

#CentraShipment
# @secured_router.post("/shipments/", response_model=schemas.CentraShipmentBase)
# def create_shipment(shipment: schemas.CentraShipmentCreate, db: Session = Depends(get_db)):
#     return crud.create_shipment(db, shipment)

# @secured_router.delete("/shipments/{shipment_id}", response_model=schemas.CentraShipment)
# def delete_shipment(shipment_id: int, db: Session = Depends(get_db)):
#     deleted = crud.delete_shipment(db, shipment_id)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="Shipment not found")
#     return {"message": "Shipment deleted successfully"}

#expedition
@secured_router.post("/expeditions/", response_model=schemas.Expedition)
def create_expedition(expedition: schemas.ExpeditionCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_expedition(db, expedition)

@secured_router.get("/expeditions/", response_model=List[schemas.Expedition])
def read_expeditions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    expeditions = crud.get_expeditions(db=db, skip=skip, limit=limit)
    return expeditions

@secured_router.get("/expeditions/{expedition_id}", response_model=schemas.Expedition)
def read_expedition(expedition_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    expedition = crud.get_expedition(db=db, expedition_id=expedition_id)
    if expedition is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return expedition

@secured_router.put("/expeditions/{expedition_id}", response_model=schemas.Expedition)
def update_expedition(expedition_id: int, expedition: schemas.ExpeditionUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_expedition = crud.update_expedition(db=db, expedition_id=expedition_id, expedition=expedition)
    if db_expedition is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return db_expedition

@secured_router.delete("/expeditions/{expedition_id}", response_model=schemas.Expedition)
def delete_expedition(expedition_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_expedition = crud.delete_expedition(db, expedition_id)
    if db_expedition is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return db_expedition

@secured_router.put("/expeditions/{expedition_id}/change_status")
def change_expedition_status_route(expedition_id: int, new_status: str, db: Session = Depends(get_db)):
    expedition = crud.change_expedition_status(db, expedition_id, new_status)
    if expedition is None:
        raise HTTPException(status_code=404, detail=f"Expedition with id {expedition_id} not found")
    return {"message": f"Status of Expedition {expedition_id} changed to {new_status}"}


@secured_router.put("/expeditions/{expedition_id}/confirm", response_model=schemas.Expedition)
def confirm_expedition_route(expedition_id: int, TotalWeight: int, db: Session = Depends(get_db)):
    expedition = crud.confirm_expedition(db, expedition_id, TotalWeight)
    if expedition is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return expedition

#expeditioncontent

@secured_router.post("/expedition_contents/", response_model=schemas.ExpeditionContent)
def create_expedition_content(expedition_content: schemas.ExpeditionContentCreate, db: Session = Depends(get_db)):
    return crud.create_expedition_content(db=db, expedition_content=expedition_content)

@secured_router.get("/expedition_contents/{expedition_content_id}", response_model=schemas.ExpeditionContent)
def read_expedition_content(expedition_content_id: int, db: Session = Depends(get_db)):
    db_expedition_content = crud.get_expedition_content(db, expedition_content_id=expedition_content_id)
    if db_expedition_content is None:
        raise HTTPException(status_code=404, detail="Expedition content not found")
    return db_expedition_content

@secured_router.get("/expedition_contents/", response_model=List[schemas.ExpeditionContent])
def read_expedition_contents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    expedition_contents = crud.get_expedition_contents(db, skip=skip, limit=limit)
    return expedition_contents

@secured_router.put("/expedition_contents/{expedition_content_id}", response_model=schemas.ExpeditionContent)
def update_expedition_content(expedition_content_id: int, expedition_content: schemas.ExpeditionContentUpdate, db: Session = Depends(get_db)):
    db_expedition_content = crud.update_expedition_content(db, expedition_content_id=expedition_content_id, expedition_content=expedition_content)
    if db_expedition_content is None:
        raise HTTPException(status_code=404, detail="Expedition content not found")
    return db_expedition_content

@secured_router.delete("/expedition_contents/{expedition_content_id}", response_model=schemas.ExpeditionContent)
def delete_expedition_content(expedition_content_id: int, db: Session = Depends(get_db)):
    db_expedition_content = crud.delete_expedition_content(db, expedition_content_id=expedition_content_id)
    if db_expedition_content is None:
        raise HTTPException(status_code=404, detail="Expedition content not found")
    return db_expedition_content

#received package
@secured_router.post("/received_packages/", response_model=schemas.ReceivedPackage)
def create_received_package(received_package: schemas.ReceivedPackageCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_received_package(db=db, received_package=received_package)

@secured_router.get("/received_packages/", response_model=List[schemas.ReceivedPackage])
def read_received_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    received_packages = crud.get_received_packages(db=db, skip=skip, limit=limit)
    return received_packages

@secured_router.get("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
def read_received_package(package_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    received_package = crud.get_received_package(db=db, package_id=package_id)
    if received_package is None:
        raise HTTPException(status_code=404, detail="Received package not found")
    return received_package

@secured_router.put("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
def update_received_package(package_id: int, received_package: schemas.ReceivedPackageUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_received_package = crud.update_received_package(db=db, package_id=package_id, received_package=received_package)
    if db_received_package is None:
        raise HTTPException(status_code=404, detail="Received package not found")
    return db_received_package

@secured_router.delete("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
def delete_received_package(package_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_received_package = crud.delete_received_package(db=db, package_id=package_id)
    if db_received_package is None:
        raise HTTPException(status_code=404, detail="Received package not found")
    return db_received_package

#package receipt
@secured_router.post("/package_receipts/", response_model=schemas.PackageReceipt)
def create_package_receipt(package_receipt: schemas.PackageReceiptCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_package_receipt(db, package_receipt)

@secured_router.get("/package_receipts/{receipt_id}", response_model=schemas.PackageReceipt)
def read_package_receipt(receipt_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_package_receipt = crud.get_package_receipt(db, receipt_id)
    if db_package_receipt is None:
        raise HTTPException(status_code=404, detail="Package receipt not found")
    return db_package_receipt

@secured_router.get("/package_receipts/", response_model=List[schemas.PackageReceipt])
def read_package_receipts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    package_receipts = crud.get_package_receipts(db, skip=skip, limit=limit)
    return package_receipts

@secured_router.put("/package_receipts/{receipt_id}", response_model=schemas.PackageReceipt)
def update_package_receipt(receipt_id: int, package_receipt: schemas.PackageReceiptUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_package_receipt = crud.update_package_receipt(db, receipt_id, package_receipt)
    if db_package_receipt is None:
        raise HTTPException(status_code=404, detail="Package receipt not found")
    return db_package_receipt

@secured_router.delete("/package_receipts/{receipt_id}", response_model=schemas.PackageReceipt)
def delete_package_receipt(receipt_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_package_receipt = crud.delete_package_receipt(db, receipt_id)
    if db_package_receipt is None:
        raise HTTPException(status_code=404, detail="Package receipt not found")
    return db_package_receipt

#product receipt
@secured_router.post("/product_receipts/", response_model=schemas.ProductReceipt)
def create_product_receipt(product_receipt: schemas.ProductReceiptCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_product_receipt(db, product_receipt)

@secured_router.get("/product_receipts/{product_receipt_id}", response_model=schemas.ProductReceipt)
def read_product_receipt(product_receipt_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_product_receipt = crud.get_product_receipt(db, product_receipt_id)
    if db_product_receipt is None:
        raise HTTPException(status_code=404, detail="Product receipt not found")
    return db_product_receipt

@secured_router.get("/product_receipts/", response_model=List[schemas.ProductReceipt])
def read_product_receipts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    product_receipts = crud.get_product_receipts(db, skip=skip, limit=limit)
    return product_receipts

@secured_router.put("/product_receipts/{product_receipt_id}", response_model=schemas.ProductReceipt)
def update_product_receipt(product_receipt_id: int, product_receipt: schemas.ProductReceiptUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_product_receipt = crud.update_product_receipt(db, product_receipt_id, product_receipt)
    if db_product_receipt is None:
        raise HTTPException(status_code=404, detail="Product receipt not found")
    return db_product_receipt

@secured_router.delete("/product_receipts/{product_receipt_id}", response_model=schemas.ProductReceipt)
def delete_product_receipt(product_receipt_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_product_receipt = crud.delete_product_receipt(db, product_receipt_id)
    if db_product_receipt is None:
        raise HTTPException(status_code=404, detail="Product receipt not found")
    return db_product_receipt

# Users in admin page
@secured_router.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = crud.create_user(db=db, user=user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_user

@secured_router.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, sort_by: str = Query('Name'), sort_order: str = Query('asc'), role: str = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return crud.get_all_users(db=db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, role=role)

@secured_router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@secured_router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, update_data: schemas.UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = crud.update_user(db=db, user_id=user_id, update_data=update_data)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@secured_router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = crud.delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user