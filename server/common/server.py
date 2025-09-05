import threading            
            
import socket
import logging
import signal
from common.client_handler import ClientHandler
from typing import Callable, Dict, List, Optional

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

        self._cond_sorteo = threading.Condition()

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

        # Despertar el thread principal si está esperando el sorteo
        with self._cond_sorteo:
            self._cond_sorteo.notify_all()

    def run(self):
        """
        Server loop con multithreading: cada conexión se atiende en un thread.
        El thread principal guarda los handlers de clientes para cierre ordenado.
        """
        clientes_atendidos = 0

        while not self._stopped and clientes_atendidos < self._agencias_totales:
            try:
                client_socket = self.__accept_new_connection()

                clientes_atendidos += 1
                handler = ClientHandler(client_socket, self)
                handler.start()
                self._client_handlers.append(handler)

            except OSError:
                self._stopped = True
                break

        # Espera bloqueante hasta que se pueda realizar el sorteo o se reciba SIGTERM
        if not self._stopped:
            self.__monitor_esperar_hasta_poder_realizar_sorteo()

        if not self._stopped:
            logging.info("action: realizar_sorteo | result: in_progress")
            self._realizar_sorteo()
            self._sorteo_realizado.set(True)
            logging.info("action: realizar_sorteo | result: success")
        else:
            self.__stop_server(None, None)

        # Al salir, join a todos los handlers restantes
        for handler in self._client_handlers:
            handler.join()
        logging.info("action: stop_server | result: success")


    def __monitor_esperar_hasta_poder_realizar_sorteo(self):
        """
        Monitor que bloquea hasta que se pueda realizar el sorteo o se reciba SIGTERM.
        """
        with self._cond_sorteo:
            while not self._stopped and (self._sorteo_realizado.get() or len(self._agencias_que_completaron_envio.get()) < self._agencias_totales):
                self._cond_sorteo.wait()

    def _realizar_sorteo(self):
        # No necesito hacer load bets thread safe, porque esta funcion se llama unicamente cuando ya todos los clientes enviaron sus apuestas.
        # Y ningun ClientHandler va a poder almacenar niguna apuesta extra, por lo que no es necesario protegerlo.
        bets: List[Bet] = load_bets()
        bets_ganadores = filter(has_won, bets)

        dnis_ganadores_por_agencia: Dict[int, List[int]] = dict()
        
        for bet in bets_ganadores:
            agencia = bet.agency
            dni = bet.document

            if agencia not in dnis_ganadores_por_agencia:
                dnis_ganadores_por_agencia[agencia] = []
            dnis_ganadores_por_agencia[agencia].append(int(dni))

        self._dnis_ganadores_por_agencia.set(dnis_ganadores_por_agencia)

    def __accept_new_connection(self) -> socket.socket:
        """
        Accept new connections

        Function blocks until a connection to a client.
        """
        logging.info('action: accept_connections | result: in_progress')
        sock, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return sock

    def agencia_completo_envio(self, agencia: int) -> bool:
        agencias_que_completaron_envio_value = self._agencias_que_completaron_envio.get()
        return agencia in agencias_que_completaron_envio_value
    
    def marcar_agencia_completada(self, agencia: int):
        with self._cond_sorteo:
            self._agencias_que_completaron_envio.update(lambda s: s.union({agencia}))
            self._cond_sorteo.notify_all()

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