from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SKU Hierarchy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/nodes", response_model=List[schemas.Node])
def list_nodes(
    level: Optional[models.Level] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud.list_nodes(db, level=level, parent_id=parent_id)


@app.get("/api/tree", response_model=List[schemas.NodeTree])
def get_tree(db: Session = Depends(get_db)):
    return crud.get_roots(db)


@app.get("/api/nodes/{node_id}", response_model=schemas.Node)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = crud.get_node(db, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.post("/api/nodes", response_model=schemas.Node, status_code=201)
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_node(db, node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/nodes/{node_id}", response_model=schemas.Node)
def update_node(node_id: int, update: schemas.NodeUpdate, db: Session = Depends(get_db)):
    try:
        node = crud.update_node(db, node_id, update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.delete("/api/nodes/{node_id}", status_code=204)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    if not crud.delete_node(db, node_id):
        raise HTTPException(status_code=404, detail="node not found")
