from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class LeaveCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date:   date
    days:       int
    reason:     Optional[str] = None

class LeaveUpdate(BaseModel):
    status:      str  # approved | rejected
    approved_by: int

class LeaveOut(BaseModel):
    id:          int
    employee_id: int
    leave_type:  str
    start_date:  date
    end_date:    date
    days:        int
    reason:      Optional[str]
    status:      str
    approved_by: Optional[int]
    created_at:  datetime

    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    employee_id: int
    date:        date
    check_in:    Optional[datetime] = None
    check_out:   Optional[datetime] = None
    status:      Optional[str] = "present"

class AttendanceOut(BaseModel):
    id:          int
    employee_id: int
    date:        date
    check_in:    Optional[datetime]
    check_out:   Optional[datetime]
    status:      str
    created_at:  datetime

    class Config:
        from_attributes = True


class PayrollCreate(BaseModel):
    employee_id: int
    month:       str
    basic_salary: float
    allowances:  Optional[float] = 0.0
    deductions:  Optional[float] = 0.0

class PayrollOut(BaseModel):
    id:           int
    employee_id:  int
    month:        str
    basic_salary: float
    allowances:   float
    deductions:   float
    net_salary:   float
    status:       str
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True