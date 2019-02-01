from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import pydicom
import shutil
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
ARCHIVOS_DIR = BASE_DIR / "archivos"

DATABASE_URL = "sqlite:///./estudios.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Estudio(Base):
    __tablename__ = "estudios"
    id = Column(Integer, primary_key=True, index=True)
    nombre_paciente = Column(String)
    fecha = Column(String)
    fecha_nacimiento = Column(String)
    descripcion = Column(String)
    id_paciente = Column(String)
    institucion = Column(String)
    archivo = Column(String)

Base.metadata.create_all(bind=engine)

os.makedirs(ARCHIVOS_DIR, exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory=str(FRONTEND_DIR))
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, q: str = ""):
    db = SessionLocal()
    if q:
        resultados = db.query(Estudio).filter(Estudio.nombre_paciente.contains(q)).all()
    else:
        resultados = db.query(Estudio).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "estudios": resultados, "q": q})

@app.post("/subir/")
async def subir_dicom(file: UploadFile = File(...)):
    ruta_archivo = ARCHIVOS_DIR / file.filename

    with open(ruta_archivo, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    dicom = pydicom.dcmread(str(ruta_archivo))
    nombre = dicom.get("PatientName", "Desconocido")
    fecha = dicom.get("StudyDate", "Sin fecha")
    nacimiento = dicom.get("PatientBirthDate", "Desconocido")
    descripcion = dicom.get("StudyDescription", "Sin descripción")
    id_paciente = dicom.get("PatientID", "Sin ID")
    institucion = dicom.get("InstitutionName", "Desconocida")

    db = SessionLocal()
    nuevo = Estudio(
        nombre_paciente=str(nombre),
        fecha=str(fecha),
        fecha_nacimiento=str(nacimiento),
        descripcion=str(descripcion),
        id_paciente=str(id_paciente),
        institucion=str(institucion),
        archivo=file.filename
    )
    db.add(nuevo)
    db.commit()
    db.close()

    return {"mensaje": "DICOM subido y procesado correctamente"}