from common.utils import Bet

class SocketNotInitializedError(RuntimeError):
    pass

class Communication:
    def __init__(self, socket):
        self.__socket = socket


    def __ensure_socket(self):
        if self.__socket is None:
            raise SocketNotInitializedError("Socket is not initialized")
        
    def recieve_bet_batch(self) -> list[Bet]:
        id_agency, batch_size = self.__recieve_batch_header()
        return [self.__recieve_single_bet(id_agency) for _ in range(batch_size)]

    def __recieve_batch_header(self) -> tuple[int, int]:
        self.__ensure_socket()
        agency = self.__read_uint32()
        batch_size = self.__read_one_byte()
        return agency, batch_size

    def __recieve_single_bet(self, agency) -> Bet:
        _len_bet_actual = self.__read_one_byte()
        
        nombre = self.__read_null_terminated_string()
        apellido = self.__read_null_terminated_string()
        documento = self.__read_uint32()
        fecha_nacimiento = self.__read_null_terminated_string()
        numero = self.__read_uint32()

        documento_str = str(documento)
        numero_str = str(numero)

        return Bet(agency=agency, first_name=nombre, last_name=apellido, document=documento_str, birthdate=fecha_nacimiento, number=numero_str)

    def send_ok(self):
        self.__ensure_socket()
        self.__socket.sendall(bytes([0]))

    def send_error(self, error=1):
        self.__ensure_socket()
        self.__socket.sendall(bytes([error]))

    def close(self):
        if self.__socket:
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
                raise ValueError("Failed to read all bytes")
            data.extend(packet)
        return data