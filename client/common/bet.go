package common

import (
	"encoding/binary"
	"errors"
	"os"
	"strconv"
)

type Bet struct {
	agency     string
	first_name string
	last_name  string
	document   uint32
	birthdate  string
	number     uint32
}

func newBetFromEnv(agency string) (*Bet, error) {
	nombre := os.Getenv("NOMBRE")
	if nombre == "" {
		return nil, errors.New("NOMBRE is required")
	}

	apellido := os.Getenv("APELLIDO")
	if apellido == "" {
		return nil, errors.New("APELLIDO is required")
	}

	numeroStr := os.Getenv("NUMERO")
	numero, err := strconv.Atoi(numeroStr)
	if err != nil {
		return nil, err
	}

	fechaNacimiento := os.Getenv("FECHA_NACIMIENTO")
	if fechaNacimiento == "" {
		return nil, errors.New("FECHA_NACIMIENTO is required")
	}

	documentoStr := os.Getenv("DOCUMENTO")
	documento, err := strconv.Atoi(documentoStr)
	if err != nil {
		return nil, err
	}

	bet := &Bet{
		agency:     agency,
		first_name: nombre,
		last_name:  apellido,
		document:   uint32(documento),
		birthdate:  fechaNacimiento,
		number:     uint32(numero),
	}
	return bet, nil
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

	appendString(b.agency)
	appendString(b.first_name)
	appendString(b.last_name)
	appendString(b.birthdate)

	// Document (uint32, big endian)
	buf_document := uint32ToBytes(b.document)
	buf = append(buf, buf_document...)

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
