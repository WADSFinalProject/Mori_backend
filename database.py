import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session


# Correct database URL with 'postgresql' dialect
SQLALCHEMY_DATABASE_URL = "postgresql://default:RO4jlz3FguJt@ep-lingering-forest-a1hakwzf.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models
Base = declarative_base()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Ensure your get_db is correctly defined as shown above
def insert_data(db):
    sql = """
    DO $$ 
    DECLARE 
        _user_id INTEGER;
        _centra_id INTEGER;
        _product_id INTEGER;
        _drying_machine_id INTEGER;
        _drying_activity_id INTEGER;
        _flouring_machine_id INTEGER;
        _flouring_activity_id INTEGER;
        _expedition_id INTEGER;
        _receipt_id INTEGER;
        _warehouse_id INTEGER;
        _pickup_id INTEGER;
    BEGIN


      --- Insert "Centra"
    INSERT INTO "Centra" ("Address", "FlouringSchedule") 
    VALUES ('Centra Address', 'Flouring Schedule')
    RETURNING "CentralID" INTO _centra_id;

    
      --- Insert warehouse
    INSERT INTO "warehouses" ("email", "phone", "location", "created_at", "TotalStock")
    VALUES ('warehouse@example.com', '1234567890', 'Warehouse Location', '2024-06-17', 100)
    RETURNING "id" INTO _warehouse_id;

    -- Insert DryingMachine
    INSERT INTO "DryingMachine" ("CentraID", "Capacity", "Duration", "Status") 
    VALUES (_centra_id, '100kg', INTERVAL '2 hours', 'idle')
    RETURNING "MachineID" INTO _drying_machine_id;

    -- Insert DryingActivity
    INSERT INTO "DryingActivity" ("CentralID", "Weight", "DryingMachineID", "Time") 
    VALUES (_centra_id, 100, _drying_machine_id, '12:00:00')
    RETURNING "DryingID" INTO _drying_activity_id;

    -- Insert FlouringMachine
    INSERT INTO "FlouringMachine" ("CentraID", "Capacity", "Duration", "Status") 
    VALUES (_centra_id, '100kg', INTERVAL '2 hours', 'idle')
    RETURNING "MachineID" INTO _flouring_machine_id;

    -- Insert FlouringActivity
    INSERT INTO "FlouringActivity" ("CentralID", "Date", "Weight", "FlouringMachineID", "DryingID", "Time") 
    VALUES (_centra_id, '2024-06-18', 100, _flouring_machine_id, _drying_activity_id, '12:00:00')
    RETURNING "FlouringID" INTO _flouring_activity_id;

    -- Insert DriedLeaves
    INSERT INTO "DriedLeaves" ("CentraID", "Weight", "DriedDate", "Floured") 
    VALUES (_centra_id, 100, '2024-06-17', FALSE);

    -- Insert ProcessedLeaves
    INSERT INTO "ProcessedLeaves" ("CentraID", "Weight", "FlouringID", "DryingID", "DriedDate", "FlouredDate", "Shipped") 
    VALUES (_centra_id, 100, _flouring_activity_id, _drying_activity_id, '2024-06-17', '2024-06-18', FALSE)
    RETURNING "ProductID" INTO _product_id;

    -- Insert WetLeavesCollection
    INSERT INTO "WetLeavesCollection" ("CentralID", "Date", "Time", "Weight", "Status") 
    VALUES (_centra_id, '2024-06-17', '12:00:00', 100, 'Fresh');

    -- Insert Expedition
    INSERT INTO "Expedition" ("AirwayBill", "EstimatedArrival", "TotalPackages", "TotalWeight", "Status", "ExpeditionDate", "ExpeditionServiceDetails", "Destination", "CentralID") 
    VALUES ('AB123456789', '2024-07-01 10:00:00', 1, 100, 'PKG_Delivering', '2024-06-17 09:00:00', 'Service Details', 'Destination Address', _centra_id)        
    RETURNING "ExpeditionID" INTO _expedition_id;

    -- Insert ExpeditionContent
    INSERT INTO "ExpeditionContent" ("ExpeditionID", "BatchID") 
    VALUES (_expedition_id, _product_id);

    -- Insert heckpointStatus
    INSERT INTO "checkpointstatus" ("expeditionid", "status", "statusdate") 
    VALUES (_expedition_id, 'Checkpoint Status', '2024-06-17 09:00:00');

    -- Insert Pickup
    INSERT INTO "pickup" ("xyzID", "expeditionID", "warehouseid", "pickup_time") 
    VALUES (1, _expedition_id, _warehouse_id, '12:00:00')
    RETURNING "id" INTO _pickup_id;

    -- Insert PackageReceipt
    INSERT INTO "PackageReceipt" ("XYZuser", "PickupID", TotalWeight", "TimeAccepted", "Note", "Date") 
    VALUES (_user_id, _pickup_id, 100, '2024-06-17 09:00:00', 'Note', '2024-06-17 09:00:00')
    RETURNING "ReceiptID" INTO _receipt_id;

    -- Insert ProductReceipt
    INSERT INTO "ProductReceipt" ("ProductID", "ReceiptID", "RescaledWeight") 
    VALUES (_product_id, _receipt_id, 100);




    END $$;
    """
    db.execute(text(sql))
    db.commit()

# Handling the session manually
with get_db() as db:
    insert_data(db)