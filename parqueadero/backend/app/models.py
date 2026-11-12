from datetime import datetime
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Date,
                        Numeric, ForeignKey, Text, Index)
from sqlalchemy.orm import relationship
from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="operador")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Zona(Base):
    __tablename__ = "zonas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    tipo_vehiculo = Column(String(20), nullable=False)
    espacios = relationship("Espacio", back_populates="zona")


class Espacio(Base):
    __tablename__ = "espacios"
    id = Column(Integer, primary_key=True)
    zona_id = Column(Integer, ForeignKey("zonas.id"))
    codigo = Column(String(10), unique=True, nullable=False)
    tipo_vehiculo = Column(String(20), nullable=False)
    estado = Column(String(20), default="libre")
    activo = Column(Boolean, default=True)
    zona = relationship("Zona", back_populates="espacios")


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    id = Column(Integer, primary_key=True)
    placa = Column(String(10), unique=True, nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    marca = Column(String(50))
    color = Column(String(30))
    propietario = Column(String(100))
    telefono = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class Tarifa(Base):
    __tablename__ = "tarifas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50))
    tipo_vehiculo = Column(String(20), nullable=False)
    valor_hora = Column(Numeric(10, 2), default=0)
    valor_fraccion = Column(Numeric(10, 2), nullable=False)
    minutos_fraccion = Column(Integer, default=15)
    valor_dia = Column(Numeric(10, 2), nullable=False)
    activa = Column(Boolean, default=True)
    vigente_desde = Column(Date, default=lambda: datetime.utcnow().date())


class Mensualidad(Base):
    __tablename__ = "mensualidades"
    id = Column(Integer, primary_key=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), default="activa")
    created_at = Column(DateTime, default=datetime.utcnow)
    vehiculo = relationship("Vehiculo")

    @property
    def placa(self) -> str | None:
        return self.vehiculo.placa if self.vehiculo else None


class Ocupacion(Base):
    __tablename__ = "ocupaciones"
    id = Column(Integer, primary_key=True)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    espacio_id = Column(Integer, ForeignKey("espacios.id"))
    tarifa_id = Column(Integer, ForeignKey("tarifas.id"))
    hora_entrada = Column(DateTime, default=datetime.utcnow, nullable=False)
    hora_salida = Column(DateTime)
    minutos_total = Column(Integer)
    valor_calculado = Column(Numeric(10, 2))
    valor_cobrado = Column(Numeric(10, 2))
    estado = Column(String(20), default="activa")
    observaciones = Column(Text)
    usuario_entrada_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario_salida_id = Column(Integer, ForeignKey("usuarios.id"))

    vehiculo = relationship("Vehiculo")
    espacio = relationship("Espacio")
    tarifa = relationship("Tarifa")

    @property
    def placa(self) -> str | None:
        return self.vehiculo.placa if self.vehiculo else None

    @property
    def tipo_vehiculo(self) -> str | None:
        return self.vehiculo.tipo if self.vehiculo else None

    @property
    def espacio_codigo(self) -> str | None:
        return self.espacio.codigo if self.espacio else None

    __table_args__ = (
        Index("idx_ocup_estado", "estado"),
        Index("idx_ocup_fecha", "hora_entrada"),
    )


class MovimientoCaja(Base):
    __tablename__ = "movimientos_caja"
    id = Column(Integer, primary_key=True)
    ocupacion_id = Column(Integer, ForeignKey("ocupaciones.id"), nullable=True)
    mensualidad_id = Column(Integer, ForeignKey("mensualidades.id"), nullable=True)
    tipo = Column(String(20), nullable=False)
    concepto = Column(String(100), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    metodo_pago = Column(String(20), default="efectivo")
    fecha = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    observacion = Column(Text)


class CierreCaja(Base):
    __tablename__ = "cierres_caja"
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    hora_apertura = Column(DateTime)
    hora_cierre = Column(DateTime, default=datetime.utcnow)
    total_ingresos = Column(Numeric(12, 2), default=0)
    total_egresos = Column(Numeric(12, 2), default=0)
    saldo_esperado = Column(Numeric(12, 2), default=0)
    saldo_contado = Column(Numeric(12, 2), default=0)
    diferencia = Column(Numeric(12, 2), default=0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    observaciones = Column(Text)
