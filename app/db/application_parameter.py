
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists

from . import schema, users, enums
from ..schema.application_parameter import ApplicationParameterValue
from ..utils import application_parameter as ap_utils


class ApplicationParameterNotFound(Exception):
	def __init__(self):
		super().__init__("Application Parameter not found")


async def get_application_parameter_by_name(db: AsyncSession, name: str) -> schema.ApplicationParameter | None:
    result = await db.execute(
        select(schema.ApplicationParameter).where(schema.ApplicationParameter.name == name)
    )
    return result.scalar_one_or_none() 


async def check_application_parameter_exists(db: AsyncSession, name: str) -> bool:
	return (await db.execute(select(
		exists().where(
			schema.ApplicationParameter.name == name
		)
	))).scalar()


async def get_application_parameter_value_by_id(db: AsyncSession, ap_id: uuid.UUID) -> schema.APValue | None:
	result = await db.execute(
		select(schema.APValue)
			.where(
				schema.APValue.ap_id == ap_id
			)
	)

	return result.scalar_one_or_none()


async def get_application_parameter_with_value(db: AsyncSession, name: str):
	result = await db.execute(
		select(schema.ApplicationParameter, schema.APValue)
		.outerjoin(
			schema.APValue,
			(schema.APValue.ap_id == schema.ApplicationParameter.id) & (schema.APValue.override == True)
		)
		.where(schema.ApplicationParameter.name == name)
	)
	
	return result.first()


async def get_application_parameter_with_value_by_id(db: AsyncSession, ap_id: uuid.UUID):
	result = await db.execute(
		select(schema.ApplicationParameter, schema.APValue)
		.outerjoin(
			schema.APValue,
			(schema.APValue.ap_id == schema.ApplicationParameter.id) & (schema.APValue.override == True)
		)
		.where(schema.ApplicationParameter.id == ap_id)
	)
	
	return result.first()


async def user_get_application_parameter(db: AsyncSession, name: str, user_id: Optional[int] = None) -> ApplicationParameterValue | None:
	result = await get_application_parameter_with_value(db, name)
	
	if not result:
		return None

	application_parameter, application_parameter_value = result

	if application_parameter.visibility != enums.AP_visibility.public:
		if not user_id:
			return None
		
		user = await users.get_user_by_id(db, user_id)
		
		if not user:
			return None
		
		if application_parameter.visibility == enums.AP_visibility.protected:
			if user.role not in [enums.UserRoles.moderator, enums.UserRoles.admin]:
				return None
			
		if application_parameter.visibility == enums.AP_visibility.private:
			if user.role != enums.UserRoles.admin:
				return None
				
	return ApplicationParameterValue(
		value=application_parameter.default_value if not application_parameter_value\
			   							          or not application_parameter_value.override\
										          else application_parameter_value.value,
		value_type=application_parameter.type
	)


async def add_application_parameter_value(db: AsyncSession, ap_id: uuid.UUID, value: str):
	result = await get_application_parameter_with_value_by_id(db, ap_id)

	if not result:
		raise ApplicationParameterNotFound()
	
	application_parameter, ap_value = result

	if not ap_utils.validate_data(value, application_parameter.type):
		raise ValueError()

	if not ap_value:
		ap_value = schema.APValue(
			ap_id=ap_id,
			value=value,
			override=True
		)
		db.add(ap_value)
	else:
		ap_value.value = value
		ap_value.override = True

	await db.commit()
	return ap_value


async def delete_application_parameter_value(db: AsyncSession, ap_id: uuid.UUID, wipe: bool = False):
	ap_value = await get_application_parameter_value_by_id(db, ap_id)

	if not ap_value:
		raise ValueError()
	
	ap_value.value = "" if wipe else ap_value.value
	ap_value.override = False

	await db.commit()


async def set_default_value(db: AsyncSession, name: str, value: any):
	ap = await get_application_parameter_by_name(db, name)
	
	if not ap_utils.validate_data(value, ap.type):
		raise ValueError()

	ap.default_value = str(value)

	await db.commit()


async def init_ap(db: AsyncSession):
	for ap_dc in ap_utils.get_application_parameters():
		if await check_application_parameter_exists(db, ap_dc.name):
			continue
		
		new_ap = schema.ApplicationParameter(
			name             = ap_dc.name,
			kind             = ap_dc.kind,
			type             = ap_dc.type,
			visibility       = ap_dc.visibility,
			default_value    = ap_dc.default_value
		)

		db.add(new_ap)
		await db.commit()