from pydantic import BaseModel

from ..db.enums import AP_type


class ApplicationParameterValue(BaseModel):
	value: str
	value_type: AP_type
