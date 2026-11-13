from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehiculo, Espacio, Ocupacion, MovimientoCaja
from ..schemas import EntradaCreate, EntradaOut, SalidaPago, OcupacionOut
from ..deps import get_current_user
from ..services.tarifa_service import (
    obtener_tarifa_vigente, tiene_mensualidad_activa, calcular_tarifa
)

router = APIRouter(prefix="/api/entradas", tags=["entradas"])

@router.get("/activas")
def activas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    ocupaciones = db.query(Ocupacion).filter(Ocupacion.estado == "activa").order_by(Ocupacion.hora_entrada).all()
    
    # Armamos la respuesta incluyendo la placa y el código del espacio
    resultado = []
    for o in ocupaciones:
        resultado.append({
            "id": o.id,
            "vehiculo_id": o.vehiculo_id,
            "placa": o.vehiculo.placa if o.vehiculo else "Desconocida",
            "tipo_vehiculo": o.vehiculo.tipo if o.vehiculo else "-",
            "espacio": o.espacio.codigo if o.espacio else "-",
            "hora_entrada": o.hora_entrada,
            "estado": o.estado
        })
    return resultado

@router.post("/entrada", response_model=EntradaOut, status_code=201)
def registrar_entrada(data: EntradaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    placa = data.placa.upper().strip()

    veh = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()
    if not veh:
        veh = Vehiculo(placa=placa, tipo=data.tipo_vehiculo,
                       marca=data.marca, color=data.color)
        db.add(veh); db.flush()

    if db.query(Ocupacion).filter(Ocupacion.vehiculo_id == veh.id, Ocupacion.estado == "activa").first():
        raise HTTPException(400, "El vehículo ya está dentro")

    if data.espacio_id:
        espacio = db.query(Espacio).filter(Espacio.id == data.espacio_id, Espacio.estado == "libre").first()
    else:
        espacio = db.query(Espacio).filter(
            Espacio.tipo_vehiculo == veh.tipo,
            Espacio.estado == "libre",
            Espacio.activo == True
        ).order_by(Espacio.codigo).first()
    if not espacio:
        raise HTTPException(400, "No hay espacios libres disponibles para este tipo de vehículo")

    tarifa = obtener_tarifa_vigente(veh.tipo, db)
    if not tarifa:
        raise HTTPException(400, f"No hay tarifa vigente para {veh.tipo}")

    ocup = Ocupacion(vehiculo_id=veh.id, espacio_id=espacio.id,
                     tarifa_id=tarifa.id, usuario_entrada_id=user.id)
    espacio.estado = "ocupado"
    db.add(ocup); db.commit(); db.refresh(ocup)
    return ocup

@router.get("/calcular/{ocupacion_id}")
def calcular(ocupacion_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    o = db.get(Ocupacion, ocupacion_id)
    if not o or o.estado != "activa":
        raise HTTPException(404, "Ocupación no activa")
    if tiene_mensualidad_activa(o.vehiculo_id, db):
        return {"minutos": int((datetime.utcnow() - o.hora_entrada).total_seconds() // 60),
                "valor": 0, "detalle": "Abonado mensual"}
    return calcular_tarifa(o.hora_entrada, datetime.utcnow(), o.tarifa)

@router.post("/salida/{ocupacion_id}")
def registrar_salida(ocupacion_id: int, data: SalidaPago,
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.get(Ocupacion, ocupacion_id)
    if not o or o.estado != "activa":
        raise HTTPException(404, "Ocupación no activa")

    hora_salida = datetime.utcnow()
    o.hora_salida = hora_salida

    if tiene_mensualidad_activa(o.vehiculo_id, db):
        valor = Decimal("0.00")
        concepto = "Salida abonado"
    else:
        calc = calcular_tarifa(o.hora_entrada, hora_salida, o.tarifa)
        valor = Decimal(calc["valor"])
        concepto = f"Parqueo {o.vehiculo.placa} - {calc['detalle']}"

    o.minutos_total = int((hora_salida - o.hora_entrada).total_seconds() // 60)
    o.valor_calculado = valor
    o.valor_cobrado = valor
    o.estado = "cerrada"
    o.usuario_salida_id = user.id

    if o.espacio_id:
        esp = db.get(Espacio, o.espacio_id)
        if esp: esp.estado = "libre"

    if valor > 0:
        db.add(MovimientoCaja(
            ocupacion_id=o.id, tipo="ingreso", concepto=concepto,
            monto=valor, metodo_pago=data.metodo_pago, usuario_id=user.id
        ))

    db.commit()
    cambio = float(data.monto_recibido or valor) - float(valor)
    return {"ocupacion_id": o.id, "minutos": o.minutos_total,
            "valor": float(valor), "cambio": round(cambio, 2),
            "placa": o.vehiculo.placa}