#!/bin/bash
SERVER_IP="server"
SERVER_PORT="12345"
NETWORK_NAME="tp0_testing_net"


MESSAGE="mensaje_de_prueba_tp0"

RESULT=$(docker run --rm --network $NETWORK_NAME busybox sh -c "echo '$MESSAGE' | nc $SERVER_IP $SERVER_PORT" 2>/dev/null)

if [ "$RESULT" = "$MESSAGE" ]; then
  echo "action: test_echo_server | result: success"
  exit 0
else
  echo "action: test_echo_server | result: fail"
  exit 1
fi
