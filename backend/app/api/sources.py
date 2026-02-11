import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.source import Source
from app.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=SourceListResponse)
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all configured camera/sensor sources."""
    result = await db.execute(select(Source).order_by(Source.created_at))
    sources = result.scalars().all()

    return SourceListResponse(
        sources=[SourceResponse.model_validate(s) for s in sources],
        total=len(sources),
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single source by ID."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return SourceResponse.model_validate(source)


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new camera/sensor source."""
    source = Source(
        **payload.model_dump(
            exclude={"location"},
            exclude_unset=False,
        ),
        location=payload.location.model_dump() if payload.location else None,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing source. Only provided fields are updated."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Handle nested location object
    if "location" in update_data:
        loc = update_data.pop("location")
        source.location = loc.model_dump() if loc else None

    for key, value in update_data.items():
        setattr(source, key, value)

    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a source."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    await db.delete(source)
    await db.commit()
