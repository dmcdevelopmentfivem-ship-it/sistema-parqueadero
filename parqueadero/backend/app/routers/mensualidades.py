from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Mensualidad, Vehiculo, MovimientoCaja
from ..schemas import MensualidadCreate, MensualidadOut
from ..deps import get_current_user

router = APIRouter(prefix="/api/mensualidades", tags=["mensualidades"])

@router.get("/", response_model=list[MensualidadOut])
def listar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    db.query(Mensualidad).filter(
        Mensualidad.fecha_fin < date.today(),
        Mensualidad.estado == "activa"
    ).update({"estado": "vencida"})
    db.commit()
    return db.query(Mensualidad).order_by(Mensualidad.fecha_fin.desc()).all()

@router.post("/", response_model=MensualidadOut, status_code=201)
def crear(data: MensualidadCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if data.fecha_fin < data.fecha_inicio:
        raise HTTPException(400, "Fecha fin debe ser >= inicio")

    veh_id = data.vehiculo_id
    placa = data.placa.upper().strip() if data.placa else None

    if placa:
        veh = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()
        if not veh:
            veh = Vehiculo(placa=placa, tipo=data.tipo_vehiculo)
            db.add(veh)
            db.flush()
        veh_id = veh.id
    elif veh_id:
        veh = db.get(Vehiculo, veh_id)
        if not veh:
            raise HTTPException(404, "Vehículo no existe")
        placa = veh.placa
    else:
        raise HTTPException(400, "Debe indicar la placa o el ID del vehículo")

    m = Mensualidad(
        vehiculo_id=veh_id,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        valor=data.valor,
        estado="activa"
    )
    db.add(m); db.flush()
    db.add(MovimientoCaja(
        mensualidad_id=m.id, tipo="ingreso",
        concepto=f"Mensualidad vehículo {placa}",
        monto=data.valor, metodo_pago="efectivo", usuario_id=user.id
    ))
    db.commit(); db.refresh(m)
    return m
