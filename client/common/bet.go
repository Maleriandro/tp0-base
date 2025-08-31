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
	
	nombre := os.LookupEnv("NOMBRE")
	if nombre == "" {
		nombre = "desconocido"
	}

	apellido := os.Getenv("APELLIDO")
	if apellido == "" {
		apellido = "desconocido"
	}

	numeroStr := os.Getenv("NUMERO")
	numero, err := strconv.Atoi(numeroStr)
	if err != nil {
		numero = 0
	}

	fechaNacimiento := os.Getenv("FECHA_NACIMIENTO")
	if fechaNacimiento == "" {
		fechaNacimiento = "2000-00-00"
	}

	documentoStr := os.Getenv("DOCUMENTO")
	documento, err := strconv.Atoi(documentoStr)
	if err != nil {
		documento = 0
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
