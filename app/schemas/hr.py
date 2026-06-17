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
    approved_by: Optional[int] = None

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


# ── Contract ───────────────────────────────────────────
class ContractCreate(BaseModel):
    employee_id:   int
    contract_type: str
    start_date:    date
    end_date:      Optional[date] = None
    salary:        float
    position:      str
    department:    str
    notes:         Optional[str] = None

class ContractUpdate(BaseModel):
    contract_type: Optional[str] = None
    end_date:      Optional[date] = None
    salary:        Optional[float] = None
    position:      Optional[str] = None
    department:    Optional[str] = None
    status:        Optional[str] = None
    notes:         Optional[str] = None

class ContractOut(BaseModel):
    id:            int
    employee_id:   int
    contract_type: str
    start_date:    date
    end_date:      Optional[date]
    salary:        float
    position:      str
    department:    str
    status:        str
    notes:         Optional[str]
    created_by:    int
    created_at:    datetime

    class Config:
        from_attributes = True


# ── Performance Review ─────────────────────────────────
class PerformanceCreate(BaseModel):
    employee_id:      int
    period:           str
    rating:           float
    kpi_score:        Optional[float] = 0.0
    attendance_score: Optional[float] = 0.0
    teamwork_score:   Optional[float] = 0.0
    technical_score:  Optional[float] = 0.0
    comments:         Optional[str] = None
    goals:            Optional[str] = None

class PerformanceUpdate(BaseModel):
    rating:           Optional[float] = None
    kpi_score:        Optional[float] = None
    attendance_score: Optional[float] = None
    teamwork_score:   Optional[float] = None
    technical_score:  Optional[float] = None
    comments:         Optional[str] = None
    goals:            Optional[str] = None
    status:           Optional[str] = None

class PerformanceOut(BaseModel):
    id:               int
    employee_id:      int
    reviewer_id:      int
    period:           str
    rating:           float
    kpi_score:        float
    attendance_score: float
    teamwork_score:   float
    technical_score:  float
    comments:         Optional[str]
    goals:            Optional[str]
    status:           str
    created_at:       datetime

    class Config:
        from_attributes = True