from pydantic import BaseModel
from typing import Optional
from datetime import date

class EmployeeCreate(BaseModel):
    first_name:  str
    last_name:   str
    phone:       Optional[str] = None
    department:  str
    designation: str
    salary:      float
    join_date:   date

class EmployeeUpdate(BaseModel):
    first_name:  Optional[str] = None
    last_name:   Optional[str] = None
    phone:       Optional[str] = None
    department:  Optional[str] = None
    designation: Optional[str] = None
    salary:      Optional[float] = None

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

    class Config:
        from_attributes = True