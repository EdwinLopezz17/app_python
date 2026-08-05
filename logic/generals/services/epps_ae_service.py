import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class EPPSAEUser:
    userid: str = ""
    userhost: str = ""
    terminal: str = ""
    logoff_time: str = ""
    obj_name: str = ""
    spare1: str = ""
    ntimestamp: str = ""
    action: str = ""

class EPPSAEService():
    def __init__(self, lazy: bool = False):
        self._cache: list[EPPSAEUser] = []
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.EPPS_AE
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = []

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                userid = str(row.get('USERID', '')).strip()
                if not userid or userid.upper() == 'NAN': 
                    continue

                user_record = EPPSAEUser(
                    userid=userid,
                    userhost=str(row.get('USERHOST', '')).strip(),
                    terminal=str(row.get('TERMINAL', '')).strip(),
                    logoff_time=str(row.get('LOGOFF$TIME', '')).strip(),
                    obj_name=str(row.get('OBJ$NAME', '')).strip(),
                    spare1=str(row.get('SPARE1', '')).strip(),
                    ntimestamp=str(row.get('NTIMESTAMP#', '')).strip(),
                    action=str(row.get('ACTION#', '')).strip(),
                )
                
                self._cache.append(user_record)

            print(f"Usuarios EPPS AE ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[EPPSAEUser]:
        return self._cache
    