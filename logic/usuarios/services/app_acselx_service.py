import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class AcselxUser:
    usuario: str = ""
    codcolaborador: str = ""
    nomusrpps: str = ""
    numdoc: str = ""
    isActive: bool = False
    codperfil: str = ""
    stsusrppsaplic: str = ""
    tipousrpps: str = ""
    fechacrea: str = ""
    fecacceso: str = ""
    codaplic: str = ""
    app_name: str = ""
    

class AcselxUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], AcselxUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.ACSELX
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('CODUSRPPS', '')).strip()
                if not usuario or usuario == 'NAN': 
                    continue

                codperfil = str(row.get('CODPERFIL', '')).strip()
                cache_key = (usuario.upper(), codperfil.upper())

                is_active = str(row.get('STSUSRPPSAPLIC', '')).strip().upper() == "ACT"
                is_active = is_active and str(row.get('STSUSRPPS', '')).strip().upper() == "ACT"

                self._cache[cache_key] = AcselxUser(
                    usuario = usuario,
                    codaplic=str(row.get('CODAPLIC', '')).strip(),
                    codcolaborador=str(row.get('CODCOLABORADOR', '')).strip(),
                    nomusrpps=str(row.get('NOMUSRPPS', '')).strip(),
                    numdoc=str(row.get('NUMDOC', '')).strip(),
                    isActive=is_active,
                    codperfil = codperfil,
                    stsusrppsaplic=str(row.get('STSUSRPPSAPLIC', '')).strip(),
                    tipousrpps=str(row.get('TIPOUSRPPS', '')).strip(),
                    fechacrea=str(row.get('FECHACREA', '')).strip(),
                    fecacceso=str(row.get('FECACCESO', '')).strip(),
                    app_name="Acsel/X",
                )

            print(f"App Acselx ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_by_usuario_y_perfil(self, id_usuario: str, cod_perfil: str) -> AcselxUser | None:
        user_key = str(id_usuario).strip().upper() if id_usuario else ""
        profile_key = str(cod_perfil).strip().upper() if cod_perfil else ""
        
        return self._cache.get((user_key, profile_key))
    
    def get_all(self) -> list[AcselxUser]:
        return list(self._cache.values())