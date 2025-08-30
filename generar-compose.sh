#!/bin/bash

# Check if both arguments are provided
if [ $# -lt 2 ]; then
  echo "Error: Debe proporcionar el nombre del archivo de salida y la cantidad de clientes."
  echo "Uso: $0 <archivo_salida> <cantidad_clientes>"
  exit 1
fi

# Check if the second argument is a non-negative integer
if ! [[ "$2" =~ ^[0-9]+$ ]]; then
  echo "Error: La cantidad de clientes debe ser un número entero no negativo."
  exit 2
fi

echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"

cat > "$1" <<EOF
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOF

for i in $(seq 1 $2); do
cat >> "$1" <<EOL

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
EOL
done

cat >> "$1" <<EOF

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF