import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class RolInfo:
    rol: str = ""
    perfil_rol: str = ""
    tipo_rol: str = ""
    cod_fun: str = ""
    funcion: str = ""
    cod_uo: str = ""
    u_orga: str = ""
    tipo_activo: str = ""
    nombre_activo: str = ""
    descripcion: str = ""
    ticket: str = ""
    modified: datetime = None
    created: datetime = None

class MatrizRolesService():
    def __init__(self, lazy: bool = False):
        self._cache: dict[tuple[str, str, str], RolInfo] = {}

        self._idx_roles_unicos: set[str] = set()
        self._idx_rol_activo: dict[tuple[str, str], list[RolInfo]] = {}
        self._idx_rol_perfil: dict[tuple[str, str], list[RolInfo]] = {}

        self.folder_path = DATA_PATH
        self.file_enum: FileName = FileName.MATRIZ_ROLES
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}
        self._idx_roles_unicos = set()
        self._idx_rol_activo = {}
        self._idx_rol_perfil = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            # df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8', low_memory=False).fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                rol = str(row.get('ROL', '')).strip()
                if not rol or rol == 'NAN':
                    continue

                perfil_rol = str(row.get('PERFIL ROL DEL ACTIVO', '')).strip()
                nombre_activo = str(row.get('NOMBRE DEL ACTIVO', '')).strip()
                tipo_activo = str(row.get('TIPO DE ACTIVO', '')).strip()

                if tipo_activo.upper() == "SEGCEN":
                    perfil_rol = perfil_rol[:6]

                rol_up = rol.upper()
                activo_up = nombre_activo.upper()
                perfil_up = perfil_rol.upper()
                cache_key = (rol_up, activo_up, perfil_up)

                rol_info = RolInfo(
                    rol=rol,
                    perfil_rol=perfil_rol,
                    tipo_rol=str(row.get('TIPO DE ROL', '')).strip(),
                    cod_fun=str(row.get('CODIGO FUNCION', '')).strip(),
                    funcion=str(row.get('FUNCION', '')).strip(),
                    cod_uo=str(row.get('CODIGO UO', '')).strip(),
                    u_orga=str(row.get('UNIDAD ORGANIZATIVA', '')).strip(),
                    tipo_activo=tipo_activo,
                    nombre_activo=nombre_activo,
                    descripcion=str(row.get('DESCRIPCION', '')).strip(),
                    ticket=str(row.get('TICKET', '')).strip(),
                    modified=to_datetime(str(row.get('MODIFIED', '')).strip(), "MDA"),
                    created=to_datetime(str(row.get('CREATED', '')).strip(), "MDA"),
                )

                self._cache[cache_key] = rol_info

                self._idx_roles_unicos.add(rol_up)

                key_rol_activo = (rol_up, activo_up)
                if key_rol_activo not in self._idx_rol_activo:
                    self._idx_rol_activo[key_rol_activo] = []
                self._idx_rol_activo[key_rol_activo].append(rol_info)

                key_rol_perfil = (rol_up, perfil_up)
                if key_rol_perfil not in self._idx_rol_perfil:
                    self._idx_rol_perfil[key_rol_perfil] = []
                self._idx_rol_perfil[key_rol_perfil].append(rol_info)

            print(f"MR Cargada ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def delete_file(self) -> bool:
        delete_file(self.path_file)
        self._cache.clear()
        self._idx_roles_unicos.clear()
        self._idx_rol_activo.clear()
        self._idx_rol_perfil.clear()
        return True
    
    def get_all(self) -> list[RolInfo]:
        return list(self._cache.values())

    def exists_by_rol(self, rol: any) -> bool:
        if not rol:
            return False
        return str(rol).strip().upper() in self._idx_roles_unicos

    def exists_by_rol_and_activo(self, rol: any, nombre_activo: any) -> bool:
        if not rol or not nombre_activo:
            return False
        key = (str(rol).strip().upper(), str(nombre_activo).strip().upper())
        return key in self._idx_rol_activo

    def exists_by_rol_activo_and_perfil(self, rol: any, nombre_activo: any, perfil_rol: any) -> bool:
        if not rol or not nombre_activo or not perfil_rol:
            return False
        cache_key = (str(rol).strip().upper(), str(nombre_activo).strip().upper(), str(perfil_rol).strip().upper())
        return cache_key in self._cache

    def exists_by_rol_and_perfil(self, rol: any, perfil_rol: any) -> bool:
        if not rol or not perfil_rol:
            return False
        key = (str(rol).strip().upper(), str(perfil_rol).strip().upper())
        return key in self._idx_rol_perfil

    def get_by_rol_and_activo(self, rol: any, nombre_activo: any) -> list[RolInfo]:
        if not rol or not nombre_activo:
            return []
        
        key = (str(rol).strip().upper(), str(nombre_activo).strip().upper())
        return self._idx_rol_activo.get(key, [])

    def get_by_rol_and_perfil(self, rol: any, perfil_rol: any) -> list[RolInfo]:
        if not rol or not perfil_rol:
            return []
        
        key = (str(rol).strip().upper(), str(perfil_rol).strip().upper())
        return self._idx_rol_perfil.get(key, [])
    