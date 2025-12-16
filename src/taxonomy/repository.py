"""Taxonomy repository."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.taxonomy.models import Category, Subcategory


class TaxonomyRepository:
    """Repository for taxonomy database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_categories_with_subcategories(
        self,
    ) -> list[Category]:
        """Get all categories with their subcategories (not soft-deleted), ordered alphabetically.
        
        Returns:
            List of Category objects with eagerly loaded subcategories, ordered alphabetically.
        """
        result = await self.session.execute(
            select(Category)
            .options(
                selectinload(Category.subcategories)  # CRITICAL: Eager load subcategories
            )
            .where(
                Category.is_del == False,
                Category.deleted_at.is_(None),
            )
            .order_by(func.lower(Category.name))  # Alphabetical ordering (case-insensitive)
        )
        categories = list(result.scalars().all())
        
        # Sort subcategories alphabetically for each category
        for category in categories:
            category.subcategories = sorted(
                [sub for sub in category.subcategories if not sub.is_del and sub.deleted_at is None],
                key=lambda s: s.name.lower()  # Case-insensitive alphabetical ordering
            )
        
        return categories
