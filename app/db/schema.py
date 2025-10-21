from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import (
	String, Text, Enum as SqlEnum, ForeignKey, Boolean, DateTime, Integer
)
from sqlalchemy.orm import (
	Mapped, mapped_column, relationship, DeclarativeBase
)
from sqlalchemy.dialects.postgresql import UUID

from .enums import *

class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	id                       : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	username                 : Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	password_hash            : Mapped[str] = mapped_column(String(255), nullable=False)
	registration_date        : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
	role                     : Mapped[UserRoles] = mapped_column(SqlEnum(UserRoles, native_enum=False), default=UserRoles.user)
	is_disabled              : Mapped[bool] = mapped_column(Boolean, default=False)
	force_password_change    : Mapped[bool] = mapped_column(Boolean, default=False)
	is_root                  : Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

	topic                        : Mapped[list[Topic]] = relationship(back_populates="creator", cascade="all, delete-orphan")
	tokens                       : Mapped[list[JWT_Token]] = relationship(back_populates="user", cascade="all, delete-orphan")
	audit_log                    : Mapped[list[Audit]] = relationship(back_populates="user")
	media_owner                  : Mapped[list[MediaObject]] = relationship(back_populates="user_uploader", foreign_keys="[MediaObject.uploaded_by_user_id]")
	media_uploader               : Mapped[list[MediaObject]] = relationship(back_populates="user_owner", foreign_keys="[MediaObject.used_user_id]")
	topic_translations: Mapped[list[TopicTranslation]] = relationship(
		back_populates="user",
		foreign_keys="[TopicTranslation.creator_user_id]"
	)
	topic_translations_editor: Mapped[list[TopicTranslation]] = relationship(
		back_populates="user_last_editor",
		foreign_keys="[TopicTranslation.last_edited_by]"
	)


class JWT_Token(Base):
	__tablename__ = "jwt_tokens"

	id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
	token            : Mapped[str] = mapped_column(Text, nullable=False)
	user_id          : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
	created          : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	last_used        : Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	device_name      : Mapped[str] = mapped_column(String(100), nullable=False)
	on_creation_ip   : Mapped[str] = mapped_column(String(45), nullable=False)
	expires_at       : Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	is_revoked       : Mapped[bool] = mapped_column(Boolean, default=False)

	user: Mapped[User] = relationship(back_populates="tokens")


class Translation(Base):
	__tablename__ = "translations"

	id                 : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	translation_code   : Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
	full_name          : Mapped[str] = mapped_column(String(100), nullable=False)

	topic_translations: Mapped[list[TopicTranslation]] = relationship(back_populates="translation", cascade="all, delete-orphan")


class Topic(Base):
	__tablename__ = "topic"

	id                 : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	name               : Mapped[str] = mapped_column(String(200), nullable=False)
	name_hash          : Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
	created_at         : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
	edited_at          : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
	imported           : Mapped[bool] = mapped_column(Boolean, nullable=False)
	creator_user_id    : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
	cover_image_id     : Mapped[Optional[int]] = mapped_column(ForeignKey("media_object.id", ondelete="SET NULL"), nullable=True)

	creator: Mapped[User] = relationship(back_populates="topic")
	translations: Mapped[list[TopicTranslation]] = relationship(back_populates="topic", cascade="all, delete-orphan")

	categories: Mapped[list[Category]] = relationship(
		secondary="categories_in_topic",
		back_populates="topic"
	)

	tags: Mapped[list[Tag]] = relationship(
		secondary="tags_in_topic",
		back_populates="topic"
	)

	media_object   : Mapped[list[MediaObject]] = relationship(back_populates="topic", foreign_keys="[MediaObject.used_topic_id]")
	links          : Mapped[list[TopicLink]]   = relationship(back_populates="topic", cascade="all, delete-orphan")


class TopicTranslation(Base):
	__tablename__ = "topic_translations"

	id               : Mapped[int] = mapped_column(primary_key=True)
	translation_id   : Mapped[int] = mapped_column(ForeignKey("translations.id", ondelete="CASCADE"), nullable=False)
	topic_id         : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
	creator_user_id  : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
	parse_mode       : Mapped[ParseMode] = mapped_column(SqlEnum(ParseMode, native_enum=False), nullable=False)
	last_edited_by   : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
	text             : Mapped[str] = mapped_column(Text, nullable=False)
	first            : Mapped[bool] = mapped_column(Boolean, nullable=False)

	translation      : Mapped[Translation] = relationship(back_populates="topic_translations")
	topic            : Mapped[Topic] = relationship(back_populates="translations")
	user: Mapped[User] = relationship(
		back_populates="topic_translations",
		foreign_keys=[creator_user_id]
	)
	user_last_editor: Mapped[User] = relationship(
		back_populates="topic_translations_editor",
		foreign_keys=[last_edited_by]
	)


class Category(Base):
	__tablename__ = "categories"

	id             : Mapped[int] = mapped_column(primary_key=True)
	name           : Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	description    : Mapped[str] = mapped_column(Text)
	display_mode   : Mapped[DisplayMode] = mapped_column(SqlEnum(DisplayMode, native_enum=False))

	topic: Mapped[list[Topic]] = relationship(
		secondary="categories_in_topic",
		back_populates="categories"
	)


class CategoryInTopic(Base):
	__tablename__ = "categories_in_topic"

	topic_id       : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True)
	category_id    : Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)


class Tag(Base):
	__tablename__ = "tags"

	id             : Mapped[int] = mapped_column(primary_key=True)
	name           : Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	description    : Mapped[str] = mapped_column(Text)

	topic: Mapped[list[Topic]] = relationship(
		secondary="tags_in_topic",
		back_populates="tags"
	) 


class TagInTopic(Base):
	__tablename__ = "tags_in_topic"

	topic_id   : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True)
	tag_id     : Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class TopicLink(Base):
	__tablename__ = "topic_links"

	id         : Mapped[int] = mapped_column(primary_key=True)
	topic_id   : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
	link_name  : Mapped[str] = mapped_column(String(200), nullable=False)
	link_url   : Mapped[str] = mapped_column(String(500), nullable=False)
	away       : Mapped[bool] = mapped_column(Boolean, default=False)

	topic: Mapped[Topic] = relationship(back_populates="links")


class Audit(Base):
	__tablename__ = "audit"

	id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	action_type      : Mapped[ActionType] = mapped_column(SqlEnum(ActionType, native_enum=False), nullable=False)
	user_id          : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	timestamp        : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
	reason           : Mapped[str] = mapped_column(Text, nullable=True)

	user: Mapped[User] = relationship(back_populates="audit_log")
	effected_object: Mapped[list[AuditEffectedObject]] = relationship(back_populates="audit")


class AuditEffectedObject(Base):
	__tablename__ = "audit_effected_objects"

	id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	audit_id         : Mapped[uuid.UUID] = mapped_column(ForeignKey("audit.id", ondelete="CASCADE"), nullable=False)
	object_type      : Mapped[ObjectType] = mapped_column(SqlEnum(ObjectType, native_enum=False), nullable=False)
	object_id        : Mapped[int] = mapped_column(Integer, nullable=False)

	audit: Mapped[Audit] = relationship(back_populates="effected_object")


class MediaObject(Base):
	__tablename__ = "media_object"

	id                     : Mapped[int] = mapped_column(primary_key=True)
	obj_type               : Mapped[MediaType] = mapped_column(SqlEnum(MediaType, native_enum=False), nullable=False)
	file_path              : Mapped[str] = mapped_column(String(500), nullable=False)
	uploaded_at            : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
	sha256_hash_original   : Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
	sha256_hash_thumb      : Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
	sha256_hash_small      : Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
	sha256_hash_medium     : Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
	sha256_hash_large      : Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
	has_small              : Mapped[bool] = mapped_column(Boolean, default=False)
	has_medium             : Mapped[bool] = mapped_column(Boolean, default=False)
	has_large              : Mapped[bool] = mapped_column(Boolean, default=False)

	uploaded_by_user_id    : Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
	used_topic_id          : Mapped[Optional[int]] = mapped_column(ForeignKey("topic.id", ondelete="SET NULL"), nullable=True)
	used_user_id           : Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

	user_owner       : Mapped[Optional[User]] = relationship(back_populates="media_uploader", foreign_keys=[used_user_id])
	user_uploader    : Mapped[User] = relationship(back_populates="media_owner", foreign_keys=[uploaded_by_user_id])
	topic            : Mapped[Optional[Topic]] = relationship(
		back_populates  = "media_object",
		foreign_keys    = [used_topic_id]
	)


class ApplicationParameter(Base):
	__tablename__ = "application_parameters"

	id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	name             : Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
	kind             : Mapped[AP_kind] = mapped_column(SqlEnum(AP_kind, native_enum=False), nullable=False)
	type             : Mapped[AP_type] = mapped_column(SqlEnum(AP_type, native_enum=False), nullable=False)
	visibility       : Mapped[AP_visibility] = mapped_column(SqlEnum(AP_visibility, native_enum=False), nullable=False)
	default_value    : Mapped[str] = mapped_column(Text, nullable=True)

	value: Mapped[list["APValue"]] = relationship(back_populates="parameter", cascade="all, delete-orphan")


class APValue(Base):
	__tablename__ = "ap_value"

	id       : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	value    : Mapped[str] = mapped_column(Text, nullable=True)
	override : Mapped[bool] = mapped_column(Boolean, default=False)
	ap_id    : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
		ForeignKey("application_parameters.id", ondelete="CASCADE"), nullable=False,
	)
	
	parameter: Mapped["ApplicationParameter"] = relationship(back_populates="value")