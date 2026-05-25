"""System settings endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.settings import SettingUpsert
from app.services.settings_service import SettingsService, _setting_to_dict

router = APIRouter(prefix="/settings")


@router.get("")
async def list_settings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    result = await SettingsService.list_settings(db, page=page, page_size=page_size, keyword=keyword)
    return success_response(result)


@router.get("/{key}")
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    setting = await SettingsService.get_setting(db, key)
    return success_response(_setting_to_dict(setting))


@router.put("/{key}")
async def upsert_setting(
    key: str,
    data: SettingUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    setting = await SettingsService.upsert_setting(db, key, data)
    return success_response(_setting_to_dict(setting), message="Setting saved")
