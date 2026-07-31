import os
import pandas as pd
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class TicketInfo:
    elemento: str = ""
    numero_ticket: str = ""
    fecha_cierre: str = ""
    dni_cesado: str = ""
    fecha_creacion: str = ""

class TicketInfoService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, TicketInfo] = {}
        self.folder_path = DATA_PATH
      
        self.file_enum: FileName = FileName.TICKETS_CESES

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de tickets configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', dtype=str, encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            if 'CREADO' in df.columns:
                df['CREADO_DT'] = pd.to_datetime(df['CREADO'], errors='coerce')
                df = df.sort_values(by='CREADO_DT', ascending=True)

            for _, row in df.iterrows():
                dni_cesado = str(row.get('NUMERO ID', '')).strip().upper()
                if not dni_cesado or dni_cesado == 'NAN':
                    dni_cesado = str(row.get('INGRESA EL DNI DE LA PERSONA A CESAR', '')).strip().upper()

                if not dni_cesado or dni_cesado == 'NAN': 
                    continue

                self._cache[dni_cesado] = TicketInfo(
                    elemento=str(row.get('ELEMENTO', '')).strip(),
                    numero_ticket=str(row.get('NÚMERO', '')).strip(),
                    fecha_cierre=str(row.get('CERRADO', '')).strip(),
                    dni_cesado=dni_cesado,
                    fecha_creacion=str(row.get('CREADO', '')).strip()
                )

            print(f"Ticket report ({self.file_enum.name}) | Total en cache (únicos más recientes): {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def delete_file(self) -> bool:
        delete_file(self.path_file)
        self._cache.clear()
        return True
    
    def get_by_dni(self, dni: str) -> TicketInfo | None:
        key = str(dni).strip().upper() if dni else ""
        return self._cache.get(key)
    
    def get_all(self) -> list[TicketInfo]:
        return list(self._cache.values())
    