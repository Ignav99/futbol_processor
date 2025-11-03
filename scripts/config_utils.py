"""
Utilidades de configuración compartidas por todos los scripts
"""
from pathlib import Path


def obtener_carpeta_configuracion():
    """
    Busca la carpeta de configuración en dos ubicaciones (en orden de prioridad):
    1. {proyecto}/futbol_calibracion (preferido - dentro del proyecto en Drive)
    2. ~/futbol_calibracion (fallback - carpeta home)

    Ventajas de usar carpeta del proyecto:
    - Configuraciones sincronizadas con Google Drive
    - Backup automático
    - Portable (puedes mover el proyecto y las configs van con él)
    """
    # Obtener directorio del proyecto (parent del directorio scripts)
    script_dir = Path(__file__).parent.parent
    project_config = script_dir / "futbol_calibracion"
    home_config = Path.home() / "futbol_calibracion"

    # Preferir carpeta del proyecto si existe
    if project_config.exists():
        return project_config
    elif home_config.exists():
        return home_config
    else:
        # Crear en el proyecto (preferido por defecto)
        project_config.mkdir(exist_ok=True, parents=True)
        return project_config
