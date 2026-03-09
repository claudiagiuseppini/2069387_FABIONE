from dataclasses import dataclass
from typing import Optional

@dataclass
class Metric:
    sensor_id: str
    sensor_type: str        
    values: dict            # {'temperature_c': 24.8, ...}
    units: dict             # {'temperature_c': 'C', ...}
    timestamp: str          
    source: Optional[str]   
    status: str