from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from ..models import Tarifa, Mensualidad

def obtener_tarifa_vigente(tipo_vehiculo: str, db: Session):
    return (
        db.query(Tarifa)
        .filter(Tarifa.tipo_vehiculo == tipo_vehiculo, Tarifa.activa == True)
        .order_by(Tarifa.vigente_desde.desc())
        .first()
    )

def tiene_mensualidad_activa(vehiculo_id: int, db: Session) -> bool:
    hoy = date.today()
    return (
        db.query(Mensualidad)
        .filter(
            Mensualidad.vehiculo_id == vehiculo_id,
            Mensualidad.estado == "activa",
            Mensualidad.fecha_inicio <= hoy,
            Mensualidad.fecha_fin >= hoy,
        )
        .first()
        is not None
    )

def calcular_tarifa(hora_entrada: datetime, hora_salida: datetime, tarifa: Tarifa) -> dict:
    minutos = int((hora_salida - hora_entrada).total_seconds() // 60)
    minutos = max(minutos, 1)

    min_frac = Decimal(tarifa.minutos_fraccion or 1)
    if min_frac <= 0:
        min_frac = Decimal(1)
    valor_minuto = Decimal(tarifa.valor_fraccion) / min_frac
    valor_dia = Decimal(tarifa.valor_dia)

    # Si pasa de 24 horas, cobramos los días completos + resto con tope diario
    if minutos >= 24 * 60:
        dias = minutos // (24 * 60)
        resto = minutos % (24 * 60)
        valor_resto = min(Decimal(resto) * valor_minuto, valor_dia) if valor_dia > 0 else (Decimal(resto) * valor_minuto)
        valor = (Decimal(dias) * valor_dia) + valor_resto
        detalle = f"{dias} día(s) + {resto} minuto(s)" if resto > 0 else f"{dias} día(s)"
        return {"minutos": minutos, "valor": valor, "detalle": detalle}

    # Si dura menos de 24 horas, cobramos minutos transcurridos con tope de tarifa día
    valor_calculado = Decimal(minutos) * valor_minuto
    if valor_dia > 0 and valor_calculado > valor_dia:
        return {"minutos": minutos, "valor": valor_dia, "detalle": f"{minutos} min (tope día completo)"}

    return {"minutos": minutos, "valor": valor_calculado, "detalle": f"{minutos} minuto(s)"}