from pydantic import BaseModel
from typing import Optional

class RuleCreate(BaseModel):
    sensor_name: str
    metric_name: str
    operator: str
    threshold: float
    actuator_name: str
    action_value: str
    enabled: bool = True

class RuleUpdate(BaseModel):
    sensor_name: Optional[str] = None
    metric_name: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    actuator_name: Optional[str] = None
    action_value: Optional[str] = None
    enabled: Optional[bool] = None

class ActuatorCommand(BaseModel):
    state: str