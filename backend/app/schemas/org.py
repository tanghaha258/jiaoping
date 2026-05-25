"""Schemas for organization base-data management."""

from typing import Optional

from pydantic import BaseModel, Field


class RegionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)


class SchoolCreate(BaseModel):
    region_id: str
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class SchoolUpdate(BaseModel):
    region_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")


class ClassCreate(BaseModel):
    school_id: str
    grade: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    academic_year: str = Field(..., min_length=1, max_length=20)


class ClassUpdate(BaseModel):
    school_id: Optional[str] = None
    grade: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=20)


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    stage: str = Field(default="junior_high", min_length=1, max_length=50)


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    stage: Optional[str] = Field(None, min_length=1, max_length=50)
