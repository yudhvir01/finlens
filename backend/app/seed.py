"""Seeds the system category tree. Safe to run repeatedly — skips categories
that already exist by (parent_name, name).

Usage: python -m app.seed
"""
from app.db.session import SessionLocal
from app.models.category import Category
from app.services.seed_categories import SEED_CATEGORIES


def run() -> None:
    db = SessionLocal()
    try:
        existing = {(c.parent_id, c.name) for c in db.query(Category).filter(Category.is_system.is_(True)).all()}

        for parent_name, children in SEED_CATEGORIES.items():
            parent = (
                db.query(Category)
                .filter(Category.name == parent_name, Category.is_system.is_(True), Category.parent_id.is_(None))
                .first()
            )
            if parent is None:
                parent = Category(name=parent_name, is_system=True)
                db.add(parent)
                db.flush()

            for child_name in children:
                if (parent.id, child_name) in existing:
                    continue
                db.add(Category(name=child_name, parent_id=parent.id, is_system=True))

        db.commit()
        print("Seeded system categories.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
