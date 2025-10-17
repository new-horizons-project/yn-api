import datetime
import uuid
import hashlib
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from . import schema
from .. import config
from ..utils import media as m
from ..db.enums import MediaType, MediaSize


async def add_media(db: AsyncSession, user: schema.User, topic_id: int | None, file: UploadFile, content_type: MediaType,
				    generate_types: list[MediaSize] = [MediaSize.thumbnail], trim: bool = True) -> schema.MediaObject:
	file_name = "uuid" + str(uuid.uuid4()) + "_" + file.filename

	original_file = BytesIO()
	while chunk := await file.read(1024*1024):
		original_file.write(chunk)
	
	original_file.seek(0)

	media = schema.MediaObject(
		file_path = file_name,
		obj_type = content_type,
		uploaded_by_user_id = user.id,
		sha256_hash_original = hashlib.sha256(original_file.getvalue()).hexdigest(),
		used_user_id = user.id if content_type == MediaType.user_avatar else None,
		used_topic_id = topic_id,
	)

	if MediaSize.thumbnail not in generate_types:
		generate_types.append(MediaSize.thumbnail)

	for size in generate_types:		
		generated_file = m.resize_image(original_file.getvalue(), size, trim)
		generated_sha256 = hashlib.sha256(generated_file).hexdigest()
		generated_file_name = f"{size.value}_{file_name}"

		match size:
			case MediaSize.small:
				media.has_small = True
				media.sha256_hash_small = generated_sha256
			case MediaSize.medium:
				media.has_medium = True
				media.sha256_hash_medium = generated_sha256
			case MediaSize.large:
				media.has_large = True
				media.sha256_hash_large = generated_sha256
			case MediaSize.thumbnail:
				media.sha256_hash_thumb = generated_sha256
		
		with open(f"{config.settings.STATIC_MEDIA_FOLDER}/{generated_file_name}", "wb") as f:
			f.write(generated_file)

	with open(f"{config.settings.STATIC_MEDIA_FOLDER}/{file_name}", "wb") as f:
		f.write(original_file.getvalue())

	db.add(media)
	await db.commit()

	return media


async def init_media(db: AsyncSession):
	result = await db.execute(select(schema.MediaObject))
	if result.first():
		return

	with open("./media/logo.png", "rb") as f:
		logo_data = f.read()
		await add_media(
			db,
			topic_id = None,
			user = schema.User(id=1),
			file = UploadFile(
				filename="logo.png",
				file=BytesIO(logo_data)),
			content_type = MediaType.system,
			generate_types=[
				MediaSize.small,
				MediaSize.medium,
				MediaSize.large
			],
			trim=True
		)


async def get_media_by_id(media_id: int, db: AsyncSession, preload_all: bool = False) -> schema.MediaObject | None:
	if preload_all:
		result = await db.scalar(
			select(schema.MediaObject)
			.where(schema.MediaObject.id == media_id)
			.options(
				selectinload(schema.MediaObject.user_uploader),
				selectinload(schema.MediaObject.user_owner),
				selectinload(schema.MediaObject.topic)
			)
		)
	else:
		result = await db.get(schema.MediaObject, media_id)

	return result