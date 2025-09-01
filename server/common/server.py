import socket
import logging
import signal

from common.communication import Communication
from common.utils import store_bets, Bet

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._current_client_communication = None
        self._stopped = False
        
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
            except OSError:
                break
            
        logging.info("action: stop_server | result: success")

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            logging.info(f"action: esperando_recibir_apuesta | result: in_progress")
            bets: list[Bet] = self._current_client_communication.recieve_bet_batch()
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")
            store_bets(bets)

            self._current_client_communication.send_ok()
            
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
            self._current_client_communication.send_error()
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
