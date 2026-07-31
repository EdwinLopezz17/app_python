import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

SOX_APPS_PERMITIDAS = {
    "Administrador de Polizas Grupales",
    "Administrador de Rentas Vitalicias",
    "Asientos Contables de Beneficios No Tradicionales",
    "Administración de Cobranzas",
    "Administración de Intermediarios",
    "Motor de Distribucion de Gastos",
    "Portal de Rentas",
    "Sistema Integral de Beneficios",
    "Sistema de Cálculos Actuariales",
    "Sistema de Productos Másivos",
    "Sistema de Productos Masivos",
    "VG 2.0",
    "Administración del VIAP.",
    "Administrador de NIif17",
    "Portal Desgravamen Digital",
    "Sistema de Requisitos Médicos",
    "personID",
    "Portal de Asesoria Digital",
    "Web Solicitud Digital Vida",
}

@dataclass
class SoxVidaUser:
    app_name: str = ""
    id_usuario: str = ""
    apellido_paterno: str = ""
    apellido_materno: str = ""
    nombres: str = ""
    cod_rol: str = ""
    nombre_rol: str = ""
    isActive: bool = False
    fecha_creacion: str = ""
    fecha_modificacion: str = ""

class SoxVidaUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str, str], SoxVidaUser] = {}

        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.SOX_VIDA

        self._apps_permitidas_upper = {app.strip().upper() for app in SOX_APPS_PERMITIDAS}

        nombre_archivo = self.file_enum.value
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de SOX VIDA configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                id_usuario = str(row.get('IDUSUARIO', '')).strip()
                if not id_usuario or id_usuario == 'NAN': 
                    continue

                app_name = str(row.get('NOMBRE_APLICACION', '')).strip()

                if app_name.upper() not in self._apps_permitidas_upper:
                    continue

                cod_rol = str(row.get('CODIGO_ROL', '')).strip()

                cache_key = (id_usuario.upper(), app_name.upper(), cod_rol.upper())

                self._cache[cache_key] = SoxVidaUser(
                    app_name = app_name,
                    id_usuario = id_usuario,
                    apellido_paterno=str(row.get('APELLIDO_PATERNO', '')).strip(),
                    apellido_materno=str(row.get('APELLIDO_MATERNO', '')).strip(),
                    nombres=str(row.get('NOMBRES', '')).strip(),
                    cod_rol = cod_rol,
                    nombre_rol=str(row.get('NOMBRE_ROL', '')).strip(),
                    isActive=not str(row.get('BLOQUEADO', '')).strip().upper() in ["1", "1.0", "SI", "YES", "TRUE", "BLOQUEADO"],
                    fecha_creacion=str(row.get('AUDITORIA_CREACION', '')).strip(),
                    fecha_modificacion=str(row.get('AUDITORIA_MODIFICACION', '')).strip()
                )

            print(f"Apps SOX VIDA ({self.file_enum.name}) | Total registros en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[SoxVidaUser]:
        return list(self._cache.values())