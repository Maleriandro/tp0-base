import threading            
            
import socket
import logging
import signal
from common.client_handler import ClientHandler
from typing import Callable, Dict, List

from common.communication import Communication, EnvioBatchMessage, Message, MessageType, SolicitudGanadoresMessage
from common.utils import has_won, load_bets, store_bets, Bet
import traceback
import copy
from typing import Generic, TypeVar

class Server:
    def __init__(self, port, listen_backlog, client_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._current_client_communication = None
        self._stopped = False

        self._client_handlers: List[ClientHandler] = []  # lista de ClientHandler activos

        self._lock_store_bets = threading.Lock()

        self._agencias_totales = client_amount
        self._agencias_que_completaron_envio: ThreadSafeValue[set[int]] = ThreadSafeValue(set())
        self._sorteo_realizado: ThreadSafeValue[bool] = ThreadSafeValue(False)
        self._dnis_ganadores_por_agencia: ThreadSafeValue[Dict[int, list[int]]] = ThreadSafeValue(dict())  

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

                self.__limpiar_client_handlers_terminados()

                if self.__se_debe_realizar_sorteo():
                    self._realizar_sorteo()
                    self._sorteo_realizado.set(True)

            except OSError:
                break

        # Al salir, join a todos los handlers restantes
        for handler in self._client_handlers:
            handler.join()
        logging.info("action: stop_server | result: success")


    def __limpiar_client_handlers_terminados(self):
        for h in self._client_handlers:
            if not h.is_alive():
                h.join()
        self._client_handlers = [h for h in self._client_handlers if h.is_alive()]

    def __se_debe_realizar_sorteo(self) -> bool:
        return (not self._sorteo_realizado.get() and len(self._agencias_que_completaron_envio.get()) == self._agencias_totales)
            
    def _realizar_sorteo(self):
        # No necesito hacer load bets thread safe, porque esta funcion se llama unicamente cuando ya todos los clientes enviaron sus apuestas.
        # Y ningun ClientHandler va a poder almacenar niguna apuesta extra, por lo que no es necesario protegerlo.
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
        agencias_que_completaron_envio_value = self._agencias_que_completaron_envio.get()
        return agencia in agencias_que_completaron_envio_value
    
    def marcar_agencia_completada(self, agencia: int):
        self._agencias_que_completaron_envio.update(lambda s: s.union({agencia}))

    def almacenar_bets(self, bets: List[Bet]):
        # Varios threads podrían intentar llamar store_bets al mismo tiempo, así que lo protejo.
        with self._lock_store_bets:
            store_bets(bets)

    def sorteo_fue_realizado(self) -> bool:
        return self._sorteo_realizado.get()

    def obtener_ganadores_de_agencia(self, agencia: int) -> List[int]:
        dnis_ganadores_por_agencia = self._dnis_ganadores_por_agencia.get()
        return dnis_ganadores_por_agencia.get(agencia, [])


# Clase genérica para encapsular un valor y su lock
T = TypeVar('T')

# Clase para proteger valores con locks, y que no acceda accidentalmente al valor de manera no protegida
class ThreadSafeValue(Generic[T]):
    def __init__(self, value: T):
        self._value: T = value
        self._lock = threading.Lock()
    def get(self) -> T:
        with self._lock:
            return copy.deepcopy(self._value)
    def set(self, value: T):
        with self._lock:
            self._value = value
    def update(self, func: 'Callable[[T], T]'):
        with self._lock:
            self._value = func(self._value)