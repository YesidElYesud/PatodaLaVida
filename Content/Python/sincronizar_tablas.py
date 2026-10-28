"""
Descarga las pestañas del Google Sheet "csv Patoda la vida" como CSV y
reimporta las Data Tables del proyecto.

Se ejecuta desde el botón "Actualizar tablas" de la barra del editor
(registrado en init_unreal.py). La hoja debe estar compartida como
"cualquiera con el enlace puede ver".
"""

import csv
import io
import os
import urllib.request

import unreal

SHEET_ID = "1Xh4Hx4zixWtOMaBeKm1Yo8X4kBLF05rwlXSlVY-mxqc"

# Pestaña del Sheet (por gid, así renombrarla no rompe nada) -> Data Table destino.
# La pestaña KeyQuest (gid 1585733246) es documentación y no se importa.
TABLAS = [
    ("Hoja 1", "0", "/Game/DataTable/CSV_PatodaLaVida_DataTable"),
    ("Dialogos", "999829843", "/Game/BP/Dialogo/DialogoDataTable"),
]


def _descargar_csv(gid):
    url = "https://docs.google.com/spreadsheets/d/{}/export?format=csv&gid={}".format(SHEET_ID, gid)
    with urllib.request.urlopen(url, timeout=30) as respuesta:
        datos = respuesta.read()
    # Si la hoja deja de ser pública, Google devuelve la página de login en HTML.
    if datos.lstrip()[:1] == b"<":
        raise RuntimeError("Google devolvió HTML en vez de CSV. ¿La hoja sigue compartida con 'cualquiera con el enlace'?")
    return datos


def _validar_columnas(tabla, datos):
    """Comprueba que el CSV tenga todas las columnas del struct de la tabla."""
    encabezados = next(csv.reader(io.StringIO(datos.decode("utf-8-sig"))), [])
    columnas_csv = set(h.strip() for h in encabezados[1:])
    columnas_tabla = unreal.DataTableFunctionLibrary.get_data_table_column_export_names(tabla)
    faltan = [c for c in columnas_tabla if c not in columnas_csv]
    if faltan:
        raise RuntimeError("Al CSV le faltan columnas de la tabla: {}".format(", ".join(faltan)))


def _sincronizar_tabla(nombre, gid, ruta_tabla, carpeta):
    assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    tabla = assets.load_asset(ruta_tabla)
    if not isinstance(tabla, unreal.DataTable):
        raise RuntimeError("No se encontró la Data Table {}".format(ruta_tabla))

    datos = _descargar_csv(gid)
    _validar_columnas(tabla, datos)

    ruta_csv = os.path.join(carpeta, "{}.csv".format(gid))
    with open(ruta_csv, "wb") as archivo:
        archivo.write(datos)

    if not unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(tabla, ruta_csv):
        raise RuntimeError("Falló la importación del CSV (revisa el Output Log).")
    assets.save_loaded_asset(tabla, only_if_is_dirty=False)

    filas = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(tabla))
    return "{}: {} filas".format(nombre, filas)


def sincronizar():
    carpeta = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "SincronizarTablas")
    os.makedirs(carpeta, exist_ok=True)

    resultados = []
    hubo_error = False
    with unreal.ScopedSlowTask(len(TABLAS), "Actualizando tablas desde Google Sheets...") as tarea:
        tarea.make_dialog()
        for nombre, gid, ruta_tabla in TABLAS:
            tarea.enter_progress_frame(1, "Actualizando {}...".format(nombre))
            try:
                resultados.append("✓ " + _sincronizar_tabla(nombre, gid, ruta_tabla, carpeta))
            except Exception as error:
                hubo_error = True
                resultados.append("✗ {}: {}".format(nombre, error))
                unreal.log_error("[SincronizarTablas] {}: {}".format(nombre, error))

    mensaje = "\n".join(resultados)
    unreal.log("[SincronizarTablas]\n" + mensaje)
    titulo = "Actualizar tablas: con errores" if hubo_error else "Actualizar tablas: listo"
    unreal.EditorDialog.show_message(titulo, mensaje, unreal.AppMsgType.OK)
