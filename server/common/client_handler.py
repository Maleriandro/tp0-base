from socket import socket
import threading
import logging

from common.communication import Communication, EnvioBatchMessage, MessageType, SolicitudGanadoresMessage
from common.server import Server

class ClientHandler(threading.Thread):
    def __init__(self, client_socket: socket, server: Server):
        super().__init__()
        self.communication: Communication = Communication(client_socket)
        self.server: Server = server
        self.stopped: bool = False

    def run(self):
        try:
            logging.info(f"thread: {self.name} | action: esperando_recibir_mensaje | result: in_progress")
            self.recibir_mensajes()
        except Exception as e:
            import traceback
            logging.error(f"thread: {self.name} | action: apuesta_recibida | result: fail | cantidad: 0 | error: {e} | file: {traceback.extract_tb(e.__traceback__)[-1].filename} | line: {traceback.extract_tb(e.__traceback__)[-1].lineno}")
            self.communication.send_confirmacion_recepcion_error()
        finally:
            self.communication.close()

    def stop(self):
        self.stopped = True
        try:
            self.communication.close()
        except Exception:
            pass

    def recibir_mensajes(self):
        mantener_conexion = True
        
        while mantener_conexion and not self.stopped:
            mensaje = self.communication.leer_mensaje_socket()
            
            if mensaje.tipo_mensaje == MessageType.ENVIO_BATCH:
                mantener_conexion = self.procesar_envio_batch(mensaje)
            elif mensaje.tipo_mensaje == MessageType.SOLICITUD_GANADORES:
                mantener_conexion = self.server._procesar_solicitud_ganadores(mensaje)
            else:
                logging.error(f"thread: {self.name} | action: mensaje_no_reconocido | result: fail | tipo: {mensaje.tipo_mensaje}")
                mantener_conexion = False


    def procesar_envio_batch(self, mensaje: EnvioBatchMessage) -> bool:
        # Si ya completó envio, no debería enviarme más apuestas
        if (self.server.agencia_completo_envio(mensaje.id_agencia)):
            self.communication.send_confirmacion_recepcion_error()
            return False

        # Si recibo 0 bets, quiere decir que ya no envian más apuestas
        if mensaje.numero_apuestas == 0:
            self.server.marcar_agencia_completada(mensaje.id_agencia)
            self.communication.send_confirmacion_recepcion_ok()
            return False
        
        apuestas = mensaje.apuestas

        logging.info(f"thread: {self.name} | action: apuesta_recibida | result: success | cantidad: {mensaje.numero_apuestas}")
        self.server.almacenar_bets(apuestas)
        
        self.communication.send_confirmacion_recepcion_ok()
        return True
    
    def procesar_solicitud_ganadores(self, mensaje: SolicitudGanadoresMessage) -> bool:
        if not self.server.sorteo_fue_realizado():
            self.communication.send_sorteo_no_realizado()
            return False

        agencia = mensaje.id_agencia
        dnis_ganadores = self.server.obtener_ganadores_de_agencia(agencia)
        
        self.communication.send_ganadores_sorteo(dnis_ganadores)
        return False