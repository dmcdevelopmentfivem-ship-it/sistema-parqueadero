from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehiculo
from ..schemas import VehiculoCreate, VehiculoOut
from ..deps import get_current_user

router = APIRouter(prefix="/api/vehiculos", tags=["vehiculos"])

@router.get("/", response_model=list[VehiculoOut])
def listar(q: str | None = Query(None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Vehiculo)
    if q:
        query = query.filter(Vehiculo.placa.ilike(f"%{q.upper()}%"))
    return query.order_by(Vehiculo.placa).limit(200).all()

@router.post("/", response_model=VehiculoOut, status_code=201)
def crear(data: VehiculoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    placa = data.placa.upper().strip()
    if db.query(Vehiculo).filter(Vehiculo.placa == placa).first():
        raise HTTPException(400, "Placa ya registrada")
    v = Vehiculo(**{**data.model_dump(), "placa": placa})
    db.add(v); db.commit(); db.refresh(v)
    return v

@router.put("/{vid}", response_model=VehiculoOut)
def actualizar(vid: int, data: VehiculoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    v = db.get(Vehiculo, vid)
    if not v: raise HTTPException(404, "No encontrado")
    for k, val in data.model_dump().items():
        setattr(v, k, val.upper().strip() if k == "placa" else val)
    db.commit(); db.refresh(v); return v
