import logging

from sqlalchemy.orm import Session

from . import models, schemas

logger = logging.getLogger(__name__)

LEVEL_PARENT = {
    models.Level.location: None,
    models.Level.department: models.Level.location,
    models.Level.category: models.Level.department,
    models.Level.subcategory: models.Level.category,
}


def _reject(message: str):
    logger.warning("rejected write: %s", message)
    raise ValueError(message)


def validate_parent(db: Session, level: models.Level, parent_id):
    expected_parent_level = LEVEL_PARENT[level]

    if expected_parent_level is None:
        if parent_id is not None:
            _reject(f"{level.value} nodes cannot have a parent")
        return

    if parent_id is None:
        _reject(f"{level.value} nodes require a parent of level {expected_parent_level.value}")

    parent = db.get(models.HierarchyNode, parent_id)
    if parent is None:
        _reject(f"parent {parent_id} not found")
    if parent.level != expected_parent_level:
        _reject(
            f"{level.value} nodes require a parent of level "
            f"{expected_parent_level.value}, got {parent.level.value}"
        )


def get_node(db: Session, node_id: int):
    return db.get(models.HierarchyNode, node_id)


def get_roots(db: Session):
    return (
        db.query(models.HierarchyNode)
        .filter(models.HierarchyNode.parent_id.is_(None))
        .order_by(models.HierarchyNode.name)
        .all()
    )


def list_nodes(db: Session, level: models.Level = None, parent_id: int = None):
    query = db.query(models.HierarchyNode)
    if level is not None:
        query = query.filter(models.HierarchyNode.level == level)
    if parent_id is not None:
        query = query.filter(models.HierarchyNode.parent_id == parent_id)
    return query.order_by(models.HierarchyNode.name).all()


def create_node(db: Session, node: schemas.NodeCreate):
    validate_parent(db, node.level, node.parent_id)
    db_node = models.HierarchyNode(**node.model_dump())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    logger.info("created %s %r (id=%s, parent_id=%s)", db_node.level.value, db_node.name, db_node.id, db_node.parent_id)
    return db_node


def update_node(db: Session, node_id: int, update: schemas.NodeUpdate):
    db_node = get_node(db, node_id)
    if db_node is None:
        logger.warning("update failed: node %s not found", node_id)
        return None

    data = update.model_dump(exclude_unset=True)
    if "parent_id" in data:
        validate_parent(db, db_node.level, data["parent_id"])

    for key, value in data.items():
        setattr(db_node, key, value)

    db.commit()
    db.refresh(db_node)
    logger.info("updated %s id=%s: %s", db_node.level.value, db_node.id, data)
    return db_node


def delete_node(db: Session, node_id: int):
    db_node = get_node(db, node_id)
    if db_node is None:
        logger.warning("delete failed: node %s not found", node_id)
        return False
    logger.info("deleting %s %r (id=%s)", db_node.level.value, db_node.name, db_node.id)
    db.delete(db_node)
    db.commit()
    return True
