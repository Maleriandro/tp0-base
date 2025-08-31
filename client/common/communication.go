package common

import (
	"encoding/binary"
	"errors"
	"net"
)

type Communication struct {
	conn net.Conn
}

func CreateCommunication(server_address string) (*Communication, error) {
	conn, err := net.Dial("tcp", server_address)
	if err != nil {
		return nil, err
	}
	return &Communication{conn: conn}, nil
}

func (comm *Communication) SendBet(bet Bet) error {
	if comm.conn == nil {
		return errors.New("there is no connection")
	}
	serializedBet := bet.serialize()
	err := writeAll(comm.conn, serializedBet)
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
	if comm.conn != nil {
		comm.conn.Close()
		comm.conn = nil
	}
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

func (b *Bet) serialize() []byte {
	buf := make([]byte, 0)

	// Helper to append string with length prefix
	appendString := func(s string) {
		if len(s) > 255 {
			s = s[:255]
		}
		buf = append(buf, byte(len(s)))
		buf = append(buf, []byte(s)...)
	}

	agency_number := uint32ToBytes(b.agency)
	buf = append(buf, agency_number...)

	appendString(b.first_name)
	appendString(b.last_name)

	// Document (uint32, big endian)
	buf_document := uint32ToBytes(b.document)
	buf = append(buf, buf_document...)

	appendString(b.birthdate)

	// Number (uint32, big endian)
	buf_number := uint32ToBytes(b.number)
	buf = append(buf, buf_number...)

	return buf
}

func uint32ToBytes(n uint32) []byte {
	buf := make([]byte, 4)

	binary.BigEndian.PutUint32(buf, n)
	return buf
}
