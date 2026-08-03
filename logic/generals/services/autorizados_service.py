import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class AutorizedUser:
    correo: str = ""
    nombre: str = ""
    equipo_chapter: str = ""
    empresa: str = ""
    jefe_chapter_lead: str = ""
    usuario_red: str = ""
    db_epps_uc: str = ""
    db_dbprodn_uc: str = ""
    db_igwprd_uc: str = ""
    db_oweb_uc: str = ""
    db_odw1_uc: str = ""
    db_dbprodn2_ae: str = ""
    db_igwprd_ae: str = ""
    db_epps_ae: str = ""
    db_igwprd_ac: str = ""
    db_epps_ac: str = ""

class AutorizedUserService():
    def __init__(self, lazy: bool = False):
        self._cache: dict[str, AutorizedUser] = {}
        self._cache_by_red: dict[str, AutorizedUser] = {}
        
        self.folder_path = DATA_PATH
        self.file_enum: FileName = FileName.USUARIOS_AUTORIZADOS
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}
        self._cache_by_red = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Prophet configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                correo = str(row.get('CORREO', '')).strip()
                if not correo or correo == 'NAN': 
                    continue

                usuario = AutorizedUser(
                    correo=correo,
                    nombre=str(row.get('NOMBRES Y APELLIDOS', '')).strip(),
                    equipo_chapter=str(row.get('EQUIPO / CHAPTER', '')).strip(),
                    empresa=str(row.get('EMPRESA', '')).strip(),
                    jefe_chapter_lead=str(row.get('JEFE / CHAPTER LEAD', '')).strip(),
                    usuario_red=str(row.get('USUARIO DE RED', '')).strip(),
                    db_epps_uc=str(row.get('BD EPPS UC', '')).strip(),
                    db_dbprodn_uc=str(row.get('BD DBPRODN UC', '')).strip(),
                    db_igwprd_uc=str(row.get('BD IGWPRD UC', '')).strip(),
                    db_oweb_uc=str(row.get('BD OWEB UC', '')).strip(),
                    db_odw1_uc=str(row.get('BD ODW1 UC', '')).strip(),
                    db_dbprodn2_ae=str(row.get('BD DBPRODN2 AE', '')).strip(),
                    db_igwprd_ae=str(row.get('BD IGWPRD  AE', '')).strip(),
                    db_epps_ae=str(row.get('BD EPPS  AE', '')).strip(),
                    db_igwprd_ac=str(row.get('BD IGWPRD AC', '')).strip(),
                    db_epps_ac=str(row.get('BD EPPS  AC', '')).strip(),
                )
                self._cache[correo.upper()] = usuario

                u_red_key = usuario.usuario_red.strip().upper()
                if u_red_key:
                    self._cache_by_red[u_red_key] = usuario

            print(f"Usuarios Autorizados ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[AutorizedUser]:
        return list(self._cache.values())

    def get_by_usuario_red(self, usuario_red: str) -> AutorizedUser | None:
        if not usuario_red:
            return None
    
        return self._cache_by_red.get(usuario_red.strip().upper())
    
    def exists_by_db_epps_ac(self, db_epps_ac: str) -> bool:
        if not db_epps_ac:
            return False
        
        db_epps_ac_key = db_epps_ac.strip().upper()
        for usuario in self._cache.values():
            if usuario.db_epps_ac.strip().upper() == db_epps_ac_key:
                return True
        return False
    
    def exists_by_db_epps_ae(self, db_epps_ae: str) -> bool:
        if not db_epps_ae:
            return False
        
        db_epps_ae_key = db_epps_ae.strip().upper()
        for usuario in self._cache.values():
            if usuario.db_epps_ae.strip().upper() == db_epps_ae_key:
                return True
        return False
    
    def exists_by_db_igwprd_ac(self, db_igwprd_ac: str) -> bool:
        if not db_igwprd_ac:
            return False
        
        db_igwprd_ac_key = db_igwprd_ac.strip().upper()
        for usuario in self._cache.values():
            if usuario.db_igwprd_ac.strip().upper() == db_igwprd_ac_key:
                return True
        return False

    def exists_by_db_igwprd_ae(self, db_igwprd_ae: str) -> bool:
        if not db_igwprd_ae:
            return False

        db_igwprd_ae_key = db_igwprd_ae.strip().upper()
        for usuario in self._cache.values():
            if usuario.db_igwprd_ae.strip().upper() == db_igwprd_ae_key:
                return True
        return False