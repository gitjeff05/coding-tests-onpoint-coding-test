import csv
import os

from .database import Base, SessionLocal, engine
from .models import HierarchyNode, Level

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sku_hierarchy.csv")


def get_or_create(db, parent_id, level, name):
    node = (
        db.query(HierarchyNode)
        .filter_by(parent_id=parent_id, level=level, name=name)
        .first()
    )
    if node:
        return node
    node = HierarchyNode(parent_id=parent_id, level=level, name=name)
    db.add(node)
    db.flush()
    return node


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        with open(CSV_PATH, newline="") as f:
            for row in csv.DictReader(f):
                location = get_or_create(db, None, Level.location, row["Location"])
                department = get_or_create(db, location.id, Level.department, row["Department"])
                category = get_or_create(db, department.id, Level.category, row["Category"])
                get_or_create(db, category.id, Level.subcategory, row["SubCategory"])
        db.commit()
        print(f"seeded {db.query(HierarchyNode).count()} nodes")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
