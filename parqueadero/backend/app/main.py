from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from . import models
from .security import hash_password
from .routers import (auth, usuarios, vehiculos, espacios, tarifas,
                      entradas, mensualidades, contabilidad, reportes)

# 1. Crear tablas
print("--> Verificando tablas en la base de datos...")
try:
    Base.metadata.create_all(bind=engine)
    print("--> ✅ Tablas verificadas/creadas.")
except Exception as e:
    print(f"--> ❌ Error creando tablas: {e}")

# 2. Seed de datos iniciales
def seed():
    db = SessionLocal()
    try:
        # Crear usuario
        if not db.query(models.Usuario).first():
            print("--> 👤 Creando usuario admin...")
            db.add(models.Usuario(
                nombre="Administrador",
                email="admin@parqueadero.com",
                password_hash=hash_password("admin123"),
                rol="admin"
            ))
            db.commit()

        # Crear tarifas
        if db.query(models.Tarifa).count() == 0:
            print("--> 💰 Creando tarifas de Bogotá...")
            db.add(models.Tarifa(
                nombre="Tarifa Carro Bogotá", tipo_vehiculo="carro",
                valor_hora=13800, valor_fraccion=230,
                minutos_fraccion=1, valor_dia=40000
            ))
            db.add(models.Tarifa(
                nombre="Tarifa Moto Bogotá", tipo_vehiculo="moto",
                valor_hora=9660, valor_fraccion=161,
                minutos_fraccion=1, valor_dia=28000
            ))
            db.add(models.Tarifa(
                nombre="Tarifa Bici Bogotá", tipo_vehiculo="bici",
                valor_hora=600, valor_fraccion=10,
                minutos_fraccion=1, valor_dia=5000
            ))
            db.commit()
            print("--> ✅ Tarifas creadas con éxito.")
        else:
            print("--> ℹ️ Las tarifas ya existen en la base de datos.")
            
    except Exception as e:
        print(f"--> ❌ Error en el Seed: {e}")
        db.rollback()
    finally:
        db.close()

seed()

# 3. Inicializar la App
app = FastAPI(title="Sistema Parqueadero API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Rutas
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