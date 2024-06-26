from fastapi import APIRouter, Request, Depends, HTTPException, Query, Depends
from database import get_db
from sqlalchemy.orm import Session
from typing import List
import schemas, crud, models, SMTP
from dependencies import get_current_user, centra_user, harbour_user, admin_user

secured_router = APIRouter()

# test protected route
@secured_router.get("/protected-route")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user": user["sub"]}

@secured_router.get("/user", response_model=schemas.User)
def read_user(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user
    
# Batches
@secured_router.get("/batches/", response_model=List[schemas.ProcessedLeaves_DriedDate])
def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    if user["role"] == "Admin":
        # If the user is an admin, fetch all batches regardless of central_id
        batches = crud.get_all_batches(db=db, skip=skip, limit=limit)
    else:
        # If the user is a Centra user, fetch batches specific to their central_id
        central_id = user.get("centralID")
        if central_id is None:
            raise HTTPException(status_code=400, detail="centralID is missing from user data")
        batches = crud.get_all_batches(db=db, central_id=central_id, skip=skip, limit=limit)
    return batches

@secured_router.post("/batches/", response_model=schemas.ProcessedLeaves)
def create_batch(batch: schemas.ProcessedLeavesCreate, db: Session = Depends(get_db)):
    created_batch = crud.create_batch(db=db, batch=batch)
    return created_batch

# @secured_router.get("/batches/", response_model=List[schemas.ProcessedLeaves])
# def read_batches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
#     batches = crud.get_all_batches(db=db, skip=skip, limit=limit)
#     return batches

@secured_router.get("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def read_batch(batch_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    batch = crud.get_batch_by_id(db=db, batch_id=batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

# @secured_router.get("/batchesDates/{batch_id}")
# def getDatesBatch(batch_id:int, db:Session = Depends(get_db)):
#     driedDate = 

@secured_router.put("/batchesShipped/")
def update_batch_shipped(request: schemas.BatchShippedRequest, db: Session = Depends(get_db)):
    batch_ids = request.batch_ids  
    if not batch_ids:
        raise HTTPException(status_code=400, detail="Batch IDs list is empty")
    batches = crud.update_batch_shipped(db=db, batch_ids=batch_ids)
    if not batches:
        raise HTTPException(status_code=404, detail="No batches found for the given IDs")
    return {"message": "Batches updated successfully"}

# @router.put("/update_batch_shipped/{batch_id}", response_model=schemas.ProcessedLeaves)
# def update_batch_shipped(batch_id: int, db: Session = Depends(get_db)):
#     updated_batch = crud.update_batch_shipped(db, batch_id)
#     if updated_batch is None:
#         raise HTTPException(status_code=404, detail="Batch not found")
#     return updated_batch

@secured_router.delete("/batches/{batch_id}", response_model=schemas.ProcessedLeaves)
def delete_existing_batch(batch_id: int, db: Session = Depends(get_db),user: dict = Depends(centra_user)):
    result = crud.delete_batch(db=db, batch_id=batch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return result

#DRYING
@secured_router.post("/drying-machine/create/")
def add_drying_machine(drying_machine: schemas.DryingMachineCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    new_machine = crud.create_drying_machine(db, drying_machine)
    if new_machine:
        return {"message": "Drying machine created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Drying machine with the same ID already exists!")

@secured_router.post("/drying_machines/{machine_id}/start", response_model=schemas.DryingMachine)
def start_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    success = crud.start_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be started")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@secured_router.post("/drying_machines/{machine_id}/stop", response_model=schemas.DryingMachine)
def stop_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    success = crud.stop_drying_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Machine could not be stopped")
    machine = db.query(models.DryingMachine).filter(models.DryingMachine.MachineID == machine_id).first()
    return machine

@secured_router.get("/drying_machines/{machine_id}/status", response_model=str)
def read_machine_status(machine_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    status = crud.get_drying_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status



# @secured_router.put("/dryingmachine/{machine_id}/status")
# def change_drying_machine_status(machine_id: int, status_update: str, db: Session = Depends(get_db)):
#     return crud.update_drying_machine_status(db, machine_id, status_update.status)

@secured_router.put("/dryingmachines/{machine_id}", response_model=schemas.DryingMachine)
def update_drying_machine(machine_id: int, machine_update: schemas.DryingMachineUpdate, db: Session = Depends(get_db)):
    updated_machine = crud.update_drying_machine(db, machine_id, machine_update)
    if not updated_machine:
        raise HTTPException(status_code=404, detail="Drying Machine not found")
    return updated_machine

@secured_router.put("/dryingmachine/status")
def change_drying_machine_status( status_update: schemas.StatusUpdateRequest, db: Session = Depends(get_db)):
    return crud.update_drying_machine_status(db, machine_id=status_update.machine_id, new_status=status_update.status)


@secured_router.get("/drying_machines/", response_model=List[schemas.DryingMachine])
def read_drying_machines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    try:
        if user["role"] == "Admin":
            # If the user is an admin, fetch all drying machines
            drying_machines = crud.get_all_drying_machines(db=db, skip=skip, limit=limit)
        else:
            # If the user is a Centra user, fetch drying machines specific to their centralID
            centra_id = user["centralID"]
            drying_machines = crud.get_all_drying_machines(db=db, centra_id=centra_id, skip=skip, limit=limit)

        if not drying_machines:
            raise HTTPException(status_code=404, detail="Drying machines not found")

        return drying_machines
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid user data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@secured_router.get("/drying_machines/centra/{centraId}", response_model=List[schemas.DryingMachine])
def read_drying_machines_byCentra(centraId:int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        machines = crud.get_all_drying_machines(db=db, centra_id=centraId, skip=skip, limit=limit)
        return machines
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@secured_router.get("/drying_machine/{machine_id}", response_model=schemas.DryingMachine)
def read_drying_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_drying_machine = crud.delete_drying_machine(db, machine_id)
    if db_drying_machine is None:
        raise HTTPException(status_code=404, detail="Drying machine not found")
    return db_drying_machine

@secured_router.delete("/drying-machine/{machine_id}", response_model=schemas.DryingMachine)
def delete_drying_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_drying_machine = crud.get_drying_machine(db, machine_id)
    if db_drying_machine is None:
        raise HTTPException(status_code=404, detail="Drying machine not found")
    
    db.delete(db_drying_machine)
    db.commit()
    return None

 #drying activity  
@secured_router.post("/drying_activity/create")
def create_drying_activity(drying_activity: schemas.DryingActivityCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    dry_activity = crud.add_new_drying_activity(db, drying_activity,user)
    if dry_activity:
        return {"message": "Drying activity created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Drying activity already exists!")

@secured_router.get("/drying-activities/{drying_id}")
def show_drying_activity(drying_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    drying = crud.get_drying_activity(db, drying_id)
    return drying

@secured_router.get("/drying-activities/machine/{machine_id}")
def show_drying_activity(machine_id: int, db: Session = Depends(get_db)):
    drying = crud.get_drying_activities_by_machine_id(db, machine_id)
    if drying:
        return drying
    else:
        raise HTTPException(status_code=400, detail="Drying activity does not exist")

@secured_router.get("/drying_activity/", response_model=List[schemas.DryingActivity])
def read_drying_activity(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    try:
        if user["role"] == "Admin":
            # If the user is an admin, fetch all drying activities
            drying_activity = crud.get_all_drying_activity(db=db, skip=skip, limit=limit)
        else:
            # If the user is a Centra user, fetch drying activities specific to their centralID
            central_id = user["centralID"]
            drying_activity = crud.get_all_drying_activity(db=db, central_id=central_id, skip=skip, limit=limit)

        if not drying_activity:
            raise HTTPException(status_code=404, detail="Drying activities not found")

        return drying_activity
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid user data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@secured_router.put("/drying-activities/{drying_id}")
def update_drying_activity(drying_id: int, drying_activity: schemas.DryingActivityUpdate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_drying_activity = crud.update_drying_activity(db, drying_id, drying_activity)
    if db_drying_activity is None:
        raise HTTPException(status_code=404, detail="Drying activity not found")
    return db_drying_activity

@secured_router.delete("/drying-activities/{drying_id}")
def delete_drying_activity(drying_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_drying_activity = crud.delete_drying_activity(db, drying_id)
    if db_drying_activity is None:
        raise HTTPException(status_code=404, detail="Drying activity not found")
    return db_drying_activity

#driedleaves
@secured_router.post("/dried_leaves/", response_model=schemas.DriedLeavesBase)
def create_dried_leaf(dried_leaf: schemas.DriedLeavesCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    return crud.create_dried_leaf(db=db, dried_leaf=dried_leaf)

# @secured_router.get("/dried_leaves/", response_model=list[schemas.DriedLeaves])
# def read_dried_leaves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     return crud.get_dried_leaves(db=db, skip=skip, limit=limit)

@secured_router.get("/dried_leaves/", response_model=list[schemas.DriedLeavesBase])
def read_dried_leaves(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(centra_user)  # Ensure only Centra and Admin users can access
):
    try:
        # Check if user is admin to fetch all dried leaves
        if user["role"] == "Admin":
            dried_leaves = crud.get_all_dried_leaves(db=db, skip=skip, limit=limit)
        else:
            central_id = user["centralID"]
            dried_leaves = crud.get_all_dried_leaves(db=db, central_id=central_id, skip=skip, limit=limit)
        
        if not dried_leaves:
            raise HTTPException(status_code=404, detail="Dried leaves not found")
        
        return dried_leaves
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@secured_router.get("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeavesBase)
def read_dried_leaf(leaf_id: int, db: Session = Depends(get_db)):
    db_dried_leaf = crud.get_dried_leaf(db=db, leaf_id=leaf_id)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

@secured_router.put("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeaves)
def update_dried_leaf(leaf_id: int, dried_leaf: schemas.DriedLeavesUpdate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_dried_leaf = crud.update_dried_leaf(db=db, leaf_id=leaf_id, dried_leaf=dried_leaf)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

@secured_router.put("/driedleaves/{dried_leaves_id}/inmachine", response_model=schemas.DriedLeavesBase)
def update_in_machine_status(leaf_id: int, in_machine_status: schemas.DriedLeavesUpdateInMachine, db: Session = Depends(get_db)):
        return crud.update_in_machine_status(db, leaf_id, in_machine_status.in_machine)

@secured_router.delete("/dried_leaves/{leaf_id}", response_model=schemas.DriedLeaves)
def delete_dried_leaf(leaf_id: int, db: Session = Depends(get_db)):
    db_dried_leaf = crud.delete_dried_leaf(db=db, leaf_id=leaf_id)
    if db_dried_leaf is None:
        raise HTTPException(status_code=404, detail="Dried leaf not found")
    return db_dried_leaf

#FLOURING
@secured_router.post("/flouring-machine/create/")
def add_flouring_machine(flouring_machine: schemas.FlouringMachineCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    new_machine = crud.add_new_flouring_machine(db, flouring_machine)
    if new_machine:
        return {"message": "Flouring machine created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Flouring machine with the same ID already exists!")

@secured_router.get("/flouring_machines/{machine_id}/status", response_model=str)
def read_flouring_machine_status(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    status = crud.get_flouring_machine_status(db, machine_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return status



@secured_router.put("/flouringmachine/status", response_model=schemas.FlouringMachine)
def change_flouring_machine_status(
    status_update: schemas.StatusUpdateRequest, 
    db: Session = Depends(get_db)
):
    return crud.update_flouring_machine_status(db, machine_id=status_update.machine_id, new_status=status_update.status)

@secured_router.put("/flouringmachines/{machine_id}", response_model=schemas.FlouringMachineUpdate)
def update_flouring_machine(machine_id: int, machine_update: schemas.FlouringMachineUpdate, db: Session = Depends(get_db)):
    try:
        updated_machine = crud.update_flouring_machine(db, machine_id, machine_update)
        return updated_machine
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@secured_router.get("/flouring_machines/", response_model=List[schemas.FlouringMachine])
def read_flouring_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(centra_user)  # Dependency updated to centra_or_admin_user
):
    try:
        if user["role"] == "Admin":
            # If the user is an admin, fetch all drying machines
            flouring_machine = crud.get_all_flouring_machines(db=db, skip=skip, limit=limit)
        else:
            # If the user is a Centra user, fetch drying machines specific to their centralID
            centra_id = user["centralID"]
            flouring_machine = crud.get_all_flouring_machines(db=db, centra_id=centra_id, skip=skip, limit=limit)

        if not flouring_machine:
            raise HTTPException(status_code=404, detail="Drying machines not found")

        return flouring_machine
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid user data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@secured_router.get("/flouring_machines/centra/{centraId}", response_model=List[schemas.FlouringMachine])   
def get_flouring_machines_byCentra(centraId:int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        flouring_machines = crud.get_all_flouring_machines(db=db, central_id=centraId, skip=skip, limit=limit)

        return flouring_machines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@secured_router.post("/flouring_machines/{machine_id}/start")
def start_flouring_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    success = crud.start_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start the machine or machine already running")
    return {"message": "Machine started successfully"}

@secured_router.post("/flouring_machines/{machine_id}/stop")
def stop_flouring_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    success = crud.stop_flouring_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop the machine or machine already idle")
    return {"message": "Machine stopped successfully"}

@secured_router.delete("/flouring-machine/{machine_id}", response_model=schemas.FlouringMachine)
def delete_flouring_machine(machine_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_flouring_machine = crud.delete_flouring_machine(db, machine_id)
    if db_flouring_machine is None:
        raise HTTPException(status_code=404, detail="Flouring machine not found")
    
    # db.delete(db_flouring_machine)
    # db.commit()
    return {"message": "Flouring machine successfully deleted"}

#flouring activity
@secured_router.post("/flouring_activity/create")
def create_flouring_activity(flouring_activity: schemas.FlouringActivityCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    flour_activity = crud.add_new_flouring_activity(db, flouring_activity)
    if flour_activity:
        return {"message": "Flouring activity created successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Flouring machine with the same ID already exists!")


@secured_router.get("/flouring_activity/", response_model=List[schemas.FlouringActivity])
def read_flouring_activity(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(centra_user)  # Dependency updated to centra_or_admin_user
):
    try:
        if user["role"] == "Admin":
            # If the user is an admin, fetch all flouring activities
            flouring_activity = crud.get_all_flouring_activity(db=db, skip=skip, limit=limit)
        else:
            # If the user is a Centra user, fetch flouring activities specific to their centralID
            central_id = user["centralID"]
            flouring_activity = crud.get_all_flouring_activity(db=db, central_id=central_id, skip=skip, limit=limit)

        if not flouring_activity:
            raise HTTPException(status_code=404, detail="Flouring activities not found")

        return flouring_activity
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid user data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@secured_router.get("/flouring_activity/{flouring_id}", response_model=schemas.FlouringActivity)
def get_flouring_activity(flouring_id: int, db: Session = Depends(get_db)):
    flouring_activity = crud.get_flouring_activity_by_id(db=db, flouring_id=flouring_id)
    if not flouring_activity:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    return flouring_activity


@secured_router.get("/flouring-activities/machine/{machine_id}")
def get_flouring_activity_Machine(machine_id: int, db: Session = Depends(get_db)):
    flouring = crud.get_flouring_activities_by_machine_id(db, machine_id)
    if flouring:
        return flouring
    else:
        raise HTTPException(status_code=400, detail="Drying activity does not exist for this machine")

@secured_router.put("/flouring_activity/update/{flouring_id}", response_model=schemas.FlouringActivity)
def update_flouring_activity(flouring_id: int, flouring_activity: schemas.FlouringActivityUpdate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    updated_flouring = crud.update_flouring_activity(db, flouring_id, flouring_activity)
    if not updated_flouring:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    return updated_flouring

@secured_router.delete("/flouring_activity/delete/{flouring_id}")
def delete_flouring_activity(flouring_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    deleted_flouring_activity = crud.delete_flouring_activity(db=db, flouring_id=flouring_id)
    if not deleted_flouring_activity:
        raise HTTPException(status_code=404, detail="Flouring activity not found")
    
    return {"message": "Flouring activity successfully deleted",}



#WET LEAVES COLLECTIONS
@secured_router.post("/wet-leaves-collections/create")
def create_wet_leaves_collection(wet_leaves_collection: schemas.WetLeavesCollectionCreate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    return crud.add_new_wet_leaves_collection(db, wet_leaves_collection)

@secured_router.get("/wet-leaves-collections/", response_model=List[schemas.WetLeavesCollection])
def read_wet_leaves_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    if user["role"] == "Admin":
        wet_leaves_collections = crud.get_all_wet_leaves_collections(db=db, skip=skip, limit=limit)
    elif user["role"] == "Centra":
        wet_leaves_collections = crud.get_wet_leaves_collections_by_creator(db=db, creator_id=user["centralID"], skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return wet_leaves_collections

secured_router.get("/wet-leaves-totalWeight/", response_model=List[schemas.WetLeavesCollection]) ##for admin/xyz dashboard
def read_wet_leaves_collections( centraId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db) ):
    
    try:
        weights = crud.get_wet_leaves_weight_by_status(db=db, creator_id=centraId)
        return weights
    
    except Exception as e:
        db.rollback()  # Rollback in case of any exception
        raise HTTPException(status_code=500, detail=f"An error occurred during password reset: {str(e)}")

@secured_router.get("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def read_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
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

# @secured_router.put("/wet_leaves-collection/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
# def update_wet_leaves_collection(wet_leaves_batch_id: int, update_data: schemas.WetLeavesCollectionUpdate, db: Session = Depends(get_db)):
#     return crud.update_wet_leaves_collection(db, wet_leaves_batch_id, update_data)

@secured_router.put("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def update_wet_leaves_collection(wet_leaves_batch_id: str, update_data: schemas.WetLeavesCollectionUpdate, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_wet_leaves_collection = crud.update_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id, update_data=update_data)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection
    
@secured_router.delete("/wet-leaves-collections/{wet_leaves_batch_id}", response_model=schemas.WetLeavesCollection)
def delete_wet_leaves_collection(wet_leaves_batch_id: str, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    db_wet_leaves_collection = crud.delete_wet_leaves_collection(db=db, wet_leaves_batch_id=wet_leaves_batch_id)
    if db_wet_leaves_collection is None:
        raise HTTPException(status_code=404, detail="WetLeavesCollection not found")
    return db_wet_leaves_collection

@secured_router.get("/wet-leaves-collections/conversion", response_model= schemas.ConversionRate)
def get_wet_leaves_conversion(centraId: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    try:
        conversion_rate = crud.get_wet_conversion_rate(db=db,centraID=centraId)

        return conversion_rate
    
    except HTTPException as e:
        return { "error": str(e)}
    
@secured_router.get("/dried-leaves/conversion", response_model= schemas.ConversionRate)
def get_dry_leaves_conversion(centraId: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    try:
        conversion_rate = crud.get_dry_conversion_rate(db=db,centraID=centraId)
        return conversion_rate
    
    except HTTPException as e:
        return { "error": str(e)}

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

#pickup by airway
@secured_router.post("/pickups/{airwaybill}", response_model=schemas.Pickup)
def create_pickup(airwaybill: str, pickup: schemas.PickupCreateAirway, db: Session = Depends(get_db)):
    pickup = crud.create_pickup_by_airwaybill(db, airwaybill, pickup)
    if pickup is None:
        raise HTTPException(status_code=404, detail="AirwayBill not found")
    return pickup

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
def update_centra(centra_id: int, centra_update: schemas.CentraUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.update_centra(db, centra_id, centra_update)

@secured_router.delete("/centras/{centra_id}", response_model=dict)
def delete_centra(centra_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.delete_centra(db, centra_id)

#notifications
@secured_router.post("/notifications/", response_model=schemas.Notification)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    return crud.create_notification(db=db, notification=notification)

@secured_router.get("/notifications/{user_id}", response_model=List[schemas.Notification])
def get_notifications(centraid: int, db: Session = Depends(get_db)):
    return crud.get_notifications(db, centraid)

@secured_router.put("/notifications/{notification_id}", response_model=schemas.Notification)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    db_notification = crud.mark_notification_as_read(db, notification_id)
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification

@secured_router.put("/machines/{machine_id}/status", response_model=schemas.Machine)
def update_machine_status(machine_id: int, new_status: str, machine_type: str, db: Session = Depends(get_db)):
    machine = crud.update_machine_status(db, machine_id, new_status, machine_type)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found or invalid machine type")
    return machine

@secured_router.get("/notifications/", response_model=List[schemas.Notification])
def read_notifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notifications = crud.get_all_notifications(db, skip=skip, limit=limit)
    return notifications

#expenotif

@secured_router.get("/expedition_notifications/", response_model=List[schemas.ExpeditionNotification])
def read_all_expedition_notifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notifications = crud.get_all_expnotifications(db, skip=skip, limit=limit)
    return notifications

@secured_router.get("/expedition_notifications/", response_model=List[schemas.ExpeditionNotification])
def read_expedition_notifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notifications = crud.get_expedition_notifications(db, skip=skip, limit=limit)
    return notifications
#userCentra

@secured_router.get("/usercentra/", response_model=List[schemas.UserCentraWithUser])
def read_user_centra_name_email(db: Session = Depends(get_db)):
    user_centra = crud.get_all_user_centra_with_user(db)
    if not user_centra:
        raise HTTPException(status_code=404, detail="UserCentra not found")
    return user_centra

# @secured_router.get("/usercentra/", response_model=List[schemas.UserCentra])
# def read_user_centra(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     user_centra = crud.get_user_centra(db=db, skip=skip, limit=limit)
#     return user_centra

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

# @secured_router.get("wet")

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
@secured_router.post("/harborguard", response_model=schemas.HarborGuardInDB)
def create_harbor_guard(harbor_guard: schemas.HarborGuardCreate, db: Session = Depends(get_db), user: dict = Depends(harbour_user)):
    return crud.create_harbor_guard(db, harbor_guard)

@secured_router.get("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def read_harbor_guard(harbour_id: int, db: Session = Depends(get_db), user: dict = Depends(harbour_user)):
    db_harbor_guard = crud.get_harbor_guard(db, harbour_id)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.put("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def update_harbor_guard(harbour_id: int, harbor_guard: schemas.HarborGuardUpdate, db: Session = Depends(get_db), user: dict = Depends(harbour_user)):
    db_harbor_guard = crud.update_harbor_guard(db, harbour_id, harbor_guard)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.delete("/harborguard/{harbour_id}", response_model=schemas.HarborGuardInDB)
def delete_harbor_guard(harbour_id: int, db: Session = Depends(get_db), user: dict = Depends(harbour_user)):
    db_harbor_guard = crud.delete_harbor_guard(db, harbour_id)
    if db_harbor_guard is None:
        raise HTTPException(status_code=404, detail="Harbor Guard not found")
    return db_harbor_guard

@secured_router.get("/harborguard", response_model=list[schemas.HarborGuardInDB])
def read_harbor_guards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(harbour_user)):
    harbor_guards = crud.get_all_harbor_guards(db, skip=skip, limit=limit)
    return harbor_guards

# Warehouses
@secured_router.get("/warehouses", response_model=List[schemas.Warehouse])
async def show_all_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    warehouses = crud.get_all_warehouses(db, skip=skip, limit=limit)
    return warehouses

# @secured_router.get("/warehouses/", response_model=List[schemas.Warehouse])
# def read_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     warehouses = crud.get_all_warehouses(db, skip=skip, limit=limit)
#     return warehouses

@secured_router.get("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    warehouse = crud.get_warehouse(db, warehouse_id=warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

@secured_router.post("/warehouses", response_model=schemas.Warehouse)
async def create_warehouse(warehouse_data: schemas.WarehouseCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud.create_warehouse(db=db, warehouse_data=warehouse_data)

@secured_router.put("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
async def update_warehouse(warehouse_id: int, warehouse_data: schemas.WarehouseUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
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

@secured_router.put("/warehouses/{warehouse_id}/stock/")
def update_stock(warehouse_id: int, new_stock: int, db: Session = Depends(get_db)):
    try:
        warehouse = crud.update_warehouse_stock(db, warehouse_id, new_stock)
        return warehouse
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@secured_router.get("/warehouses/{warehouse_id}/stock_history/")
def get_stock_history(warehouse_id: int, db: Session = Depends(get_db)):
    history = crud.get_warehouse_stock_history(db, warehouse_id)
    if not history:
        raise HTTPException(status_code=404, detail="Warehouse not found or no stock history available")
    return history

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


#expedition

@secured_router.post("/expeditions/") # belum bener harus di kerjain
def create_expedition(expedition: schemas.ExpeditionCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        expedition = crud.create_expedition(db, expedition,user)
        return {"expeditionId": expedition.ExpeditionID}
    except HTTPException as e:
        return {"error": str(e)}

# @secured_router.get("/all_expeditions/", response_model=List[schemas.Expedition])
# def read_expeditions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     expeditions = crud.get_all_expeditions_with_batches(db=db, skip=skip, limit=limit)
#     return expeditions

# @secured_router.get("/all_expeditions/", response_model=List[schemas.Expedition])
# def read_expeditions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     expeditions = crud.get_all_expeditions_with_batches(db=db, skip=skip, limit=limit)
#     return expeditions

# @secured_router.get("/all_expeditions/{centraId}", response_model=List[schemas.Expedition])
# def read_expeditions(centraId :int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     expeditions = crud.get_all_expeditions_with_batches_by_centra(db=db,centra_id=centraId,skip=skip,limit=limit)
#     return expeditions


# @secured_router.get("/expeditions", response_model=List[schemas.Expedition])
# def get_expeditions(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Expedition).offset(skip).limit(limit).all()

@secured_router.get("/expeditions_by_centra/{centra_id}", response_model=List[schemas.ExpeditionWithBatches])
def get_expeditions_by_centra(centra_id: int,skip:int = 0, limit:int = 100, db: Session = Depends(get_db)):
    expeditions = crud.get_expeditions_with_batches_by_centra(db=db,centra_id=centra_id, skip=skip, limit=limit)
    return expeditions

@secured_router.get("/all_expeditions", response_model=List[schemas.ExpeditionWithBatches])
def get_all_expedition_with_batches( skip:int = 0, limit:int = 100, db: Session = Depends(get_db)):
    all = crud.get_all_expedition_with_batches(db=db,skip=skip,limit=limit)
    return all

@secured_router.get("/expedition/{expedition_id}", response_model=List[schemas.ExpeditionWithBatches])
def get_expedition_with_batches(expedition_id: int, db: Session = Depends(get_db)):
    expeditions_with_batches = crud.get_expedition_with_batches(db, expedition_id)
    if not expeditions_with_batches:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return expeditions_with_batches


@secured_router.get("/expedition/airwaybill/{airwaybill}", response_model=schemas.ExpeditionWithBatches)
def read_expedition_by_airwaybill(airwaybill: str, db: Session = Depends(get_db)):
    expedition_data = crud.get_expedition_with_batches_by_airwaybill(db=db,airwaybill=airwaybill)
    if not expedition_data:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return expedition_data

@secured_router.put("/expedition/warehouse/{airway_bill}", response_model=schemas.Expedition)
def update_warehouse_id_for_expedition(airway_bill: str, warehouse_id_update: schemas.WarehouseIDUpdate, db: Session = Depends(get_db)
):
    updated_expedition = crud.update_warehouse_id_by_airway_bill(db, airway_bill, warehouse_id_update.warehouse_id)
    
    if not updated_expedition:
        raise HTTPException(status_code=404, detail=f"Expedition with AirwayBill {airway_bill} not found")
    
    return updated_expedition
    
# @secured_router.get("/expeditions", response_model=List[schemas.Expedition])
# def get_expeditions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     expeditions = crud.get_expeditions(db, skip=skip, limit=limit)
#     return expeditions


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

@secured_router.put("/expedition/{awb}/status")
def change_expedition_status(status_update: schemas.StatusUpdate, db: Session = Depends(get_db)):
    return crud.update_expedition_status(db, status_update.awb, status_update.status)

@secured_router.delete("/expeditions/{expedition_id}")
def delete_expedition(expedition_id: int, db: Session = Depends(get_db)):
    db_expedition = crud.delete_expedition(db, expedition_id)
    if db_expedition is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return db_expedition

# @secured_router.put("/expeditions/{expedition_id}/change_status")
# def change_expedition_status_route(expedition_id: int, new_status: str, db: Session = Depends(get_db)):
#     expedition = crud.change_expedition_status(db, expedition_id, new_status)
#     if expedition is None:
#         raise HTTPException(status_code=404, detail=f"Expedition with id {expedition_id} not found")
#     return {"message": f"Status of Expedition {expedition_id} changed to {new_status}"}


# @secured_router.put("/expeditions/{expedition_id}/confirm", response_model=schemas.Expedition)
# def confirm_expedition_route(expedition_id: int, TotalWeight: int, db: Session = Depends(get_db)):
#     expedition = crud.confirm_expedition(db, expedition_id, TotalWeight)
#     if expedition is None:
#         raise HTTPException(status_code=404, detail="Expedition not found")
#     return expedition

#expeditioncontent
# class ExpeditionContentBase(BaseModel):
#     ExpeditionID: int
#     BatchID: int
#     # checkpointID: int


# @secured_router.post("/expedition_contents/", response_model=schemas.ExpeditionContent)
# def create_expedition_contents(expedition_contents: List[schemas.ExpeditionContentCreate], db: Session = Depends(get_db)):
#     created_contents = []
#     for content in expedition_contents:
#         created_content = crud.create_expedition_content(db=db, expedition_content=content)
#         created_contents.append(created_content)
#     return created_contents

@secured_router.post("/expedition_contents/", response_model=List[schemas.ExpeditionContent])
def create_expedition_contents(expedition_content: schemas.ExpeditionContentCreate, db: Session = Depends(get_db)):
    created_contents = []
    expedition_id = expedition_content.ExpeditionID
    for batch_id in expedition_content.BatchIDs:
        content_data = models.ExpeditionContent(ExpeditionID=expedition_id, BatchID=batch_id)
        created_content = crud.create_expedition_content(db=db, expedition_content=content_data)
        created_contents.append(created_content)
    return created_contents


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

#checkpointstatus
@secured_router.post("/checkpointstatus/", response_model=schemas.CheckpointStatus)
def create_checkpoint(checkpoint_status: schemas.CheckpointStatusCreate, db: Session = Depends(get_db)):
    return crud.create_checkpoint_status(db, checkpoint_status)

@secured_router.post("/checkpoint_statuses/", response_model=schemas.CheckpointStatus)
def create_checkpoint_status(airwaybill: str, checkpoint_status_data: schemas.CheckpointStatusCreateAirway, db: Session = Depends(get_db)):
    checkpoint_status = crud.create_checkpoint_status_by_airwaybill(db, airwaybill, checkpoint_status_data)
    if checkpoint_status is None:
        raise HTTPException(status_code=404, detail="Expedition not found")
    return checkpoint_status

@secured_router.get("/checkpointstatus/{checkpoint_id}", response_model=schemas.CheckpointStatus)
def read_checkpoint(checkpoint_id: int, db: Session = Depends(get_db)):
    db_checkpoint = crud.get_checkpoint_status(db, checkpoint_id)
    if db_checkpoint is None:
        raise HTTPException(status_code=404, detail="Checkpoint status not found")
    return db_checkpoint

@secured_router.get("/checkpointstatus/airwaybill/{awb}")
def getAllCheckpoint_byAWB(awb:str, db:Session = Depends(get_db)):
    checkpoints = crud.get_checkpoints_statuses_by_airwaybill(db=db,airwaybill=awb)

    if checkpoints is None:
        raise HTTPException(status_code=404, detail="Checkpoint status not found")
    return checkpoints

@secured_router.get("/checkpointstatus/", response_model=List[schemas.CheckpointStatus])
def read_all_checkpoints(db: Session = Depends(get_db)):
    return crud.get_all_checkpoint_statuses(db=db)

@secured_router.put("/checkpointstatus/{checkpoint_id}", response_model=schemas.CheckpointStatus)
def update_checkpoint(checkpoint_id: int, checkpoint_status: schemas.CheckpointStatusCreate, db: Session = Depends(get_db)):
    db_checkpoint = crud.update_checkpoint_status(db, checkpoint_id, checkpoint_status)
    if db_checkpoint is None:
        raise HTTPException(status_code=404, detail="Checkpoint status not found")
    return db_checkpoint

@secured_router.delete("/checkpointstatus/{checkpoint_id}", response_model=schemas.CheckpointStatus)
def delete_checkpoint(checkpoint_id: int, db: Session = Depends(get_db)):
    db_checkpoint = crud.delete_checkpoint_status(db, checkpoint_id)
    if db_checkpoint is None:
        raise HTTPException(status_code=404, detail="Checkpoint status not found")
    return db_checkpoint


#received package
# @secured_router.post("/received_packages/", response_model=schemas.ReceivedPackage)
# def create_received_package(received_package: schemas.ReceivedPackageCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     return crud.create_received_package(db=db, received_package=received_package)

# @secured_router.get("/received_packages/", response_model=List[schemas.ReceivedPackage])
# def read_received_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     received_packages = crud.get_received_packages(db=db, skip=skip, limit=limit)
#     return received_packages

# @secured_router.get("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
# def read_received_package(package_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     received_package = crud.get_received_package(db=db, package_id=package_id)
#     if received_package is None:
#         raise HTTPException(status_code=404, detail="Received package not found")
#     return received_package

# @secured_router.put("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
# def update_received_package(package_id: int, received_package: schemas.ReceivedPackageUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     db_received_package = crud.update_received_package(db=db, package_id=package_id, received_package=received_package)
#     if db_received_package is None:
#         raise HTTPException(status_code=404, detail="Received package not found")
#     return db_received_package

# @secured_router.delete("/received_packages/{package_id}", response_model=schemas.ReceivedPackage)
# def delete_received_package(package_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
#     db_received_package = crud.delete_received_package(db=db, package_id=package_id)
#     if db_received_package is None:
#         raise HTTPException(status_code=404, detail="Received package not found")
#     return db_received_package

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

@secured_router.delete("/package_receipts/{receipt_id}")
def delete_package_receipt(receipt_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_package_receipt = crud.delete_package_receipt(db, receipt_id)
    if db_package_receipt is None:
        raise HTTPException(status_code=404, detail="Package receipt not found")
    return db_package_receipt

# @secured_router.delete("/package_receipts/{expedition_id}")
# def delete_package_receipt(expedition_id: int, db: Session = Depends(get_db)):
#     package_receipt = crud.delete_package_receipt_by_expeditionid(db, expedition_id)
#     if package_receipt is None:
#         raise HTTPException(status_code=404, detail="Package receipt not found")
#     return package_receipt

# @secured_router.get("/package_receipts/expedition/{expedition_id}", response_model=List[schemas.PackageReceipt])
# def get_package_receipts(expedition_id: int, db: Session = Depends(get_db)):
#     package_receipts = crud.get_package_receipts_by_expeditionid(db, expedition_id)
#     if not package_receipts:
#         raise HTTPException(status_code=404, detail="No package receipts found for the given ExpeditionID")
#     return package_receipts

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
def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db), user: dict = Depends(admin_user)):
    db_user = crud.create_user(db=db, user=new_user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        SMTP.send_setPassEmail(db_user,db)
        return db_user

@secured_router.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, sort_by: str = Query('Name'), sort_order: str = Query('asc'), role: str = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(admin_user)):
    return crud.get_all_users(db=db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, role=role)

@secured_router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(admin_user)):
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@secured_router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, update_data: schemas.UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(admin_user)):
    db_user = crud.update_user(db=db, user_id=user_id, update_data=update_data)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@secured_router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(admin_user)):
    db_user = crud.delete_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Leaves (Combined API)
@secured_router.get("/leaves", response_model=schemas.LeavesStatus)
def get_leaves_status(centra_id: int, db: Session = Depends(get_db), user: dict = Depends(centra_user)):
    leaves_summary = crud.get_leaves_summary(db, centra_id)
    return leaves_summary

@secured_router.get("/conversion_rates/{centra_id}", response_model=schemas.ConversionRateResponse)
def get_conversion_rates(centra_id: int, db: Session = Depends(get_db)):
    conversion_rate = crud.calculate_conversion_rates(db, centra_id)
    return conversion_rate