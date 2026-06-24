from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class EmployeeCreate(BaseModel):
    first_name:  str
    last_name:   str
    phone:       Optional[str]  = None
    department:  str
    designation: str
    salary:      float
    join_date:   date
    manager_id:  Optional[int]  = None

class EmployeeUpdate(BaseModel):
    first_name:  Optional[str]   = None
    last_name:   Optional[str]   = None
    phone:       Optional[str]   = None
    department:  Optional[str]   = None
    designation: Optional[str]   = None
    salary:      Optional[float] = None
    manager_id:  Optional[int]   = None

class EmployeeOut(BaseModel):
    id:          int
    user_id:     int
    first_name:  str
    last_name:   str
    phone:       Optional[str]
    department:  str
    designation: str
    salary:      float
    join_date:   Optional[date]
    manager_id:  Optional[int]
    class Config:
        from_attributes = True

class OrgNode(BaseModel):
    id:             int
    user_id:        int
    full_name:      str
    designation:    str
    department:     str
    manager_id:     Optional[int]
    direct_reports: List["OrgNode"] = []
    class Config:
        from_attributes = True

OrgNode.model_rebuild()