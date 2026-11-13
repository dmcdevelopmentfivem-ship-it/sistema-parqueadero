from fastapi import FastAPI
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
        # 1. Crear usuario si no existe
        if not db.query(models.Usuario).first():
            db.add(models.Usuario(
                nombre="Administrador",
                email="admin@parqueadero.com",
                password_hash=hash_password("admin123"),
                rol="admin"
            ))
            db.commit()

        # 2. Crear tarifas SIEMPRE y cuando no existan
        if db.query(models.Tarifa).count() == 0:
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