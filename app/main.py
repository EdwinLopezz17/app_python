from models.reports.gdh_rows import GDHRows
from logic.usuarios.reports.gdh_report import gdh_report

from models.reports.app_rows import AppRows
from logic.usuarios.reports.app_report import get_app_report

from models.file_names import FileName

print("Iniciando la carga de data esto suele tardar un par de minutos...")

app_rows_report = get_app_report()

for row in app_rows_report:
    print(row.aplicacion)
