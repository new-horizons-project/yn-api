from os import path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import uuid
import json

from urllib.parse import urlparse

from ..db import enums


APPLICATION_PARAMETERS_JSON = path.join(path.dirname(__file__), 
							  "..", "application_parameters.json")


@dataclass
class ApplicationParameterDC:
	name: str
	kind: enums.AP_kind
	default_value: Optional[str]
	type: enums.AP_type
	visibility: enums.AP_visibility


def validate_data(data: str, data_type: enums.AP_type):
	try:
		match data_type:
			case enums.AP_type.string:
				return True
			case enums.AP_type.bool:
				return data in ("0", "1")
			case enums.AP_type.integer:
				int(data)
			case enums.AP_type.float:
				float(data)
			case enums.AP_type.json:
				try:
					json.loads(data)
				except json.JSONDecodeError:
					return False
			case enums.AP_type.datetime:
				datetime.fromisoformat(data)
			case enums.AP_type.uuid:
				uuid.UUID(data)
			case enums.AP_type.url:
				parsed = urlparse(data)
				return parsed.scheme in ("http", "https") and parsed.netloc
			case _:
				return False
	except ValueError:
		return False
	
	return True


def parse_parameters(data: dict, path: str = "") -> List[ApplicationParameterDC]:
	params: List[ApplicationParameterDC] = []
	
	for key, value in data.items():
		current_path = f"{path}.{key}" if path else key

		if isinstance(value, dict) and not value.get("parameter") == 1:
			params.extend(parse_parameters(value, current_path))
			continue

		if not isinstance(value, dict):
			raise ValueError("Unable to parse AP json")
		
		ap_kind         = value.get("kind")
		ap_type         = value.get("type")
		ap_visibility   = value.get("visibility")
		ap_def          = value.get("default_value")

		if None in [ap_kind, ap_type, ap_visibility, ap_def]:
			raise ValueError(f"Incomplete AP {current_path}")

		if ap_type not in enums.AP_type._value2member_map_:
			raise ValueError("Unknown AP type")
		
		if ap_kind not in enums.AP_kind._value2member_map_:
			raise ValueError("Unknown AP kind")
		
		if ap_visibility not in enums.AP_visibility._value2member_map_:
			raise ValueError("Unknown AP visibility value")

		params.append(ApplicationParameterDC(
			name=current_path,
			kind             = ap_kind,
			type             = ap_type,
			default_value    = None if ap_def == "" else ap_def,
			visibility       = ap_visibility
		))
			
	return params


def get_application_parameters() -> List[ApplicationParameterDC]:
	with open(APPLICATION_PARAMETERS_JSON) as f:
		data = json.load(f)

	return parse_parameters(data)