import os
import pandas as pd
from dataclasses import dataclass
from datetime import date
from typing import Optional
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class GDHUserInfo:
    dni: str = ""
    nombre: str = ""
    apellido_paterno: str = ""
    apellido_materno: str = ""
    grupo_personal: str = ""
    esProveedor: bool = False
    cod_funcion: str = ""
    funcion: str = ""
    cod_uni_orga: str = ""
    cod_servicio: str = ""
    u_organizativa: str = ""
    servicio: str = ""
    sociedad: str = ""
    fecha_alta: Optional[date] = None
    fecha_cese: Optional[date] = None
    isActive: bool = False
    isCesado: bool = False
    area_nomina: str = ""
    area_bcp: str = ""
    division_bcp: str = ""
    n_personal: str = ""
    cod_jefe: str = ""
    nombre_jefe: str = ""

    def fullname(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
    
    def calculate_role_type(self) -> str:
        if self.grupo_personal.upper() == "EXTERNO":
            return "Proveedor"
        elif (
            self.grupo_personal.upper() in ["INTERNO-NEGOCIOS RV", "FF VV"]
            and self.area_nomina.upper() in ["ZM-EMPLEADOS", "PV- EMPLEADOS"]
            and self.area_bcp.upper() in [
                "AGENCIAS SALUD",
                "AREA COMERCIAL DE RENTAS",
                "AGENCIAS VIDA LIMA",
                "AGENCIAS VIDA REGIONES",
            ]
            and self.division_bcp.upper() == "DIVISION CANALES DE ASESO"
        ):
            return "FFVV"
        else:
            return "Planilla"
        
    def get_rol(self):
        if self.isActive:
            if self.esProveedor:
                return "Rol AD Externo"
            else:
                if self.calculate_role_type() == "FFVV":
                    return f"R{self.cod_funcion}{self.cod_servicio}"
                return f"R{self.cod_funcion}{self.cod_uni_orga}"
        else:
            return "*Cesado en SAP*"

class GDHUserService():
    def __init__(self, lazy: bool = False):
        self._cache: dict[str, GDHUserInfo] = {}
        self._cache_n_personal: dict[str, GDHUserInfo] = {} 
        self.folder_path = DATA_PATH
        
        self.enum_activos = FileName.ACTIVOS_GDH
        self.enum_cesados = FileName.CESADOS_GDH

        self.path_file_activos = os.path.join(self.folder_path, self.enum_activos.value)
        self.path_file_cesados = os.path.join(self.folder_path, self.enum_cesados.value)
        
        self.path_files_list = [self.path_file_activos, self.path_file_cesados]
        
        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}
        self._cache_n_personal = {}

        faltantes = [f for f in self.path_files_list if not os.path.exists(f)]
        if faltantes:
            print(f"Error: Archivos de GDH no encontrados en el disco: {faltantes}")
            return

        try:
            #df_activos = pd.read_parquet(self.path_file_activos, engine='pyarrow').fillna('')
            df_activos = pd.read_csv(self.path_file_activos, sep=';', dtype=str, encoding='utf-8').fillna('')
            
            df_activos.columns = [str(c).strip().upper() for c in df_activos.columns]

            #df_cesados = pd.read_parquet(self.path_file_cesados, engine='pyarrow').fillna('')
            df_cesados = pd.read_csv(self.path_file_cesados, sep=';', dtype=str, encoding='utf-8').fillna('')
            df_cesados.columns = [str(c).strip().upper() for c in df_cesados.columns]

            for _, row in df_activos.iterrows():
                dni = str(row.get('NÚMERO ID', '')).strip().upper()
                if not dni or dni == 'NAN': 
                    continue
                
                user_info = GDHUserInfo(
                    dni=str(row.get('NÚMERO ID', '')).strip(),
                    nombre=str(row.get('NOMBRES', '')).strip(),
                    apellido_paterno=str(row.get('APELLIDO PATERNO', '')).strip(),
                    apellido_materno=str(row.get('APELLIDO MATERNO', '')).strip(),
                    esProveedor=str(row.get('GRUPO DE PERSONAL', '')).strip().upper() in ["EXTERNO"],
                    grupo_personal=str(row.get('GRUPO DE PERSONAL', '')).strip(),
                    cod_funcion=str(row.get('CÓDIGO FUNCIÓN', '')).strip(),
                    funcion=str(row.get('FUNCIÓN', '')).strip(),
                    cod_uni_orga=str(row.get('CÓDIGO DE UN.ORG.', '')).strip(),
                    cod_servicio=str(row.get('CÓDIGO SERVICIO', '')).strip(),
                    u_organizativa=str(row.get('UNIDAD ORGANIZATIVA', '')).strip(),
                    sociedad=str(row.get('SOCIEDAD', '')).strip(),
                    fecha_alta=to_datetime(str(row.get('FECHA', '')).strip(), "DMA"),
                    fecha_cese=None,
                    isActive=True,
                    isCesado=False,
                    area_nomina=str(row.get('ÁREA DE NÓMINA', '')).strip(),
                    area_bcp=str(row.get('AREA BCP', '')).strip(),
                    division_bcp=str(row.get('DIVISIÓN BCP', '')).strip(),
                    servicio=str(row.get('TEXTO SERVICIO', '')).strip(),
                    n_personal=str(row.get('Nº PERS.', '')).strip(),
                    cod_jefe=str(row.get('CÓDIGO JEFE', '')).strip(),
                    nombre_jefe=str(row.get('NOMBRE DEL JEFE', '')).strip(),
                )

                self._cache[dni] = user_info
                
                n_pers_key = user_info.n_personal.upper()
                if n_pers_key and n_pers_key != 'NAN':
                    self._cache_n_personal[n_pers_key] = user_info

            for _, row in df_cesados.iterrows():
                dni = str(row.get('NÚMERO ID', '')).strip().upper()
                if not dni or dni == 'NAN': 
                    continue

                fecha_cese_val = to_datetime(str(row.get('FECHA', '')).strip(), "DMA")
                n_pers_raw = str(row.get('Nº PERS.', '')).strip()

                if dni in self._cache:
                    user_info = self._cache[dni]
                    user_info.isCesado = True
                    user_info.fecha_cese = fecha_cese_val
                    if not user_info.n_personal and n_pers_raw:
                        user_info.n_personal = n_pers_raw
                else:
                    user_info = GDHUserInfo(
                        dni=str(row.get('NÚMERO ID', '')).strip(),
                        nombre=str(row.get('NOMBRES', '')).strip(),
                        apellido_paterno=str(row.get('APELLIDO PATERNO', '')).strip(),
                        apellido_materno=str(row.get('APELLIDO MATERNO', '')).strip(),
                        esProveedor=str(row.get('GRUPO DE PERSONAL', '')).strip().upper() in ["CESADO-EXTERNO"],
                        grupo_personal=str(row.get('GRUPO DE PERSONAL', '')).strip(),
                        cod_funcion="",
                        cod_uni_orga="",
                        cod_servicio="",
                        fecha_cese=fecha_cese_val,
                        u_organizativa=str(row.get('UNIDAD ORGANIZATIVA', '')).strip(),
                        funcion=str(row.get('FUNCIÓN', '')).strip(),
                        sociedad=str(row.get('SOCIEDAD', '')).strip(),
                        n_personal=n_pers_raw,
                        isCesado=True
                    )
                    self._cache[dni] = user_info

                n_pers_key = user_info.n_personal.upper()
                if n_pers_key and n_pers_key != 'NAN':
                    self._cache_n_personal[n_pers_key] = user_info

            print(f"Usuarios GDH | Activos: {len(df_activos)} ({self.enum_activos.name}), Cesados: {len(df_cesados)} ({self.enum_cesados.name}), Total en cache DNI: {len(self._cache)}, Total en cache N° Personal: {len(self._cache_n_personal)}")

        except Exception as e:
            print(f"Error cargando datos de GDH: {e}")

    def delete_file(self) -> bool:
        for path in self.path_files_list:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                return False
                
        self._cache = {}
        self._cache_n_personal = {}
        return True

    def get_by_dni(self, dni: str) -> GDHUserInfo | None:
        key = str(dni).strip().upper() if dni else ""
        return self._cache.get(key)
    
    def get_by_n_personal(self, n_personal: str) -> GDHUserInfo | None:
        key = str(n_personal).strip().upper() if n_personal else ""
        return self._cache_n_personal.get(key)
    
    def get_all(self) -> list[GDHUserInfo]:
        return list(self._cache.values())