import socket
import logging
import signal
from common.client_handler import ClientHandler
from typing import Dict, List

from common.communication import Communication, EnvioBatchMessage, Message, MessageType, SolicitudGanadoresMessage
from common.utils import has_won, load_bets, store_bets, Bet
import traceback

class Server:
    def __init__(self, port, listen_backlog, client_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._current_client_communication = None
        self._stopped = False

        self._client_handlers: List[ClientHandler] = []  # lista de ClientHandler activos

        self._agencias_totales = client_amount
        self._agencias_que_completaron_envio = set()

        self._sorteo_realizado = False
        self._dnis_ganadores_por_agencia: Dict[int, List[int]] = dict()

        signal.signal(signal.SIGTERM, self.__stop_server)

    def __stop_server(self, signum, frame):
        # Parar loop
        logging.info("action: stop_server | result: in_progress")
        self._stopped = True

        # Cerrar socket servidor
        logging.debug("action: stop_server_socket | result: in_progress")
        if self._server_socket:
            self._server_socket.shutdown(socket.SHUT_RDWR)
            self._server_socket.close()
        self._server_socket = None
        logging.debug("action: stop_server_socket | result: success")

        # Parar y joinear todos los handlers de clientes
        logging.debug("action: stop_client_handlers | result: in_progress")
        for handler in self._client_handlers:
            handler.stop()
        for handler in self._client_handlers:
            handler.join()
        self._client_handlers.clear()
        logging.debug("action: stop_client_handlers | result: success")

    def run(self):
        """
        Server loop con multithreading: cada conexión se atiende en un thread.
        El thread principal guarda los handlers de clientes para cierre ordenado.
        """
        while not self._stopped:
            try:
                client_socket = self.__accept_new_connection()
                handler = ClientHandler(client_socket, self)
                handler.start()
                self._client_handlers.append(handler)

                # Limpiar handlers terminados
                for h in self._client_handlers:
                    if not h.is_alive():
                        h.join()
                self._client_handlers = [h for h in self._client_handlers if h.is_alive()]

                if self.__se_debe_realizar_sorteo():
                    self._realizar_sorteo()
                    self._sorteo_realizado = True

            except OSError:
                break

        # Al salir, join a todos los handlers restantes
        for handler in self._client_handlers:
            handler.join()
        logging.info("action: stop_server | result: success")


    def __se_debe_realizar_sorteo(self) -> bool:
        return (not self._sorteo_realizado and len(self._agencias_que_completaron_envio) == self._agencias_totales)
            
            
    def _realizar_sorteo(self):
        bets: List[Bet] = load_bets()
        bets_ganadores = filter(has_won, bets)
        
        for bet in bets_ganadores:
            agencia = bet.agency
            dni = bet.document

            if agencia not in self._dnis_ganadores_por_agencia:
                self._dnis_ganadores_por_agencia[agencia] = []
            self._dnis_ganadores_por_agencia[agencia].append(int(dni))

    def __accept_new_connection(self) -> socket:
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        socket, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')

        return socket


    
    def agencia_completo_envio(self, agencia: int) -> bool:
        # TODO: hacer thread safe
        return agencia in self._agencias_que_completaron_envio
    
    def marcar_agencia_completada(self, agencia: int):
        # TODO: hacer thread safe
        self._agencias_que_completaron_envio.add(agencia)

    def almacenar_bets(self, bets: List[Bet]):
        # TODO: hacer thread safe
        store_bets(bets)
        
    def sorteo_fue_realizado(self):
        # Todo: hacer thread safe?
        return self._sorteo_realizado

    def obtener_ganadores_de_agencia(self, agencia: int) -> List[int]:
        # TODO: hacer thread safe
        return self._dnis_ganadores_por_agencia.get(agencia, [])