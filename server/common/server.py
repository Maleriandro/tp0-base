import socket
import logging
import signal
from typing import Dict, List

from common.communication import Communication, EnvioBatchMessage, Message, MessageType, SolicitudGanadoresMessage
from common.utils import has_won, load_bets, store_bets, Bet

class Server:
    def __init__(self, port, listen_backlog, client_amount):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._current_client_communication = None
        self._stopped = False
        
        self._agencias_totales = client_amount
        self._agencias_que_completaron_envio = set()

        self._sorteo_realizado = False
        self._dnis_ganadores_por_agencia: Dict[int, List[str]] = dict()

        signal.signal(signal.SIGTERM, self.__stop_server)

    def __stop_server(self, signum, frame):
        # Parar loop
        logging.info("action: stop_server | result: in_progress")
        self._stopped = True

        # Cerrar socket servidor
        logging.debug("action: stop_server_socket | result: in_progress")
        if self._server_socket:
            self._server_socket.close()
        self._server_socket = None
        logging.debug("action: stop_server_socket | result: success")

        # Cerrar socket cliente
        logging.debug("action: stop_client_socket | result: in_progress")
        if self._current_client_communication:
            self._current_client_communication.close()
        self._current_client_communication = None
        logging.debug("action: stop_client_socket | result: success")

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """


        while not self._stopped:
            try:
                self._current_client_communication = self.__accept_new_connection()
                self.__handle_client_connection()
                
                if self.__se_debe_realizar_sorteo():
                    self._realizar_sorteo()
                    self._sorteo_realizado = True

            except OSError:
                break

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
            self._dnis_ganadores_por_agencia[agencia].append(dni)

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            logging.info(f"action: esperando_recibir_mensaje | result: in_progress")
            self.recibir_mensajes()
            
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0")
            self._current_client_communication.send_confirmacion_recepcion_error(self, error=1)()
        finally:
            if self._current_client_communication:
                self._current_client_communication.close()
            self._current_client_communication = None

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')

        client_communication = Communication(c)
        return client_communication


    # Devuelve true si la conexion debe ser mantenida, false si debe ser cerrada.
    def _procesar_envio_batch(self, mensaje: EnvioBatchMessage) -> bool:
        # Si ya completó envio, no debería enviarme más apuestas
        if (mensaje.id_agencia in self._agencias_que_completaron_envio):
            self._current_client_communication.send_confirmacion_recepcion_error(self, error=1)()
            return False

        # Si recibo 0 bets, quiere decir que ya no envian más apuestas
        if mensaje.numero_apuestas == 0:
            self._agencias_que_completaron_envio.add(mensaje.id_agencia)
            self._current_client_communication.send_confirmacion_recepcion_ok()
            return False
        
        apuestas = mensaje.apuestas
        
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(mensaje.numero_apuestas)}")
        store_bets(apuestas)
        
        return True
    

    # Devuelve true si la conexion debe ser mantenida, false si debe ser cerrada.
    def _procesar_solicitud_ganadores(self, mensaje: SolicitudGanadoresMessage) -> bool:
        if not self._sorteo_realizado:
            self._current_client_communication.send_sorteo_no_realizado()
            return False

        agencia = mensaje.id_agencia
        dnis_ganadores = self._dnis_ganadores_por_agencia.get(agencia, [])
        
        self._current_client_communication.send_ganadores_sorteo(dnis_ganadores)
        return False


    def recibir_mensajes(self):        
        mantener_conexion = True

        while mantener_conexion and not self._stopped:
            mensaje = self._current_client_communication.leer_mensaje_socket()

            match mensaje.tipo_mensaje:
                case MessageType.ENVIO_BATCH:
                    mantener_conexion = self._procesar_envio_batch(mensaje)
                case MessageType.SOLICITUD_GANADORES:
                    mantener_conexion = self._procesar_solicitud_ganadores(mensaje)
