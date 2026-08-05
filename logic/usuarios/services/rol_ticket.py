from datetime import datetime
import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class RolTicket:
    ticket_number: str = ""
    dni_user: str = ""
    assigned_role: str = ""
    requested_role: str = ""
    creation_date: datetime = None
    closure_date: datetime = None


class RolTicketService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, RolTicket] = {}
        self._cache_dni: dict[str, list[RolTicket]] = {} 
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.ROL_TICKET
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}
        self._cache_dni = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de EAS configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                ticket_number = str(row.get('ELEMENTO DE SOLICITUD', '')).strip().upper()
                if not ticket_number or ticket_number == 'NAN': 
                    continue
                
                dni = str(row.get('NÚMERO DE DOCUMENTO', '')).strip()

                ticket = RolTicket(
                    ticket_number=ticket_number,
                    dni_user=dni,
                    assigned_role=str(row.get('ROL ASIGNADO', '')).strip(),
                    requested_role=str(row.get('¿QUÉ ROL SE LE ASIGNARÁ?', '')).strip(),
                    creation_date=to_datetime(str(row.get('CREADO', '')).strip(), "DMA"),
                    closure_date=to_datetime(str(row.get('CERRADO', '')).strip(), "DMA"),
                )

                self._cache[ticket_number] = ticket

                if dni:
                    if dni not in self._cache_dni:
                        self._cache_dni[dni] = []
                    self._cache_dni[dni].append(ticket)

            for dni in self._cache_dni:
                self._cache_dni[dni].sort(
                    key=lambda x: x.closure_date if x.closure_date else datetime.min, 
                    reverse=True
                )

            print(f"Ticket Rol ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[RolTicket]:
        return list(self._cache.values())

    def get_by_dni(self, dni: str) -> RolTicket | None:
        if not dni:
            return None
        tickets = self._cache_dni.get(str(dni).strip())
        
        if tickets:
            return tickets[0] 
            
        return None
    