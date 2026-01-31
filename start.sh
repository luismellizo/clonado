#!/bin/bash

# Web Cloner Elite - Startup Script

echo "🚀 Iniciando Web Cloner Elite..."

# Detener contenedores previos si existen
echo "🛑 Deteniendo contenedores anteriores..."
docker-compose down

# Construir e iniciar contenedores
echo "🏗️ Construyendo e iniciando servicios..."
docker-compose up --build --remove-orphans

# Nota: Usa Ctrl+C para detener
