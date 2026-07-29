import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .auth import require_auth
from .auth import router as auth_router
from .database import get_db
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="SKU Hierarchy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        '%s %s -> %s (%.1fms)',
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.exception("health check: database connectivity failed")
        db_ok = False
    body = {"status": "ok" if db_ok else "unhealthy", "db": db_ok}
    return JSONResponse(status_code=200 if db_ok else 503, content=body)


app.include_router(auth_router)

api_router = APIRouter(prefix="/api", dependencies=[Depends(require_auth)])


@api_router.get("/nodes", response_model=List[schemas.Node])
def list_nodes(
    level: Optional[models.Level] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud.list_nodes(db, level=level, parent_id=parent_id)


@api_router.get("/tree", response_model=List[schemas.NodeTree])
def get_tree(db: Session = Depends(get_db)):
    return crud.get_roots(db)


@api_router.get("/nodes/{node_id}", response_model=schemas.Node)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = crud.get_node(db, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@api_router.post("/nodes", response_model=schemas.Node, status_code=201)
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_node(db, node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.put("/nodes/{node_id}", response_model=schemas.Node)
def update_node(node_id: int, update: schemas.NodeUpdate, db: Session = Depends(get_db)):
    try:
        node = crud.update_node(db, node_id, update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@api_router.delete("/nodes/{node_id}", status_code=204)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    if not crud.delete_node(db, node_id):
        raise HTTPException(status_code=404, detail="node not found")


app.include_router(api_router)
