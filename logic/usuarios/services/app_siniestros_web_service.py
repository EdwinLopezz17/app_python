import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class SiniestrosWebUser:
    acl_entry_name: str = ""
    acl_entry_type: str = ""
    acl_level: str = ""
    isActive: bool = False
    app_name: str = ""

class SiniestrosWebUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], SiniestrosWebUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.SINIESTROS_WEB
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Siniestros Web configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            primer_columna = df.columns[0]

            for _, row in df.iterrows():
                val_primer_col = str(row.get(primer_columna, '')).strip()
                if val_primer_col == '' or val_primer_col.upper() == 'NAN' or 'ACL LOG:' in val_primer_col.upper():
                    break 

                acl_entry_name = str(row.get('ACL ENTRY NAME', '')).strip()
                acl_entry_type = str(row.get('ACL ENTRY TYPE', '')).strip()
                
                if not acl_entry_name: 
                    continue

                cache_key = (acl_entry_name.upper(), acl_entry_type.upper())
                self._cache[cache_key] = SiniestrosWebUser(
                    acl_entry_name=acl_entry_name,
                    acl_entry_type=acl_entry_type,
                    acl_level=str(row.get('ACL LEVEL', '')).strip(),
                    isActive=True,
                    app_name = "Siniestros Web",
                )

            print(f"App Siniestros Web ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[SiniestrosWebUser]:
        return list(self._cache.values())
    