#!/usr/bin/env python3
"""
Generador del proyecto Sistema de Parqueadero.
Ejecutar: python setup.py
Crea toda la estructura de carpetas y archivos en ./parqueadero/
"""
import os
from pathlib import Path

BASE = Path("parqueadero")

FILES: dict[str, str] = {}

def add(path: str, content: str):
    FILES[path] = content

# ============================================================
# DOCKER / CONFIGURACIÓN RAÍZ
# ============================================================

add("docker-compose.yml", """version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-parqueadero}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-parqueadero123}
      POSTGRES_DB: ${POSTGRES_DB:-parqueadero}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-parqueadero}"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+psycopg2://${POSTGRES_USER:-parqueadero}:${POSTGRES_PASSWORD:-parqueadero123}@db:5432/${POSTGRES_DB:-parqueadero}
      SECRET_KEY: ${SECRET_KEY:-cambia-esta-clave-en-produccion}
      ACCESS_TOKEN_EXPIRE_MINUTES: 480
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "3000:80"

volumes:
  pgdata:
""")

add(".env.example", """POSTGRES_USER=parqueadero
POSTGRES_PASSWORD=parqueadero123
POSTGRES_DB=parqueadero
SECRET_KEY=super-secreto-cambialo
""")

add("README.md", """# Sistema de Parqueadero

Sistema web de gestión para parqueadero mixto (carros, motos, bicicletas).

## Requisitos
- Docker Desktop

## Iniciar

```bash
docker compose up -d --build
```
""")
# ============================================================
# BACKEND - CONFIGURACIÓN Y CORE
# ============================================================

add("backend/requirements.txt", """fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==3.2.2
python-multipart==0.0.9
openpyxl==3.1.5
jinja2==3.1.4
email-validator==2.2.0
""")

add("backend/Dockerfile", """FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential libpq-dev libffi-dev && \\
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
""")

add("backend/app/__init__.py", "")

add("backend/app/config.py", """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./parqueadero.db"
    SECRET_KEY: str = "cambia-esta-clave"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"

settings = Settings()
""")

add("backend/app/database.py", """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""")

# ============================================================
# BACKEND - MODELOS DE BASE DE DATOS
# ============================================================

add("backend/app/models.py", """from datetime import datetime
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
""")

# ============================================================
# BACKEND - SEGURIDAD Y SCHEMAS
# ============================================================

add("backend/app/security.py", """from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return pwd_context.verify(p, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return {}
""")

add("backend/app/deps.py", """from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import Usuario
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    payload = decode_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    user = db.query(Usuario).filter(Usuario.email == email, Usuario.activo == True).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no encontrado")
    return user

def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol admin")
    return user
""")

add("backend/app/schemas.py", """from datetime import datetime, date
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
""")

# ============================================================
# BACKEND - SERVICIOS (Lógica de negocio)
# ============================================================

add("backend/app/services/__init__.py", "")

add("backend/app/services/tarifa_service.py", """from datetime import datetime, date
from decimal import Decimal, ROUND_CEILING
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
""")

# ============================================================
# BACKEND - ROUTERS
# ============================================================

add("backend/app/routers/__init__.py", "")

add("backend/app/routers/auth.py", """from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..security import verify_password, create_access_token
from ..schemas import Token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == form.username, Usuario.activo == True).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Credenciales inválidas")
    token = create_access_token({"sub": user.email, "rol": user.rol})
    return Token(access_token=token, rol=user.rol, nombre=user.nombre)
""")

add("backend/app/routers/usuarios.py", """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..schemas import UsuarioCreate, UsuarioOut
from ..security import hash_password
from ..deps import require_admin, get_current_user

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

@router.get("/", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Usuario).order_by(Usuario.id).all()

@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)):
    return user

@router.post("/", response_model=UsuarioOut, status_code=201)
def crear(data: UsuarioCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(400, "Email ya registrado")
    u = Usuario(nombre=data.nombre, email=data.email,
                password_hash=hash_password(data.password), rol=data.rol)
    db.add(u); db.commit(); db.refresh(u)
    return u
""")

add("backend/app/routers/vehiculos.py", """from fastapi import APIRouter, Depends, HTTPException, Query
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
""")

add("backend/app/routers/espacios.py", """from fastapi import APIRouter, Depends, HTTPException
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
""")

add("backend/app/routers/tarifas.py", """from fastapi import APIRouter, Depends
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
""")

add("backend/app/routers/entradas.py", """from datetime import datetime
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

@router.get("/activas", response_model=list[OcupacionOut])
def activas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Ocupacion).filter(Ocupacion.estado == "activa").order_by(Ocupacion.hora_entrada).all()

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
        raise HTTPException(400, "No hay espacios libres disponibles")

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
""")

add("backend/app/routers/mensualidades.py", """from datetime import date
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
""")

add("backend/app/routers/contabilidad.py", """from datetime import date
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
""")

add("backend/app/routers/reportes.py", """from datetime import date, timedelta
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
""")

# ============================================================
# BACKEND - MAIN
# ============================================================

add("backend/app/main.py", """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from . import models
from .security import hash_password
from .routers import (auth, usuarios, vehiculos, espacios, tarifas,
                      entradas, mensualidades, contabilidad, reportes)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Seed de datos iniciales
def seed():
    db = SessionLocal()
    try:
        if not db.query(models.Usuario).first():
            db.add(models.Usuario(
                nombre="Administrador",
                email="admin@parqueadero.com",
                password_hash=hash_password("admin123"),
                rol="admin"
            ))
            db.add(models.Tarifa(
                nombre="Tarifa Carro", tipo_vehiculo="carro",
                valor_hora=5000, valor_fraccion=2000,
                minutos_fraccion=15, valor_dia=30000
            ))
            db.add(models.Tarifa(
                nombre="Tarifa Moto", tipo_vehiculo="moto",
                valor_hora=3000, valor_fraccion=1000,
                minutos_fraccion=15, valor_dia=18000
            ))
            db.add(models.Tarifa(
                nombre="Tarifa Bici", tipo_vehiculo="bici",
                valor_hora=1000, valor_fraccion=500,
                minutos_fraccion=30, valor_dia=5000
            ))
            db.commit()
    finally:
        db.close()

seed()

app = FastAPI(title="Sistema Parqueadero API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(vehiculos.router)
app.include_router(espacios.router)
app.include_router(tarifas.router)
app.include_router(entradas.router)
app.include_router(mensualidades.router)
app.include_router(contabilidad.router)
app.include_router(reportes.router)

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
""")
# ============================================================
# FRONTEND - CONFIGURACIÓN BASE
# ============================================================

add("frontend/package.json", """{
  "name": "parqueadero-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "lucide-react": "^0.441.0",
    "recharts": "^2.12.7"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.12",
    "vite": "^5.4.7"
  }
}
""")

add("frontend/vite.config.js", """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
""")

add("frontend/tailwind.config.js", """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
""")

add("frontend/postcss.config.js", """export default {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}
""")

add("frontend/index.html", """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Parqueadero - Gestión</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""")

add("frontend/Dockerfile", """FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""")

add("frontend/nginx.conf", """server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
""")

# ============================================================
# FRONTEND - CÓDIGO FUENTE
# ============================================================

add("frontend/src/index.css", """@tailwind base;
@tailwind components;
@tailwind utilities;

body { @apply bg-slate-100 text-slate-800; }
.btn { @apply px-4 py-2 rounded-lg font-medium transition shadow-sm; }
.btn-primary { @apply bg-blue-600 text-white hover:bg-blue-700; }
.btn-danger { @apply bg-red-600 text-white hover:bg-red-700; }
.btn-success { @apply bg-green-600 text-white hover:bg-green-700; }
.input { @apply w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none; }
.card { @apply bg-white rounded-xl shadow-sm border border-slate-200 p-5; }
""")

add("frontend/src/main.jsx", """import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
""")

add("frontend/src/api.js", """import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
""")

add("frontend/src/auth.jsx", """import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem('user')
    return u ? JSON.parse(u) : null
  })

  const login = (data) => {
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify({ nombre: data.nombre, rol: data.rol }))
    setToken(data.access_token)
    setUser({ nombre: data.nombre, rol: data.rol })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null); setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
""")

add("frontend/src/App.jsx", """import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Entradas from './pages/Entradas'
import Espacios from './pages/Espacios'
import Vehiculos from './pages/Vehiculos'
import Tarifas from './pages/Tarifas'
import Mensualidades from './pages/Mensualidades'
import Contabilidad from './pages/Contabilidad'
import Reportes from './pages/Reportes'

function Private({ children }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Private><Dashboard /></Private>} />
      <Route path="/entradas" element={<Private><Entradas /></Private>} />
      <Route path="/espacios" element={<Private><Espacios /></Private>} />
      <Route path="/vehiculos" element={<Private><Vehiculos /></Private>} />
      <Route path="/tarifas" element={<Private><Tarifas /></Private>} />
      <Route path="/mensualidades" element={<Private><Mensualidades /></Private>} />
      <Route path="/contabilidad" element={<Private><Contabilidad /></Private>} />
      <Route path="/reportes" element={<Private><Reportes /></Private>} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
""")

add("frontend/src/components/Layout.jsx", """import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { LayoutDashboard, Car, MapPin, Users, DollarSign, Calendar, Wallet, BarChart3, LogOut } from 'lucide-react'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/entradas', label: 'Entradas/Salidas', icon: Car },
  { to: '/espacios', label: 'Espacios', icon: MapPin },
  { to: '/vehiculos', label: 'Vehículos', icon: Users },
  { to: '/tarifas', label: 'Tarifas', icon: DollarSign },
  { to: '/mensualidades', label: 'Mensualidades', icon: Calendar },
  { to: '/contabilidad', label: 'Contabilidad', icon: Wallet },
  { to: '/reportes', label: 'Reportes', icon: BarChart3 },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-slate-900 text-white flex flex-col">
        <div className="p-5 border-b border-slate-700">
          <h1 className="text-xl font-bold">🅿️ Parqueadero</h1>
          <p className="text-xs text-slate-400 mt-1">{user?.nombre} · {user?.rol}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                }`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <button onClick={() => { logout(); nav('/login') }}
          className="flex items-center gap-2 px-5 py-3 text-sm text-slate-400 hover:text-white border-t border-slate-700">
          <LogOut size={16} /> Cerrar sesión
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
""")

add("frontend/src/pages/Login.jsx", """import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../auth'

export default function Login() {
  const [email, setEmail] = useState('admin@parqueadero.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const nav = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post('/auth/login', form)
      login(data)
      nav('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error de login')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <form onSubmit={submit} className="bg-white p-8 rounded-xl shadow-xl w-96">
        <h1 className="text-2xl font-bold text-center mb-1">🅿️ Parqueadero</h1>
        <p className="text-center text-slate-500 text-sm mb-6">Ingresa a tu cuenta</p>
        {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-3 text-sm">{error}</div>}
        <label className="block text-sm mb-1">Email</label>
        <input className="input mb-3" value={email} onChange={e => setEmail(e.target.value)} />
        <label className="block text-sm mb-1">Contraseña</label>
        <input type="password" className="input mb-4" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="btn btn-primary w-full">Ingresar</button>
        <p className="text-xs text-slate-400 text-center mt-4">
          Demo: admin@parqueadero.com / admin123
        </p>
      </form>
    </div>
  )
}
""")

add("frontend/src/pages/Dashboard.jsx", """import { useEffect, useState } from 'react'
import api from '../api'
import { Car, MapPin, Users, Calendar, DollarSign } from 'lucide-react'

function Stat({ label, value, icon: Icon, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}><Icon size={22} /></div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { api.get('/reportes/dashboard').then(r => setStats(r.data)) }, [])

  if (!stats) return <div>Cargando...</div>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Stat label="Espacios Totales" value={stats.espacios_total} icon={MapPin} color="bg-blue-100 text-blue-700" />
        <Stat label="Espacios Libres" value={stats.espacios_libres} icon={MapPin} color="bg-green-100 text-green-700" />
        <Stat label="Espacios Ocupados" value={stats.espacios_ocupados} icon={MapPin} color="bg-orange-100 text-orange-700" />
        <Stat label="Vehículos Dentro" value={stats.vehiculos_dentro} icon={Car} color="bg-purple-100 text-purple-700" />
        <Stat label="Mensualidades Activas" value={stats.mensualidades_activas} icon={Calendar} color="bg-cyan-100 text-cyan-700" />
        <Stat label="Ingresos Hoy" value={`$${stats.ingresos_hoy.toLocaleString()}`} icon={DollarSign} color="bg-emerald-100 text-emerald-700" />
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Entradas.jsx", """import { useEffect, useState } from 'react'
import api from '../api'
import { Plus, LogOut } from 'lucide-react'

export default function Entradas() {
  const [activas, setActivas] = useState([])
  const [form, setForm] = useState({ placa: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/entradas/activas').then(r => setActivas(r.data))
  useEffect(() => { cargar() }, [])

  async function entrada(e) {
    e.preventDefault()
    setMsg('')
    try {
      await api.post('/entradas/entrada', form)
      setForm({ placa: '', tipo_vehiculo: 'carro' })
      cargar()
      setMsg('✅ Entrada registrada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  async function salida(id) {
    try {
      const calc = await api.get(`/entradas/calcular/${id}`)
      const valor = calc.data.valor
      if (!confirm(`Cobrar $${valor}?`)) return
      const { data } = await api.post(`/entradas/salida/${id}`, { metodo_pago: 'efectivo' })
      setMsg(`✅ Salida: ${data.placa} - $${data.valor} (cambio: $${data.cambio})`)
      cargar()
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Entradas / Salidas</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={entrada} className="card mb-5 flex gap-3 items-end flex-wrap">
        <div>
          <label className="text-sm">Placa</label>
          <input className="input" value={form.placa} required
            onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        </div>
        <div>
          <label className="text-sm">Tipo</label>
          <select className="input" value={form.tipo_vehiculo}
            onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
            <option value="carro">Carro</option>
            <option value="moto">Moto</option>
            <option value="bici">Bicicleta</option>
          </select>
        </div>
        <button className="btn btn-primary flex items-center gap-2"><Plus size={16} /> Registrar Entrada</button>
      </form>

      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-3">Vehículos dentro ({activas.length})</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Ticket</th><th>Placa</th><th>Tipo</th><th>Espacio</th><th>Entrada</th><th></th></tr>
          </thead>
          <tbody>
            {activas.map(o => (
              <tr key={o.id} className="border-b hover:bg-slate-50">
                <td className="py-2">#{o.id}</td>
                <td className="font-bold text-slate-800">{o.placa || `#${o.vehiculo_id}`}</td>
                <td><span className="uppercase text-xs font-semibold px-2 py-0.5 bg-slate-100 rounded text-slate-700">{o.tipo_vehiculo || '-'}</span></td>
                <td><span className="px-2 py-0.5 bg-blue-50 text-blue-700 font-medium rounded text-xs">{o.espacio_codigo || (o.espacio_id ? `#${o.espacio_id}` : '-')}</span></td>
                <td>{new Date(o.hora_entrada).toLocaleString()}</td>
                <td>
                  <button onClick={() => salida(o.id)} className="btn btn-danger text-xs flex items-center gap-1">
                    <LogOut size={12} /> Salida
                  </button>
                </td>
              </tr>
            ))}
            {!activas.length && <tr><td colSpan="6" className="py-6 text-center text-slate-400">Sin vehículos dentro</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Espacios.jsx", """import { useEffect, useState } from 'react'
import api from '../api'
import { Trash2 } from 'lucide-react'

export default function Espacios() {
  const [esp, setEsp] = useState([])
  const [form, setForm] = useState({ codigo: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/espacios/').then(r => setEsp(r.data))
  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/espacios/', form)
      setForm({ codigo: '', tipo_vehiculo: 'carro' })
      cargar()
      setMsg('✅ Espacio creado')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  async function eliminar(id, codigo) {
    if (!confirm(`¿Estás seguro de eliminar el espacio "${codigo}"?`)) return
    try {
      await api.delete(`/espacios/${id}`)
      cargar()
      setMsg(`✅ Espacio "${codigo}" eliminado`)
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'Error al eliminar'))
    }
  }

  const color = (e) => e.estado === 'libre' ? 'bg-green-100 border-green-400 text-green-700'
    : e.estado === 'ocupado' ? 'bg-red-100 border-red-400 text-red-700'
    : 'bg-slate-100 border-slate-400 text-slate-700'

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Espacios</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 flex gap-3 items-end flex-wrap">
        <div>
          <label className="text-sm">Código</label>
          <input className="input" required value={form.codigo}
            onChange={e => setForm({ ...form, codigo: e.target.value.toUpperCase() })} />
        </div>
        <div>
          <label className="text-sm">Tipo</label>
          <select className="input" value={form.tipo_vehiculo}
            onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
            <option value="carro">Carro</option>
            <option value="moto">Moto</option>
            <option value="bici">Bicicleta</option>
          </select>
        </div>
        <button className="btn btn-primary">Agregar</button>
      </form>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {esp.map(e => (
          <div key={e.id} className={`relative border-2 rounded-lg p-3 text-center ${color(e)}`}>
            <button
              type="button"
              onClick={() => eliminar(e.id, e.codigo)}
              disabled={e.estado === 'ocupado'}
              title={e.estado === 'ocupado' ? 'No se puede eliminar un espacio ocupado' : 'Eliminar espacio'}
              className={`absolute top-2 right-2 p-1 rounded-md transition ${
                e.estado === 'ocupado'
                  ? 'opacity-20 cursor-not-allowed text-slate-400'
                  : 'text-slate-400 hover:text-red-600 hover:bg-white/80'
              }`}
            >
              <Trash2 size={15} />
            </button>
            <p className="font-bold text-lg">{e.codigo}</p>
            <p className="text-xs uppercase">{e.tipo_vehiculo}</p>
            <p className="text-xs mt-1 capitalize">{e.estado}</p>
          </div>
        ))}
        {!esp.length && (
          <div className="col-span-full py-8 text-center text-slate-400">
            Sin espacios registrados. Agrega uno usando el formulario superior.
          </div>
        )}
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Vehiculos.jsx", """import { useEffect, useState } from 'react'
import api from '../api'

export default function Vehiculos() {
  const [vs, setVs] = useState([])
  const [q, setQ] = useState('')
  const [form, setForm] = useState({ placa: '', tipo: 'carro', marca: '', color: '', propietario: '', telefono: '' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get(`/vehiculos/?${q ? `q=${q}` : ''}`).then(r => setVs(r.data))
  useEffect(() => { cargar() }, [q])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/vehiculos/', form)
      setForm({ placa: '', tipo: 'carro', marca: '', color: '', propietario: '', telefono: '' })
      cargar()
      setMsg('✅ Vehículo registrado')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Vehículos</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-3 gap-3">
        <input className="input" placeholder="Placa" required value={form.placa}
          onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
          <option value="carro">Carro</option><option value="moto">Moto</option><option value="bici">Bicicleta</option>
        </select>
        <input className="input" placeholder="Marca" value={form.marca} onChange={e => setForm({ ...form, marca: e.target.value })} />
        <input className="input" placeholder="Color" value={form.color} onChange={e => setForm({ ...form, color: e.target.value })} />
        <input className="input" placeholder="Propietario" value={form.propietario} onChange={e => setForm({ ...form, propietario: e.target.value })} />
        <input className="input" placeholder="Teléfono" value={form.telefono} onChange={e => setForm({ ...form, telefono: e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-3">Agregar vehículo</button>
      </form>

      <div className="card">
        <input className="input mb-3" placeholder="Buscar por placa..." value={q} onChange={e => setQ(e.target.value)} />
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Placa</th><th>Tipo</th><th>Marca</th><th>Color</th><th>Propietario</th></tr>
          </thead>
          <tbody>
            {vs.map(v => (
              <tr key={v.id} className="border-b">
                <td className="py-2 font-bold">{v.placa}</td>
                <td>{v.tipo}</td><td>{v.marca || '-'}</td><td>{v.color || '-'}</td><td>{v.propietario || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Tarifas.jsx", """import { useEffect, useState } from 'react'
import api from '../api'

export default function Tarifas() {
  const [ts, setTs] = useState([])
  const [form, setForm] = useState({ nombre: '', tipo_vehiculo: 'carro', valor_hora: 0, valor_fraccion: 0, minutos_fraccion: 15, valor_dia: 0 })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/tarifas/').then(r => setTs(r.data))
  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/tarifas/', form)
      cargar()
      setMsg('✅ Tarifa creada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Tarifas</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-3 gap-3">
        <input className="input" placeholder="Nombre" required value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} />
        <select className="input" value={form.tipo_vehiculo} onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
          <option value="carro">Carro</option><option value="moto">Moto</option><option value="bici">Bicicleta</option>
        </select>
        <input className="input" type="number" placeholder="Valor hora" value={form.valor_hora} onChange={e => setForm({ ...form, valor_hora: +e.target.value })} />
        <input className="input" type="number" placeholder="Valor fracción" required value={form.valor_fraccion} onChange={e => setForm({ ...form, valor_fraccion: +e.target.value })} />
        <input className="input" type="number" placeholder="Minutos fracción" value={form.minutos_fraccion} onChange={e => setForm({ ...form, minutos_fraccion: +e.target.value })} />
        <input className="input" type="number" placeholder="Valor día" required value={form.valor_dia} onChange={e => setForm({ ...form, valor_dia: +e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-3">Crear tarifa</button>
      </form>

      <div className="card">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Tipo</th><th>Nombre</th><th>Hora</th><th>Fracción</th><th>Día</th><th>Activa</th></tr>
          </thead>
          <tbody>
            {ts.map(t => (
              <tr key={t.id} className="border-b">
                <td className="py-2 font-bold uppercase">{t.tipo_vehiculo}</td>
                <td>{t.nombre}</td><td>${t.valor_hora}</td>
                <td>${t.valor_fraccion}/{t.minutos_fraccion}min</td>
                <td>${t.valor_dia}</td>
                <td>{t.activa ? '✅' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Mensualidades.jsx", """import { useEffect, useState } from 'react'
import api from '../api'

export default function Mensualidades() {
  const [ms, setMs] = useState([])
  const [form, setForm] = useState({ placa: '', tipo_vehiculo: 'carro', fecha_inicio: '', fecha_fin: '', valor: '' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/mensualidades/').then(r => setMs(r.data))
  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/mensualidades/', { ...form, valor: +form.valor })
      setForm({ placa: '', tipo_vehiculo: 'carro', fecha_inicio: '', fecha_fin: '', valor: '' })
      cargar()
      setMsg('✅ Mensualidad creada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Mensualidades</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-5 gap-3">
        <input className="input" placeholder="Placa (ej. ABC123)" required value={form.placa}
          onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        <select className="input" value={form.tipo_vehiculo} onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
          <option value="carro">Carro</option>
          <option value="moto">Moto</option>
          <option value="bici">Bicicleta</option>
        </select>
        <input className="input" type="date" required value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} />
        <input className="input" type="date" required value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} />
        <input className="input" type="number" placeholder="Valor" required value={form.valor} onChange={e => setForm({ ...form, valor: e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-5">Crear mensualidad</button>
      </form>

      <div className="card">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">ID</th><th>Placa</th><th>Inicio</th><th>Fin</th><th>Valor</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {ms.map(m => (
              <tr key={m.id} className="border-b">
                <td className="py-2">#{m.id}</td>
                <td className="font-bold text-slate-800">{m.placa || `#${m.vehiculo_id}`}</td>
                <td>{m.fecha_inicio}</td><td>{m.fecha_fin}</td>
                <td>${(+m.valor).toLocaleString()}</td>
                <td><span className={`px-2 py-1 rounded text-xs ${m.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{m.estado}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Contabilidad.jsx", """import { useEffect, useState } from 'react'
import api from '../api'

const hoy = new Date().toISOString().slice(0, 10)

export default function Contabilidad() {
  const [resumen, setResumen] = useState(null)
  const [movs, setMovs] = useState([])
  const [fecha, setFecha] = useState(hoy)
  const [form, setForm] = useState({ tipo: 'egreso', concepto: '', monto: 0, metodo_pago: 'efectivo' })

  const cargar = async () => {
    const r1 = await api.get(`/contabilidad/resumen?fecha=${fecha}`)
    setResumen(r1.data)
    const r2 = await api.get(`/contabilidad/movimientos?desde=${fecha}&hasta=${fecha}`)
    setMovs(r2.data)
  }
  useEffect(() => { cargar() }, [fecha])

  async function crear(e) {
    e.preventDefault()
    await api.post('/contabilidad/movimientos', { ...form, monto: +form.monto })
    setForm({ tipo: 'egreso', concepto: '', monto: 0, metodo_pago: 'efectivo' })
    cargar()
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Contabilidad</h2>

      <div className="mb-5">
        <label className="text-sm mr-2">Fecha:</label>
        <input type="date" className="input w-auto inline-block" value={fecha} onChange={e => setFecha(e.target.value)} />
      </div>

      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          <div className="card"><p className="text-sm text-slate-500">Ingresos</p><p className="text-xl font-bold text-green-600">${resumen.ingresos.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Egresos</p><p className="text-xl font-bold text-red-600">${resumen.egresos.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Neto</p><p className="text-xl font-bold">${resumen.neto.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Movimientos</p><p className="text-xl font-bold">{resumen.movimientos}</p></div>
        </div>
      )}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
          <option value="ingreso">Ingreso</option><option value="egreso">Egreso</option>
        </select>
        <input className="input" placeholder="Concepto" required value={form.concepto} onChange={e => setForm({ ...form, concepto: e.target.value })} />
        <input className="input" type="number" placeholder="Monto" required value={form.monto} onChange={e => setForm({ ...form, monto: e.target.value })} />
        <select className="input" value={form.metodo_pago} onChange={e => setForm({ ...form, metodo_pago: e.target.value })}>
          <option value="efectivo">Efectivo</option><option value="tarjeta">Tarjeta</option><option value="transferencia">Transferencia</option>
        </select>
        <button className="btn btn-primary col-span-2 md:col-span-4">Registrar movimiento</button>
      </form>

      <div className="card">
        <h3 className="font-semibold mb-3">Movimientos del día</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Hora</th><th>Tipo</th><th>Concepto</th><th>Monto</th><th>Método</th></tr>
          </thead>
          <tbody>
            {movs.map(m => (
              <tr key={m.id} className="border-b">
                <td className="py-2">{new Date(m.fecha).toLocaleTimeString()}</td>
                <td><span className={m.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'}>{m.tipo}</span></td>
                <td>{m.concepto}</td>
                <td>${(+m.monto).toLocaleString()}</td>
                <td>{m.metodo_pago}</td>
              </tr>
            ))}
            {!movs.length && <tr><td colSpan="5" className="py-6 text-center text-slate-400">Sin movimientos</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

add("frontend/src/pages/Reportes.jsx", """import { useEffect, useState } from 'react'
import api from '../api'

const hoy = new Date().toISOString().slice(0, 10)
const hace30 = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)

export default function Reportes() {
  const [desde, setDesde] = useState(hace30)
  const [hasta, setHasta] = useState(hoy)
  const [historial, setHistorial] = useState([])

  useEffect(() => {
    api.get(`/reportes/historial?desde=${desde}&hasta=${hasta}`).then(r => setHistorial(r.data))
  }, [desde, hasta])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Reportes</h2>

      <div className="card mb-5 flex gap-3 items-end flex-wrap">
        <div><label className="text-sm">Desde</label><input type="date" className="input" value={desde} onChange={e => setDesde(e.target.value)} /></div>
        <div><label className="text-sm">Hasta</label><input type="date" className="input" value={hasta} onChange={e => setHasta(e.target.value)} /></div>
      </div>

      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-3">Historial de ocupaciones ({historial.length})</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Placa</th><th>Tipo</th><th>Entrada</th><th>Salida</th><th>Min</th><th>Valor</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {historial.map(h => (
              <tr key={h.id} className="border-b">
                <td className="py-2 font-bold">{h.placa}</td><td>{h.tipo}</td>
                <td>{h.entrada ? new Date(h.entrada).toLocaleString() : '-'}</td>
                <td>{h.salida ? new Date(h.salida).toLocaleString() : '-'}</td>
                <td>{h.minutos ?? '-'}</td><td>${h.valor.toLocaleString()}</td>
                <td>{h.estado}</td>
              </tr>
            ))}
            {!historial.length && <tr><td colSpan="7" className="py-6 text-center text-slate-400">Sin datos</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
""")

# ============================================================
# GENERADOR FINAL
# ============================================================

if __name__ == "__main__":
    import sys
    print(f"📁 Generando proyecto en ./{BASE}/ ...")
    print(f"📄 Total de archivos: {len(FILES)}\n")
    for rel_path, content in FILES.items():
        full_path = BASE / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  ✓ {rel_path}")

    # Copia .env.example a .env si no existe
    env_example = BASE / ".env.example"
    env_file = BASE / ".env"
    if env_example.exists() and not env_file.exists():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"\n  ✓ .env (creado desde .env.example)")

    print("\n" + "=" * 50)
    print("✅ Proyecto generado exitosamente")
    print("=" * 50)
    print(f"\nCarpeta: {BASE.absolute()}\n")
    print("Próximos pasos:\n")
    print(f"  1. cd {BASE}")
    print("  2. docker compose up -d --build")
    print("  3. Abrir: http://localhost:3000")
    print("  4. Login: admin@parqueadero.com / admin123\n")