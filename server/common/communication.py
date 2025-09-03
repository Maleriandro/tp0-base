from abc import ABC, abstractmethod
import logging
import socket
from common.utils import Bet
from enum import IntEnum
from dataclasses import dataclass
from typing import List, Optional


class SocketNotInitializedError(Exception):
    pass

class InvalidMessageType(Exception):
    pass

class InvalidServerMessage(Exception):
    """Raised when the server receives a message it should not receive."""
    pass

class ConexionCerradaPorCliente(Exception):
    """Elevada cuando el cliente se desconecta correctamente."""
    pass

class EOFError(Exception):
    """Elevada cuando se alcanza el final del archivo."""
    pass


class MessageType(IntEnum):
    ENVIO_BATCH = 1
    CONFIRMACION_RECEPCION = 2
    SOLICITUD_GANADORES = 3
    SORTEO_NO_REALIZADO = 4
    RESPUESTA_GANADORES = 5
    

class Message(ABC):
    tipo_mensaje: int
    
    @abstractmethod
    def serialize(self) -> bytes:
        raise NotImplementedError("Subclasses must implement this method")

@dataclass
class EnvioBatchMessage(Message):
    id_agencia: int
    numero_apuestas: int
    apuestas: List[Bet]
    tipo_mensaje: int = MessageType.ENVIO_BATCH

    def serialize(self) -> bytes:
        raise InvalidServerMessage("Server should not send ENVIO_BATCH messages")


@dataclass
class ConfirmacionRecepcionMessage(Message):
    confirmacion: int  # 0=exito, 1=error
    tipo_mensaje: int = MessageType.CONFIRMACION_RECEPCION

    def serialize(self) -> bytes:
        tipo_mensaje_byte = self.tipo_mensaje.to_bytes(1, byteorder='big')
        confirmacion_byte = self.confirmacion.to_bytes(1, byteorder='big')

        return tipo_mensaje_byte + confirmacion_byte

@dataclass
class SolicitudGanadoresMessage(Message):
    id_agencia: int
    tipo_mensaje: int = MessageType.SOLICITUD_GANADORES

    def serialize(self) -> bytes:
        raise InvalidServerMessage("Server should not send SOLICITUD_GANADORES messages")

@dataclass
class SorteoNoRealizadoMessage(Message):
    tipo_mensaje: int = MessageType.SORTEO_NO_REALIZADO

    def serialize(self) -> bytes:
        return self.tipo_mensaje.to_bytes(1, byteorder='big')

@dataclass
class RespuestaGanadoresMessage(Message):
    cant_ganadores: int
    dnis_ganadores: List[int]
    tipo_mensaje: int = MessageType.RESPUESTA_GANADORES

    def serialize(self) -> bytes:
        tipo_mensaje_byte = self.tipo_mensaje.to_bytes(1, byteorder='big')
        cant_ganadores_byte = self.cant_ganadores.to_bytes(4, byteorder='big')
        dnis_ganadores_bytes = b''.join(dni.to_bytes(4, byteorder='big') for dni in self.dnis_ganadores)

        return tipo_mensaje_byte + cant_ganadores_byte + dnis_ganadores_bytes

class Communication:
    def __init__(self, socket):
        self.__socket = socket
        
    def leer_mensaje_socket(self) -> Message:
        self.__ensure_socket()
        try:
            tipo_mensaje = self.__read_one_byte()
        except EOFError:
            raise ConexionCerradaPorCliente("Connection closed by the client")

        if tipo_mensaje == MessageType.ENVIO_BATCH:
            return self._leer_mensaje_envio_batch()
        elif tipo_mensaje == MessageType.SOLICITUD_GANADORES:
            return self._leer_mensaje_solicitud_ganadores()
        
        elif tipo_mensaje == MessageType.CONFIRMACION_RECEPCION:
            raise InvalidServerMessage("Server should not receive CONFIRMACION_RECEPCION messages")
        elif tipo_mensaje == MessageType.SORTEO_NO_REALIZADO:
            raise InvalidServerMessage("Server should not receive SORTEO_NO_REALIZADO messages")
        elif tipo_mensaje == MessageType.RESPUESTA_GANADORES:
            raise InvalidServerMessage("Server should not receive RESPUESTA_GANADORES messages")
        else:
            raise ValueError("Unknown message type")
        
    def receive_bet_batch(self) -> list[Bet]:
        mensaje = self.leer_mensaje_socket()
        if isinstance(mensaje, EnvioBatchMessage):
            return mensaje.apuestas
        raise InvalidMessageType("Expected EnvioBatchMessage")

    def receive_solicitud_ganador(self) -> SolicitudGanadoresMessage:
        mensaje = self.leer_mensaje_socket()
        if isinstance(mensaje, SolicitudGanadoresMessage):
            return mensaje
        raise InvalidMessageType("Expected SolicitudGanadoresMessage")

    def escribir_mensaje_socket(self, mensaje: Message):
        self.__ensure_socket()
        self.__socket.sendall(mensaje.serialize())

    def send_sorteo_no_realizado(self):
        mensaje = SorteoNoRealizadoMessage()
        self.escribir_mensaje_socket(mensaje)

    def send_ganadores_sorteo(self, ganadores: List[int]):
        mensaje = RespuestaGanadoresMessage(cant_ganadores=len(ganadores), dnis_ganadores=ganadores)
        self.escribir_mensaje_socket(mensaje)

    def _leer_mensaje_envio_batch(self):
        id_agencia = self.__read_uint32()
        numero_apuestas = self.__read_one_byte()
        apuestas = [self.__recieve_single_bet(id_agencia) for _ in range(numero_apuestas)]
        return EnvioBatchMessage(id_agencia=id_agencia, numero_apuestas=numero_apuestas, apuestas=apuestas)

    def _leer_mensaje_solicitud_ganadores(self):
        id_agencia = self.__read_uint32()
        return SolicitudGanadoresMessage(id_agencia=id_agencia)

    def __ensure_socket(self):
        if self.__socket is None:
            raise SocketNotInitializedError("Socket is not initialized")

    

    def __recieve_single_bet(self, agency) -> Bet:        
        nombre = self.__read_null_terminated_string()
        apellido = self.__read_null_terminated_string()
        documento = self.__read_uint32()
        fecha_nacimiento = self.__read_null_terminated_string()
        numero = self.__read_uint32()
        documento_str = str(documento)
        numero_str = str(numero)
        return Bet(agency=agency, first_name=nombre, last_name=apellido, document=documento_str, birthdate=fecha_nacimiento, number=numero_str)

    def send_confirmacion_recepcion_ok(self):
        mensaje = ConfirmacionRecepcionMessage(confirmacion=0)
        self.escribir_mensaje_socket(mensaje)

    def send_confirmacion_recepcion_error(self, error=1):
        mensaje = ConfirmacionRecepcionMessage(confirmacion=error)
        self.escribir_mensaje_socket(mensaje)

    def close(self):
        if self.__socket:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__socket = None

    def __read_one_byte(self):
        byte = self.__recvall(1)
        if not byte:
            raise ValueError("Failed to read byte")
        return byte[0]

    def __read_null_terminated_string(self):
        string_bytes = bytearray()
        while True:
            byte = self.__recvall(1)
            if byte == b'\x00':
                break
            string_bytes.extend(byte)
        return string_bytes.decode("utf-8")

    def __read_uint32(self):
        data = self.__recvall(4)
        return int.from_bytes(data, byteorder='big')

    def __recvall(self, n):
        data = bytearray()
        while len(data) < n:
            packet = self.__socket.recv(n - len(data))
            if not packet:
                if len(data) == 0:
                    raise EOFError("Connection closed by the client")
                
                raise ValueError("Failed to read all bytes")
            data.extend(packet)
        return data
