#!/bin/bash
# scripts/get-emails.sh
# Script súper simple para extraer emails confirmados

DATA_FILE="data/newsletter-subscribers.json"

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ No se encontró: $DATA_FILE"
    exit 1
fi

# Verificar si jq está instalado
if ! command -v jq &> /dev/null; then
    echo "❌ jq no está instalado. Instálalo con: brew install jq (Mac) o apt install jq (Linux)"
    exit 1
fi

echo "📧 EMAILS CONFIRMADOS:"
echo "====================="

# Extraer solo emails confirmados
jq -r '.[] | select(.confirmed == true) | .email' "$DATA_FILE"

echo "====================="
echo "📊 Total: $(jq '[.[] | select(.confirmed == true)] | length' "$DATA_FILE") confirmados"

# Guardar en archivo
jq -r '.[] | select(.confirmed == true) | .email' "$DATA_FILE" > data/confirmed-emails.txt
echo "💾 Guardado en: data/confirmed-emails.txt"