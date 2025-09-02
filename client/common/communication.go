package common

import (
	"encoding/binary"
	"errors"
	"net"
)

type Communication struct {
	conn               net.Conn
	max_bets_per_batch int
	server_address     string
}

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

func (comm *Communication) SendBetsBatch(bets []Bet) error {
	if comm.conn == nil {
		return errors.New("there is no connection")
	}

	if len(bets) > comm.max_bets_per_batch {
		return errors.New("too many bets")
	}

	serializedBets := SerializeBets(bets)
	err := writeAll(comm.conn, serializedBets)
	return err
}

func (comm *Communication) RecieveConfirmation() (resp byte, err error) {
	if comm.conn == nil {
		return 0, errors.New("there is no connection")
	}
	buffer := make([]byte, 1)

	err = readAll(comm.conn, buffer)

	if err != nil {
		return 0, err
	}
	return buffer[0], nil
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

	serialized[0] = byte(len(serialized))

	return serialized
}

func SerializeBets(bets []Bet) []byte {

	if len(bets) == 0 {
		return nil
	}

	if len(bets) > 255 {
		return nil
	}

	serializedBets := make([][]byte, len(bets))
	for i, bet := range bets {
		serializedBets[i] = serializeSingleBet(bet)
	}

	if len(bets) == 0 {
		return nil
	}
	header := make([]byte, 5)
	binary.BigEndian.PutUint32(header[:4], bets[0].agency)
	header[4] = byte(len(bets))

	result := make([]byte, 0)
	result = append(result, header...)

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
