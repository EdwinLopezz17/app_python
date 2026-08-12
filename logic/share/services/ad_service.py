import os
import pandas as pd
from datetime import date, datetime
from dataclasses import dataclass
from dotenv import load_dotenv
from logic.share.services.entraid_service import EntraUserService
from models.file_names import FileName
from logic.share.utils import to_datetime

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class ADUserInfo:
    usuario: str = ""
    nombre: str = ""
    correo: str = ""
    rol: str = ""
    isActive: bool = False
    dni: str = ""
    description: str = ""
    fecha_creacion: datetime = None 
    fecha_ult_login: datetime = None 
    fecha_cambio: date = None
    passwordneverexpires: bool = False
    cannotchangepassword: bool = False
    passwordlastset: date = None
    title: str = ""
    department: str = ""
    company: str = ""
    jefe: str = ""
    origen: str = ""
    ultima_actividad_entra: str = ""
    last_activity: datetime = None 

class ADService():
    def __init__(self, lazy: bool = False):
        self._cache: dict[tuple[str, str], ADUserInfo] = {}
        self._cache_email: dict[tuple[str, str], ADUserInfo] = {}
        self._cache_dni: dict[tuple[str, str], ADUserInfo] = {}
        
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.AD_CONSOLIDADO
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        
        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}
        self._cache_email = {}
        self._cache_dni = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [c.strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('SAMACCOUNTNAME', '')).strip().upper()
                if not usuario or usuario == "NAN":
                    continue

                origen = str(row.get('ORIGEN', '')).strip()

                cache_key = (usuario, origen.upper())
                if cache_key in self._cache: continue

                correo_ad = str(row.get('EMAILADDRESS', '')).strip()
                dni_val = str(row.get('FACSIMILETELEPHONENUMBER', '')).strip()

                login_date = to_datetime(row.get('LASTLOGONDATE'), "DMA")

                user_info = ADUserInfo(
                    usuario = str(row.get('SAMACCOUNTNAME', '')).strip(),
                    nombre = str(row.get('DISPLAYNAME', '')).strip(),
                    correo = correo_ad,
                    rol = str(row.get('IPPHONE', '')).strip(),
                    fecha_creacion = to_datetime(row.get('WHENCREATED'), "DMA"),
                    fecha_ult_login = login_date,
                    last_activity = login_date,
                    fecha_cambio = to_datetime(row.get('WHENCHANGED'), "DMA"),
                    dni = dni_val,
                    description = str(row.get('DESCRIPTION', '')).strip(),
                    isActive = str(row.get('ENABLED', '')).strip().upper() in ["TRUE", "1"],
                    passwordneverexpires = str(row.get('PASSWORDNEVEREXPIRES', '')).strip().upper() in ["TRUE", "1", "YES"],
                    cannotchangepassword = str(row.get('CANNOTCHANGEPASSWORD', '')).strip().upper() in ["TRUE", "1", "YES"],
                    passwordlastset = to_datetime(row.get('PASSWORDLASTSET'), "DMA"),
                    title = str(row.get('TITLE', '')).strip(),
                    department = str(row.get('DEPARTMENT', '')).strip(),
                    company = str(row.get('COMPANY', '')).strip(),
                    jefe = str(row.get('STREETADDRESS', '')).strip(),
                    origen = origen,
                )
                self._cache[cache_key] = user_info

                if correo_ad:
                    email_key = (correo_ad.strip().lower(), origen.upper())
                    self._cache_email[email_key] = user_info
                
                if dni_val:
                    dni_key = (dni_val.upper(), origen.upper())
                    self._cache_dni[dni_key] = user_info

            total_pps = len([u for u in self._cache.values() if u.origen == "PPS"])
            total_vida = len([u for u in self._cache.values() if u.origen == "VIDA"])

            print(f"Usuarios AD | PPS: {total_pps} ({self.enum_pps.name}), VIDA: {total_vida} ({self.enum_vida.name}), Total en cache: {len(self._cache)}")
                    
        except Exception as e:
            print(f"Error procesando el archivo {self.path_file}: {e}")

    def delete_file(self) -> bool:
        todos_eliminados = True
        for path in self.path_files_list:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                todos_eliminados = False
                
        self._cache = {}
        self._cache_email = {}
        self._cache_dni = {}
        return todos_eliminados

    def get_all(self) -> list[ADUserInfo]:
        return list(self._cache.values())
    
    def get_by_username_and_origen(self, usuario: any, origen: any) -> ADUserInfo | None:
        if not usuario or not origen:
            return None
        
        user_str = str(usuario).strip().upper()
        origen_str = str(origen).strip().upper()
        
        cache_key = (user_str, origen_str)
        return self._cache.get(cache_key, None)
    
    def get_by_email_and_origen(self, correo: any, origen: any) -> ADUserInfo | None:
        if not correo or not origen:
            return None
        
        correo_str = str(correo).strip().lower()
        origen_str = str(origen).strip().upper()
        
        cache_key = (correo_str, origen_str)
        return self._cache_email.get(cache_key, None)
    
    def get_by_dni_and_origen(self, dni: any, origen: any) -> ADUserInfo | None:
        if not dni or not origen:
            return None
        
        dni_str = str(dni).strip().upper()
        origen_str = str(origen).strip().upper()
        
        cache_key = (dni_str, origen_str)
        return self._cache_dni.get(cache_key, None)

    def sync_last_activity_entra(self, entra_service: EntraUserService) -> None:
        try:
            for user in self._cache.values():
                eu = entra_service.get_by_email(user.correo) if user.correo else None
                if eu is None and user.correo:
                    eu = entra_service.get_by_upn(user.correo)
                
                if eu is None:
                    continue

                user.ultima_actividad_entra = eu.lastActivityDateTime 

                dt_entra = to_datetime(eu.lastActivityDateTime)
                dt_ad = user.fecha_ult_login

                if dt_entra and dt_ad:
                    user.last_activity = max(dt_entra, dt_ad)
                else:
                    user.last_activity = dt_entra or dt_ad

        except Exception as e:
            print(f"Error sincronizando AD con Entra: {e}")
        