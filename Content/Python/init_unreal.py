"""
Unreal ejecuta este archivo al abrir el editor. Registra el botón
"Actualizar tablas" en la barra de herramientas del Level Editor.
"""

import unreal


def _registrar_boton():
    menus = unreal.ToolMenus.get()
    barra = menus.extend_menu("LevelEditor.LevelEditorToolBar.User")

    boton = unreal.ToolMenuEntry(
        name="PatodaLaVida.ActualizarTablas",
        type=unreal.MultiBlockType.TOOL_BAR_BUTTON,
    )
    boton.set_label("Actualizar tablas")
    boton.set_tool_tip("Descarga el Google Sheet y reimporta CSV_PatodaLaVida_DataTable y DialogoDataTable")
    boton.set_icon("EditorStyle", "Icons.Refresh")
    # Recarga el módulo en cada clic para tomar cambios del script sin reiniciar el editor.
    boton.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON,
        "",
        "import importlib, sincronizar_tablas; importlib.reload(sincronizar_tablas); sincronizar_tablas.sincronizar()",
    )

    barra.add_menu_entry("PatodaLaVida", boton)
    menus.refresh_all_widgets()


_registrar_boton()
