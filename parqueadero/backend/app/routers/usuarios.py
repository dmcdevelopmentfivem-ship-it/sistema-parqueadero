from fastapi import APIRouter, Depends, HTTPException
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
