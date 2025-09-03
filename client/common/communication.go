package common

import (
	"encoding/binary"
	"errors"
	"net"
	"time"
)

type Communication struct {
	conn               net.Conn
	max_bets_per_batch int
	server_address     string
}

const (
	ENVIO_BATCH            byte = 1
	CONFIRMACION_RECEPCION byte = 2
	SOLICITUD_GANADORES    byte = 3
	SORTEO_NO_REALIZADO    byte = 4
	RESPUESTA_GANADORES    byte = 5
)

func CreateCommunication(server_address string, max_bets_per_batch int) (*Communication, error) {
	conn, err := net.Dial("tcp", server_address)
	if err != nil {
		return nil, err
	}
	return &Communication{conn: conn, max_bets_per_batch: max_bets_per_batch, server_address: server_address}, nil
}

func (comm *Communication) startConnection() error {
	//Si la comunicacion ya está iniciada, no hace nada
	if comm.conn != nil {
		return nil
	}

	conn, err := net.Dial("tcp", comm.server_address)
	if err != nil {
		return err
	}
	comm.conn = conn
	return nil
}

func (comm *Communication) stopConnection() {
	if comm.conn != nil {
		comm.conn.Close()
		comm.conn = nil
	}
}

func (comm *Communication) ResetConnection() error {
	comm.stopConnection()
	return comm.startConnection()
}

func (comm *Communication) SendBetsBatch(bets []Bet, agencyId uint32) error {
	if comm.conn == nil {
		return errors.New("there is no connection")
	}

	if len(bets) > comm.max_bets_per_batch {
		return errors.New("too many bets")
	}

	serializedBets := SerializeBetsBatchMessage(bets, agencyId)
	err := writeAll(comm.conn, serializedBets)
	return err
}

func (comm *Communication) RecieveConfirmation() (resp byte, err error) {
	if comm.conn == nil {
		return 0, errors.New("there is no connection")
	}
	buffer := make([]byte, 2)

	err = readAll(comm.conn, buffer)

	if err != nil {
		return 0, err
	}

	if buffer[0] != CONFIRMACION_RECEPCION {
		return 0, errors.New("invalid confirmation")
	}
	return buffer[1], nil
}

func (comm *Communication) Close() {
	comm.stopConnection()
}

func readAll(conn net.Conn, buf []byte) error {
	total := 0
	for total < len(buf) {
		n, err := conn.Read(buf[total:])
		if err != nil {
			return err
		}
		total += n
	}
	return nil
}

func writeAll(conn net.Conn, buf []byte) error {
	total := 0
	for total < len(buf) {
		n, err := conn.Write(buf[total:])
		if err != nil {
			return err
		}
		total += n
	}
	return nil
}

func serializeSingleBet(bet Bet) []byte {
	serialized_name := stringToNullEndedBytes(bet.first_name, 29)
	serialized_last_name := stringToNullEndedBytes(bet.last_name, 29)
	serialized_birthdate := stringToNullEndedBytes(bet.birthdate, 10)

	serialized := make([]byte, 0)
	serialized = append(serialized, serialized_name...)
	serialized = append(serialized, serialized_last_name...)
	serialized = append(serialized, uint32ToBytes(bet.document)...)
	serialized = append(serialized, serialized_birthdate...)
	serialized = append(serialized, uint32ToBytes(bet.number)...)

	return serialized
}

func SerializeBetsBatchMessage(bets []Bet, agencyId uint32) []byte {
	if len(bets) > 255 {
		return nil
	}

	serializedBets := make([][]byte, len(bets))
	for i, bet := range bets {
		serializedBets[i] = serializeSingleBet(bet)
	}

	header_msg := make([]byte, 1)
	header_msg[0] = ENVIO_BATCH

	header_body := make([]byte, 5)
	binary.BigEndian.PutUint32(header_body[:4], agencyId)
	header_body[4] = byte(len(bets))

	result := append(header_msg, header_body...)

	for i := 0; i < len(serializedBets); i++ {
		result = append(result, serializedBets[i]...)
	}
	return result
}

func uint32ToBytes(n uint32) []byte {
	buf := make([]byte, 4)

	binary.BigEndian.PutUint32(buf, n)
	return buf
}

func stringToNullEndedBytes(s string, max_size int) []byte {
	if len(s) > max_size {
		s = s[:max_size]
	}
	return append([]byte(s), 0)
}

func (comm *Communication) GetLotteryResult(agencyId uint32) ([]uint32, error) {

	var ganadores []uint32 = nil
	for {
		err := comm.sendWinnersRequest(agencyId)
		if err != nil {
			return nil, err
		}
		ganadores, err = comm.receiveWinnersResponse()
		if err != nil {
			return nil, err
		}

		//Si ganadores deja de ser nil, quiere decir que ya obtuve quienes son los ganadores
		if ganadores != nil {
			break
		}

		//Si sigue siendo nil, tengo que reiniciar la conexion,
		// esperar un tiempo, y volver a consultar por ganadores
		time.Sleep(100 * time.Millisecond)
		log.Infof("action: consulta_ganadores | result: in_progress | client_id: %v", agencyId)
	}

	return ganadores, nil
}

func (comm *Communication) sendWinnersRequest(agencyId uint32) error {
	header := make([]byte, 1)
	header[0] = SOLICITUD_GANADORES

	agency := uint32ToBytes(agencyId)

	msg := append(header, agency...)

	err := writeAll(comm.conn, msg)
	if err != nil {
		return err
	}

	return nil
}

// Devuelve null en caso de que la lotería no se haya realizado,
// Devuelve un array vacio en caso de que la lotería se haya realizado, pero no hay ningun ganador
func (comm *Communication) receiveWinnersResponse() ([]uint32, error) {
	if comm.conn == nil {
		return nil, errors.New("there is no connection")
	}

	buffer := make([]byte, 1)
	err := readAll(comm.conn, buffer)
	if err != nil {
		return nil, err
	}

	if buffer[0] == SORTEO_NO_REALIZADO {
		return nil, nil
	}
	if buffer[0] != RESPUESTA_GANADORES {
		return nil, errors.New("invalid response from server")
	}

	cantidadGanadoresBuf := make([]byte, 4)
	err = readAll(comm.conn, cantidadGanadoresBuf)
	if err != nil {
		return nil, err
	}
	cantidadGanadores := binary.BigEndian.Uint32(cantidadGanadoresBuf)

	results := make([]uint32, cantidadGanadores)
	for i := uint32(0); i < cantidadGanadores; i++ {
		numBuf := make([]byte, 4)
		err = readAll(comm.conn, numBuf)
		if err != nil {
			return nil, err
		}
		results[i] = binary.BigEndian.Uint32(numBuf)
	}

	return results, nil
}
