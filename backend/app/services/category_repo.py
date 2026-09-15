from sqlalchemy.orm import Session

from app.models.category import Category


def load_system_category_map(db: Session) -> dict[tuple[str, str], Category]:
    """Returns {(parent_name, child_name): Category} for the seeded system tree."""
    categories = db.query(Category).filter(Category.is_system.is_(True)).all()
    by_id = {c.id: c for c in categories}
    mapping: dict[tuple[str, str], Category] = {}
    for c in categories:
        if c.parent_id is not None:
            parent = by_id.get(c.parent_id)
            if parent:
                mapping[(parent.name, c.name)] = c
    return mapping


def get_uncategorized(db: Session) -> Category | None:
    return (
        db.query(Category)
        .filter(Category.name == "Uncategorized", Category.is_system.is_(True))
        .first()
    )
