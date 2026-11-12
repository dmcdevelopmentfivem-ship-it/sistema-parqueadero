from datetime import date, timedelta
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query
from ..database import get_db
from ..models import Ocupacion, Espacio, Vehiculo, Mensualidad, MovimientoCaja
from ..deps import get_current_user

router = APIRouter(prefix="/api/reportes", tags=["reportes"])

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total = db.query(Espacio).filter(Espacio.activo == True).count()
    libres = db.query(Espacio).filter(Espacio.estado == "libre", Espacio.activo == True).count()
    ocupados = total - libres
    activos = db.query(Ocupacion).filter(Ocupacion.estado == "activa").count()
    mens_activas = db.query(Mensualidad).filter(Mensualidad.estado == "activa").count()
    
    hoy = date.today()
    ing_hoy = db.query(func.coalesce(func.sum(MovimientoCaja.monto), 0)).filter(
        func.date(MovimientoCaja.fecha) == hoy,
        MovimientoCaja.tipo == "ingreso"
    ).scalar()
    
    return {
        "espacios_total": total,
        "espacios_libres": libres,
        "espacios_ocupados": ocupados,
        "vehiculos_dentro": activos,
        "mensualidades_activas": mens_activas,
        "ingresos_hoy": float(ing_hoy or 0)
    }

@router.get("/ocupacion-por-tipo")
def ocupacion_por_tipo(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(
        Espacio.tipo_vehiculo,
        func.count(Espacio.id).label("total"),
        func.sum(case((Espacio.estado == "libre", 1), else_=0)).label("libres")
    ).filter(Espacio.activo == True).group_by(Espacio.tipo_vehiculo).all()
    return [{"tipo": r.tipo_vehiculo, "total": r.total, "libres": r.libres or 0} for r in rows]

@router.get("/ingresos-rango")
def ingresos_rango(desde: date = Query(...), hasta: date = Query(...),
                   db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(
        func.date(Ocupacion.hora_salida).label("fecha"),
        func.count(Ocupacion.id).label("cantidad"),
        func.coalesce(func.sum(Ocupacion.valor_cobrado), 0).label("total")
    ).filter(
        func.date(Ocupacion.hora_salida) >= desde,
        func.date(Ocupacion.hora_salida) <= hasta,
        Ocupacion.estado == "cerrada"
    ).group_by(func.date(Ocupacion.hora_salida)).order_by(func.date(Ocupacion.hora_salida)).all()
    return [{"fecha": str(r.fecha), "cantidad": r.cantidad, "total": float(r.total)} for r in rows]

@router.get("/historial")
def historial(desde: date = Query(...), hasta: date = Query(...), placa: str = Query(None),
              db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Ocupacion).filter(
        func.date(Ocupacion.hora_entrada) >= desde,
        func.date(Ocupacion.hora_entrada) <= hasta
    )
    if placa:
        q = q.join(Vehiculo).filter(Vehiculo.placa.ilike(f"%{placa.upper()}%"))
    
    rows = q.order_by(Ocupacion.hora_entrada.desc()).limit(500).all()
    return [{
        "id": o.id,
        "placa": o.vehiculo.placa if o.vehiculo else "-",
        "tipo": o.vehiculo.tipo if o.vehiculo else "-",
        "entrada": o.hora_entrada.isoformat() if o.hora_entrada else None,
        "salida": o.hora_salida.isoformat() if o.hora_salida else None,
        "minutos": o.minutos_total,
        "valor": float(o.valor_cobrado or 0),
        "estado": o.estado
    } for o in rows]
