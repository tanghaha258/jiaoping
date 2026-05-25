"""System settings service."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.system_setting import SystemSetting
from app.schemas.settings import SettingUpsert


class SettingsService:
    """CRUD helpers for system settings."""

    @staticmethod
    async def list_settings(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> dict:
        query = select(SystemSetting)
        count_query = select(func.count()).select_from(SystemSetting)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(or_(SystemSetting.key.like(pattern), SystemSetting.description.like(pattern)))
            count_query = count_query.where(or_(SystemSetting.key.like(pattern), SystemSetting.description.like(pattern)))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(query.order_by(SystemSetting.key).offset(offset).limit(page_size))
        settings = result.scalars().all()
        return {
            "items": [_setting_to_dict(item) for item in settings],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def get_setting(db: AsyncSession, key: str) -> SystemSetting:
        setting = await db.get(SystemSetting, key)
        if setting is None:
            raise ResourceNotFoundException("Setting not found")
        return setting

    @staticmethod
    async def upsert_setting(db: AsyncSession, key: str, data: SettingUpsert) -> SystemSetting:
        setting = await db.get(SystemSetting, key)
        if setting is None:
            setting = SystemSetting(
                key=key,
                value=data.value,
                description=data.description,
            )
        else:
            setting.value = data.value
            setting.description = data.description
        db.add(setting)
        await db.flush()
        await db.refresh(setting)
        return setting


def _setting_to_dict(setting: SystemSetting) -> dict:
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description,
    }
