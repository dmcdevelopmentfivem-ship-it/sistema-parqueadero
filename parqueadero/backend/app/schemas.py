from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre: str


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str = "operador"


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool


class VehiculoCreate(BaseModel):
    placa: str
    tipo: str
    marca: str | None = None
    color: str | None = None
    propietario: str | None = None
    telefono: str | None = None


class VehiculoOut(VehiculoCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ZonaCreate(BaseModel):
    nombre: str
    tipo_vehiculo: str


class ZonaOut(ZonaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EspacioCreate(BaseModel):
    zona_id: int | None = None
    codigo: str
    tipo_vehiculo: str


class EspacioOut(EspacioCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estado: str


class TarifaCreate(BaseModel):
    nombre: str
    tipo_vehiculo: str
    valor_hora: Decimal = Decimal("0")
    valor_fraccion: Decimal
    minutos_fraccion: int = 15
    valor_dia: Decimal


class TarifaOut(TarifaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activa: bool


class EntradaCreate(BaseModel):
    placa: str
    tipo_vehiculo: str
    espacio_id: int | None = None
    marca: str | None = None
    color: str | None = None


class EntradaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehiculo_id: int
    espacio_id: int | None
    hora_entrada: datetime
    estado: str


class SalidaPago(BaseModel):
    metodo_pago: str = "efectivo"
    monto_recibido: Decimal | None = None


class OcupacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehiculo_id: int
    placa: str | None = None
    tipo_vehiculo: str | None = None
    espacio_id: int | None
    espacio_codigo: str | None = None
    hora_entrada: datetime
    hora_salida: datetime | None
    minutos_total: int | None
    valor_calculado: Decimal | None
    valor_cobrado: Decimal | None
    estado: str


class MensualidadCreate(BaseModel):
    placa: str | None = None
    vehiculo_id: int | None = None
    tipo_vehiculo: str = "carro"
    fecha_inicio: date
    fecha_fin: date
    valor: Decimal


class MensualidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehiculo_id: int
    placa: str | None = None
    fecha_inicio: date
    fecha_fin: date
    valor: Decimal
    estado: str


class CierreCajaCreate(BaseModel):
    saldo_contado: Decimal
    observaciones: str = ""


class MovimientoCreate(BaseModel):
    tipo: str
    concepto: str
    monto: Decimal
    metodo_pago: str = "efectivo"
    observacion: str | None = None


class MovimientoOut(MovimientoCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha: datetime
