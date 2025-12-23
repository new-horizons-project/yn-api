from typing import Optional
from datetime import datetime

from pydantic import BaseModel

class Task(BaseModel):
	id             : int
	pretty_name    : str
	interval       : int
	enabled        : bool
	last_execution : Optional[datetime]

	class Config:
		from_attributes = True