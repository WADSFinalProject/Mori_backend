from typing import Optional
from pydantic import BaseModel

# User schemas
class UserBase(BaseModel):
    IDORole: int
    Email: str
    FullName: str
    Role: str

class UserCreate(UserBase):
    pass #ini harusnya ada password  

class UserSetPassword(BaseModel):
    Password: str

class UserUpdate(BaseModel):
    IDORole: Optional[str] = None
    Password: Optional[str] = None
    Email: Optional[str] = None
    FullName: Optional[str] = None
    Role: Optional[str] = None

class User(UserBase):
    UserID: int

    class Config:
        orm_mode = True

# ProcessedLeaves schemas
class ProcessedLeavesBase(BaseModel):
    Description: str
    FlouringID: str
    DryingID: str

class ProcessedLeavesCreate(ProcessedLeavesBase):
    pass

class ProcessedLeavesUpdate(BaseModel):
    Description: Optional[str] = None
    FlouringID: Optional[str] = None
    DryingID: Optional[str] = None

class ProcessedLeaves(ProcessedLeavesBase):
    ProductID: int

    class Config:
        orm_mode = True

# WetLeavesCollection schemas
class WetLeavesCollectionBase(BaseModel):
    UserID: int
    CentralID: int
    Date: str
    Time: str
    Weight: int
    Expired: bool
    ExpirationTime: str

class WetLeavesCollectionCreate(WetLeavesCollectionBase):
    pass

class WetLeavesCollectionUpdate(BaseModel):
    UserID: Optional[int] = None
    CentralID: Optional[int] = None
    Date: Optional[str] = None
    Time: Optional[str] = None
    Weight: Optional[int] = None
    Expired: Optional[bool] = None
    ExpirationTime: Optional[str] = None

class WetLeavesCollection(WetLeavesCollectionBase):
    WetLeavesBatchID: str

    class Config:
        orm_mode = True

# DryingMachine schemas
class DryingMachineBase(BaseModel):
    Capacity: str

class DryingMachineCreate(DryingMachineBase):
    pass

class DryingMachineUpdate(BaseModel):
    Capacity: Optional[str] = None

class DryingMachine(DryingMachineBase):
    MachineID: str

    class Config:
        orm_mode = True

# DryingActivity schemas
class DryingActivityBase(BaseModel):
    UserID: int
    CentralID: int
    Date: str
    Weight: int
    DryingMachineID: str
    Time: str

class DryingActivityCreate(DryingActivityBase):
    pass

class DryingActivityUpdate(BaseModel):
    UserID: Optional[int] = None
    CentralID: Optional[int] = None
    Date: Optional[str] = None
    Weight: Optional[int] = None
    DryingMachineID: Optional[str] = None
    Time: Optional[str] = None

class DryingActivity(DryingActivityBase):
    DryingID: str

    class Config:
        orm_mode = True

# FlouringMachine schemas
class FlouringMachineBase(BaseModel):
    Capacity: str

class FlouringMachineCreate(FlouringMachineBase):
    pass

class FlouringMachineUpdate(BaseModel):
    Capacity: Optional[str] = None

class FlouringMachine(FlouringMachineBase):
    MachineID: str

    class Config:
        orm_mode = True

# FlouringActivity schemas
class FlouringActivityBase(BaseModel):
    UserID: int
    CentralID: int
    Date: str
    Weight: int
    FlouringMachineID: str
    DryingID: str

class FlouringActivityCreate(FlouringActivityBase):
    pass

class FlouringActivityUpdate(BaseModel):
    UserID: Optional[int] = None
    CentralID: Optional[int] = None
    Date: Optional[str] = None
    Weight: Optional[int] = None
    FlouringMachineID: Optional[str] = None
    DryingID: Optional[str] = None

class FlouringActivity(FlouringActivityBase):
    FlouringID: str

    class Config:
        orm_mode = True

# Centra schemas
class CentraBase(BaseModel):
    Address: str

class CentraCreate(CentraBase):
    pass

class CentraUpdate(BaseModel):
    Address: Optional[str] = None

class Centra(CentraBase):
    CentralID: int

    class Config:
        orm_mode = True

# Expedition schemas
class ExpeditionBase(BaseModel):
    EstimatedArrival: str
    TotalPackages: int
    ExpeditionDate: str
    ExpeditionServiceDetails: str
    Destination: str
    CentralID: int

class ExpeditionCreate(ExpeditionBase):
    pass

class ExpeditionUpdate(BaseModel):
    EstimatedArrival: Optional[str] = None
    TotalPackages: Optional[int] = None
    ExpeditionDate: Optional[str] = None
    ExpeditionServiceDetails: Optional[str] = None
    Destination: Optional[str] = None
    CentralID: Optional[int] = None

class Expedition(ExpeditionBase):
    ExpeditionID: int

    class Config:
        orm_mode = True

# ReceivedPackage schemas
class ReceivedPackageBase(BaseModel):
    ExpeditionID: int
    UserID: int
    PackageType: str
    ReceivedDate: str
    WarehouseDestination: str

class ReceivedPackageCreate(ReceivedPackageBase):
    pass

class ReceivedPackageUpdate(BaseModel):
    ExpeditionID: Optional[int] = None
    UserID: Optional[int] = None
    PackageType: Optional[str] = None
    ReceivedDate: Optional[str] = None
    WarehouseDestination: Optional[str] = None

class ReceivedPackage(ReceivedPackageBase):
    PackageID: int

    class Config:
        orm_mode = True

# PackageReceipt schemas
class PackageReceiptBase(BaseModel):
    UserID: int
    PackageID: int
    TotalWeight: int
    TimeAccepted: str
    Note: str
    Date: str

class PackageReceiptCreate(PackageReceiptBase):
    pass

class PackageReceiptUpdate(BaseModel):
    UserID: Optional[int] = None
    PackageID: Optional[int] = None
    TotalWeight: Optional[int] = None
    TimeAccepted: Optional[str] = None
    Note: Optional[str] = None
    Date: Optional[str] = None

class PackageReceipt(PackageReceiptBase):
    ReceiptID: int

    class Config:
        orm_mode = True

# ProductReceipt schemas
class ProductReceiptBase(BaseModel):
    ProductID: str
    ReceiptID: int
    RescaledWeight: int

class ProductReceiptCreate(ProductReceiptBase):
    pass

class ProductReceiptUpdate(BaseModel):
    ProductID: Optional[str] = None
    ReceiptID: Optional[int] = None
    RescaledWeight: Optional[int] = None

class ProductReceipt(ProductReceiptBase):
    ProductReceiptID: int

    class Config:
        orm_mode = True

# PackageType schemas
class PackageTypeBase(BaseModel):
    Description: str

class PackageTypeCreate(PackageTypeBase):
    pass

class PackageTypeUpdate(BaseModel):
    Description: Optional[str] = None

class PackageType(PackageTypeBase):
    PackageTypeID: int

    class Config:
        orm_mode = True
