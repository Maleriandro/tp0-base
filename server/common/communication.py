from common.utils import Bet

class SocketNotInitializedError(RuntimeError):
    pass

class Communication:
    def __init__(self, socket):
        self.__socket = socket


    def __ensure_socket(self):
        if self.__socket is None:
            raise SocketNotInitializedError("Socket is not initialized")

    def recieve_bet(self):
        self.__ensure_socket()
        agency = self.__read_uint32()
        first_name = self.__read_next_string()
        last_name = self.__read_next_string()
        document = self.__read_uint32()
        birthdate = self.__read_next_string()
        number = self.__read_uint32()

        document_str = str(document)
        number_str = str(number)

        return Bet(agency=agency, first_name=first_name, last_name=last_name, document=document_str, birthdate=birthdate, number=number_str)

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
        byte = self.__socket.recv(1)
        if not byte:
            raise ValueError("Failed to read byte")
        return byte[0]

    def __read_next_string(self):
        length = self.__read_one_byte()
        return self.__read_string(length)

    def __read_string(self, n):
        string_bytes = self.__recvall(n)
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