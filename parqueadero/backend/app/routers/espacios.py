from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Zona, Espacio, Ocupacion
from ..schemas import ZonaCreate, ZonaOut, EspacioCreate, EspacioOut
from ..deps import get_current_user

router = APIRouter(prefix="/api/espacios", tags=["espacios"])

@router.get("/zonas", response_model=list[ZonaOut])
def listar_zonas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Zona).order_by(Zona.nombre).all()

@router.post("/zonas", response_model=ZonaOut, status_code=201)
def crear_zona(data: ZonaCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    z = Zona(**data.model_dump()); db.add(z); db.commit(); db.refresh(z); return z

@router.get("/", response_model=list[EspacioOut])
def listar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Espacio).order_by(Espacio.codigo).all()

@router.get("/libres")
def libres(tipo: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    esp = db.query(Espacio).filter(
        Espacio.tipo_vehiculo == tipo,
        Espacio.estado == "libre",
        Espacio.activo == True,
    ).order_by(Espacio.codigo).all()
    return [{"id": e.id, "codigo": e.codigo} for e in esp]

@router.post("/", response_model=EspacioOut, status_code=201)
def crear(data: EspacioCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.query(Espacio).filter(Espacio.codigo == data.codigo).first():
        raise HTTPException(400, "Código ya existe")
    e = Espacio(**data.model_dump()); db.add(e); db.commit(); db.refresh(e); return e

@router.delete("/{espacio_id}")
def eliminar(espacio_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    espacio = db.get(Espacio, espacio_id)
    if not espacio:
        raise HTTPException(404, "Espacio no encontrado")
    if espacio.estado == "ocupado":
        raise HTTPException(400, "No se puede eliminar un espacio que se encuentra ocupado")
    db.query(Ocupacion).filter(Ocupacion.espacio_id == espacio.id).update({"espacio_id": None})
    db.delete(espacio)
    db.commit()
    return {"status": "ok", "message": f"Espacio {espacio.codigo} eliminado"}
