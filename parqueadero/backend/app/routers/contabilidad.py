from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MovimientoCaja, CierreCaja, Ocupacion
from ..schemas import MovimientoCreate, MovimientoOut, CierreCajaCreate
from ..deps import get_current_user, require_admin

router = APIRouter(prefix="/api/contabilidad", tags=["contabilidad"])

@router.get("/movimientos", response_model=list[MovimientoOut])
def movimientos(desde: date = Query(...), hasta: date = Query(...),
                db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(MovimientoCaja).filter(
        func.date(MovimientoCaja.fecha) >= desde,
        func.date(MovimientoCaja.fecha) <= hasta
    ).order_by(MovimientoCaja.fecha.desc()).all()

@router.post("/movimientos", response_model=MovimientoOut, status_code=201)
def crear_movimiento(data: MovimientoCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = MovimientoCaja(**data.model_dump(), usuario_id=user.id)
    db.add(m); db.commit(); db.refresh(m); return m

@router.get("/resumen")
def resumen(fecha: date = Query(default=None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    fecha = fecha or date.today()
    movs = db.query(MovimientoCaja).filter(func.date(MovimientoCaja.fecha) == fecha).all()
    ingresos = sum(m.monto for m in movs if m.tipo == "ingreso") or Decimal(0)
    egresos = sum(m.monto for m in movs if m.tipo == "egreso") or Decimal(0)
    por_metodo = {}
    for m in movs:
        if m.tipo == "ingreso":
            por_metodo[m.metodo_pago] = float(por_metodo.get(m.metodo_pago, 0) + m.monto)
    return {
        "fecha": str(fecha),
        "ingresos": float(ingresos),
        "egresos": float(egresos),
        "neto": float(ingresos - egresos),
        "movimientos": len(movs),
        "por_metodo": por_metodo
    }

@router.post("/cierre")
def cerrar_caja(data: CierreCajaCreate,
                db: Session = Depends(get_db), user=Depends(require_admin)):
    hoy = date.today()
    movs = db.query(MovimientoCaja).filter(func.date(MovimientoCaja.fecha) == hoy).all()
    ingresos = sum(m.monto for m in movs if m.tipo == "ingreso") or Decimal(0)
    egresos = sum(m.monto for m in movs if m.tipo == "egreso") or Decimal(0)
    esperado = ingresos - egresos
    cierre = CierreCaja(
        fecha=hoy, total_ingresos=ingresos, total_egresos=egresos,
        saldo_esperado=esperado, saldo_contado=data.saldo_contado,
        diferencia=data.saldo_contado - esperado,
        usuario_id=user.id, observaciones=data.observaciones
    )
    db.add(cierre); db.commit(); db.refresh(cierre)
    return {"cierre_id": cierre.id, "esperado": float(esperado), "contado": float(data.saldo_contado)}
