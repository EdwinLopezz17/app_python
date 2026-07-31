import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class SalesforceUser:
    id_federacion: str = ""
    perfil: str = ""
    isActive: bool = False
    ult_login: str = ""
    app_name: str = ""
    
class SalesforceUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], SalesforceUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.SALESFORCE

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Salesforce configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                id_federacion = str(row.get('ID DE FEDERACION', '')).strip()
                if not id_federacion or id_federacion == 'NAN': 
                    continue

                perfil = str(row.get('PERFIL', '')).strip()
                
                cache_key = (id_federacion.upper(), perfil.upper())
                self._cache[cache_key] = SalesforceUser(
                    id_federacion = id_federacion,
                    perfil = perfil,
                    isActive = str(row.get('ACTIVO', '')).strip().upper() in ["VERDADERO", "TRUE", "1", "1.0", "ACTIVO"],
                    ult_login=str(row.get('ULTIMO INICIO DE SESION', '')).strip(),
                    app_name="Salesforce"
                )

            print(f"App Salesforce ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[SalesforceUser]:
        return list(self._cache.values())
    