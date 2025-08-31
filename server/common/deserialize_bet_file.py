from utils import Bet

def deserialize_bet(socket):
    agency = read_next_string(socket)
    first_name = read_next_string(socket)
    last_name = read_next_string(socket)
    document = read_uint32(socket)
    birthdate = read_next_string(socket)
    number = read_uint32(socket)

    document_str = str(document)
    number_str = str(number)

    return Bet(agency=agency, first_name=first_name, last_name=last_name, document=document_str, birthdate=birthdate, number=number_str)


def read_one_byte(socket):
    byte = socket.recv(1)
    if not byte:
        raise ValueError("Failed to read byte")
    return byte[0]


def read_next_string(socket):
    length = read_one_byte(socket)
    return read_string(socket, length)

def read_string(socket, n):
    string_bytes = recvall(socket, n)
    return string_bytes.decode("utf-8")


def read_uint32(socket):
    data = recvall(socket, 4)
    return int.from_bytes(data, byteorder='big')


def recvall(socket, n):
    data = bytearray()
    while len(data) < n:
        packet = socket.recv(n - len(data))
        if not packet:
            raise ValueError("Failed to read all bytes")
        data.extend(packet)
    return data