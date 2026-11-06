from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class TaskExportRequest(BaseModel):
    report_type: str  # SALES, INVENTORY, ORDERS, PERFORMANCE
    export_format: str = "CSV"  # CSV, EXCEL, PDF
    parameters: Optional[Dict[str, Any]] = None


class ScheduleSummaryRequest(BaseModel):
    summary_type: str = "DAILY_INVENTORY_ORDERS"
    parameters: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_name: str
    task_type: str
    status: str
    export_format: Optional[str] = None
    file_path: Optional[str] = None
    payload: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    created_by_user_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

