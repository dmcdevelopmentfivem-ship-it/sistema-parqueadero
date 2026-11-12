from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tarifa
from ..schemas import TarifaCreate, TarifaOut
from ..deps import get_current_user

router = APIRouter(prefix="/api/tarifas", tags=["tarifas"])

@router.get("/", response_model=list[TarifaOut])
def listar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Tarifa).order_by(Tarifa.tipo_vehiculo, Tarifa.id).all()

@router.post("/", response_model=TarifaOut, status_code=201)
def crear(data: TarifaCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    # Desactiva tarifas anteriores del mismo tipo
    db.query(Tarifa).filter(Tarifa.tipo_vehiculo == data.tipo_vehiculo).update({"activa": False})
    t = Tarifa(**data.model_dump()); db.add(t); db.commit(); db.refresh(t); return t
