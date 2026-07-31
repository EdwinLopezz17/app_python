import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class ContactManagerUser:
    username: str = ""
    rolename: str = ""
    nombre: str = ""
    lastname: str = ""
    secondlastname: str = ""
    roledescription: str = ""
    fecha_creacion: str = ""
    isActive: bool = False
    app_name: str = ""

class ContactManagerUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], ContactManagerUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.CONTACT_MANAGER

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                username = str(row.get('USERNAME', '')).strip().upper()
                if not username or username == 'NAN': 
                    continue

                rolename = str(row.get('ROLENAME', '')).strip()
                
                cache_key = (username, rolename.upper())
                self._cache[cache_key] = ContactManagerUser(
                    username=str(row.get('USERNAME', '')).strip(),
                    rolename=rolename,
                    nombre=str(row.get('NAME', '')).strip(),
                    lastname=str(row.get('LASTNAME', '')).strip(),
                    secondlastname=str(row.get('SECONDLASTNAME', '')).strip(),
                    roledescription=str(row.get('ROLEDESCRIPTION', '')).strip(),
                    fecha_creacion=str(row.get('FECHA_CREACION', '')).strip(),
                    isActive=str(row.get('ESTADO', '')).strip().upper() in ['ACTIVO', '1', "1.0", 'TRUE'],
                    app_name = "Contact Manager"
                )

            print(f"App Contact Manager ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[ContactManagerUser]:
        return list(self._cache.values())