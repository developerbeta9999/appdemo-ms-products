#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

echo "🚀 Iniciando entorno de desarrollo para appdemo-ms-products..."

# 1. Gestionar el Virtual Env
if [ ! -d "venv" ]; then
    echo "📦 Creando venv..."
    python -m venv venv
fi

# 2. Activar el entorno
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 3. Instalación de dependencias 
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# --- NUEVO PASO: Configuración de Variables de Entorno ---
if [ ! -f ".env" ]; then
    if [ -f ".env.dev" ]; then
        echo "📄 Creando archivo .env desde .env.dev..."
        cp .env.dev .env
    else
        echo "⚠️ Error: No se encontró .env.dev para crear el .env"
        exit 1
    fi
fi

# Exportar variables del .env para la sesión actual del bash
export $(grep -v '^#' .env | xargs)

# 4. Base de Datos
echo "⚙️ Preparando base de datos..."
# Estas líneas ahora usarán el DB_HOST=localhost del .env 
python manage.py makemigrations
python manage.py migrate

# 5. Ejecución del servidor [cite: 4]
echo "🌐 Servicio disponible en http://localhost:8001/products/"
python manage.py runserver 0.0.0.0:8001