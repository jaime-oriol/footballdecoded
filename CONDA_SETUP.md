# Guía de Configuración y Uso de Conda

## ¿Qué es Conda?

Conda es un gestor de paquetes y entornos que permite:
- Crear entornos aislados por proyecto
- Gestionar dependencias de Python y paquetes del sistema
- Reproducir entornos en diferentes máquinas
- Evitar conflictos entre versiones de librerías

## Instalación de Anaconda en WSL2

### Paso 1: Descargar Anaconda

```bash
# Ir al directorio home
cd ~

# Descargar el instalador de Anaconda (última versión para Linux)
wget https://repo.anaconda.com/archive/Anaconda3-2024.02-1-Linux-x86_64.sh

# Verificar la integridad del archivo (opcional pero recomendado)
sha256sum Anaconda3-2024.02-1-Linux-x86_64.sh
```

### Paso 2: Ejecutar el instalador

```bash
# Hacer el script ejecutable
chmod +x Anaconda3-2024.02-1-Linux-x86_64.sh

# Ejecutar instalador
bash Anaconda3-2024.02-1-Linux-x86_64.sh

# Durante la instalación:
# 1. Presiona ENTER para continuar
# 2. Lee la licencia (presiona SPACE para avanzar)
# 3. Escribe 'yes' para aceptar
# 4. Presiona ENTER para instalar en la ubicación por defecto (~\anaconda3)
# 5. Escribe 'yes' cuando pregunte si quiere inicializar Anaconda
```

### Paso 3: Activar Conda

```bash
# Recargar la configuración del shell
source ~/.bashrc

# Verificar instalación
conda --version
conda list
```

### Paso 4: Configuración inicial (opcional pero recomendado)

```bash
# Evitar que conda se active automáticamente en cada terminal
conda config --set auto_activate_base false

# Usar canal conda-forge por defecto (más paquetes y actualizaciones)
conda config --add channels conda-forge
conda config --set channel_priority strict

# Actualizar conda
conda update -n base -c defaults conda
```

## Uso del Entorno FootballDecoded

### Crear el entorno desde environment.yml

```bash
# Navegar al directorio del proyecto
cd /home/jaime/FD/data

# Crear el entorno (primera vez, tarda varios minutos)
conda env create -f environment.yml

# El nombre del entorno es 'footballdecoded' (definido en environment.yml)
```

### Activar/Desactivar el entorno

```bash
# Activar el entorno
conda activate footballdecoded

# Tu prompt cambiará a algo como:
# (footballdecoded) user@machine:~$

# Trabajar en tu proyecto...

# Desactivar cuando termines
conda deactivate
```

### Verificar el entorno

```bash
# Con el entorno activado, verificar paquetes instalados
conda list

# Ver información del entorno
conda info

# Ver todos los entornos disponibles
conda env list
```

## Comandos Esenciales de Conda

### Gestión de entornos

```bash
# Crear entorno nuevo (manualmente)
conda create -n nombre_entorno python=3.11

# Crear desde archivo
conda env create -f environment.yml

# Activar entorno
conda activate nombre_entorno

# Desactivar entorno actual
conda deactivate

# Listar todos los entornos
conda env list

# Eliminar un entorno
conda env remove -n nombre_entorno

# Exportar entorno actual
conda env export > environment_backup.yml

# Clonar un entorno
conda create --name nuevo_entorno --clone entorno_existente
```

### Gestión de paquetes

```bash
# Instalar paquete
conda install nombre_paquete

# Instalar versión específica
conda install nombre_paquete=1.2.3

# Instalar desde canal específico
conda install -c conda-forge nombre_paquete

# Instalar múltiples paquetes
conda install paquete1 paquete2 paquete3

# Actualizar paquete
conda update nombre_paquete

# Actualizar todos los paquetes
conda update --all

# Desinstalar paquete
conda remove nombre_paquete

# Buscar paquetes disponibles
conda search nombre_paquete

# Listar paquetes instalados
conda list

# Listar paquetes que coinciden con patrón
conda list nombre*
```

### Uso con pip dentro de Conda

```bash
# Activar el entorno primero
conda activate footballdecoded

# Instalar con pip (para paquetes no disponibles en conda)
pip install nombre_paquete

# IMPORTANTE: Siempre preferir conda install cuando sea posible
# Solo usar pip para paquetes que no existan en conda
```

### Información y limpieza

```bash
# Ver información del entorno actual
conda info

# Ver configuración
conda config --show

# Limpiar paquetes no usados (libera espacio)
conda clean --all

# Ver espacio usado por conda
du -sh ~/anaconda3
```

## Workflow Diario de Trabajo

### Inicio de sesión

```bash
# 1. Abrir terminal WSL2

# 2. Navegar al proyecto
cd /home/jaime/FD/data

# 3. Activar el entorno
conda activate footballdecoded

# 4. Verificar que estás en el entorno correcto
# Tu prompt debe mostrar: (footballdecoded)

# 5. Trabajar normalmente
jupyter notebook  # o cualquier comando de tu proyecto
python database/data_loader.py
```

### Actualizar dependencias

```bash
# Si añades nuevos paquetes al environment.yml:

# 1. Actualizar el entorno existente
conda env update -f environment.yml --prune

# --prune elimina paquetes que ya no están en environment.yml

# 2. Verificar cambios
conda list
```

### Compartir entorno con otros

```bash
# Exportar el entorno actual exacto
conda env export --no-builds > environment_exact.yml

# Este archivo incluye todas las versiones específicas
# Útil para reproducción exacta en otra máquina
```

## Solución de Problemas Comunes

### Problema: "conda: command not found"

```bash
# Solución 1: Recargar bash
source ~/.bashrc

# Solución 2: Inicializar conda manualmente
source ~/anaconda3/bin/activate

# Solución 3: Añadir conda al PATH manualmente
export PATH="$HOME/anaconda3/bin:$PATH"
```

### Problema: "EnvironmentNotWritableError"

```bash
# El entorno base está protegido, usa tu entorno:
conda activate footballdecoded
# Luego instala paquetes
```

### Problema: Conflictos de dependencias

```bash
# Opción 1: Crear entorno limpio
conda env remove -n footballdecoded
conda env create -f environment.yml

# Opción 2: Usar mamba (más rápido en resolver dependencias)
conda install -n base -c conda-forge mamba
mamba env create -f environment.yml
```

### Problema: Instalación muy lenta

```bash
# Usar mamba en lugar de conda (mucho más rápido)
conda install -n base -c conda-forge mamba
mamba install nombre_paquete
```

### Problema: Jupyter no encuentra el kernel

```bash
# Activar entorno
conda activate footballdecoded

# Instalar kernel de Jupyter
python -m ipykernel install --user --name=footballdecoded --display-name "Python (FootballDecoded)"

# Reiniciar Jupyter y seleccionar el kernel "Python (FootballDecoded)"
```

### Problema: VSCode no detecta el entorno

```bash
# 1. Abrir Command Palette (Ctrl+Shift+P)
# 2. Buscar "Python: Select Interpreter"
# 3. Seleccionar el intérprete de ~/anaconda3/envs/footballdecoded/bin/python

# O configurar manualmente en .vscode/settings.json:
{
  "python.defaultInterpreterPath": "~/anaconda3/envs/footballdecoded/bin/python"
}
```

## Comparación Poetry vs Conda

| Aspecto | Poetry | Conda |
|---------|--------|-------|
| **Propósito** | Gestión de paquetes Python | Gestión de paquetes y entornos multiplataforma |
| **Alcance** | Solo Python | Python + paquetes del sistema (C, Fortran, etc.) |
| **Velocidad** | Resolución lenta | Resolución más rápida (especialmente con mamba) |
| **Archivos** | pyproject.toml + poetry.lock | environment.yml |
| **Instalación** | `poetry install` | `conda env create` |
| **Activación** | Automática en virtualenv | `conda activate nombre` |
| **Añadir paquete** | `poetry add paquete` | `conda install paquete` |
| **Actualizar** | `poetry update` | `conda update paquete` |
| **Exportar** | `poetry export` | `conda env export` |
| **Build/Publish** | Nativo | Requiere herramientas adicionales |

## Comandos Rápidos (Cheatsheet)

```bash
# GESTIÓN DE ENTORNOS
conda env list                    # Listar entornos
conda activate nombre             # Activar entorno
conda deactivate                  # Desactivar entorno
conda create -n nombre python=3.11  # Crear entorno
conda env remove -n nombre        # Eliminar entorno

# PAQUETES
conda install paquete            # Instalar paquete
conda update paquete             # Actualizar paquete
conda remove paquete             # Desinstalar paquete
conda list                       # Listar instalados
conda search paquete             # Buscar paquete

# ARCHIVO ENVIRONMENT.YML
conda env create -f environment.yml      # Crear desde archivo
conda env update -f environment.yml      # Actualizar desde archivo
conda env export > environment.yml       # Exportar a archivo

# INFORMACIÓN
conda info                       # Info del sistema
conda config --show              # Ver configuración

# LIMPIEZA
conda clean --all                # Limpiar caches y paquetes no usados
```

## Recursos Adicionales

- [Documentación oficial de Conda](https://docs.conda.io/)
- [Conda Cheat Sheet](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html)
- [Anaconda Package List](https://docs.anaconda.com/anaconda/packages/pkg-docs/)
- [Conda-Forge Channel](https://conda-forge.org/)

## Notas Importantes

1. **Siempre activa el entorno antes de trabajar**: `conda activate footballdecoded`
2. **Usa conda install preferentemente**: Solo recurre a pip si el paquete no existe en conda
3. **Actualiza environment.yml**: Cuando añadas paquetes manualmente, actualiza el archivo
4. **No mezcles pip y conda innecesariamente**: Puede causar conflictos
5. **Usa mamba para operaciones lentas**: Es mucho más rápido que conda para resolver dependencias
6. **Exporta entornos periódicamente**: Útil como backup
