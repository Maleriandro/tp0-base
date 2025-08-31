package common

import (
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

func newBetFromEnv(agency string) (Bet, error) {

	nombre := os.Getenv("NOMBRE")
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
		fechaNacimiento = "2000-01-01"
	}

	documentoStr := os.Getenv("DOCUMENTO")
	documento, err := strconv.Atoi(documentoStr)
	if err != nil {
		documento = 0
	}

	bet := Bet{
		agency:     agency,
		first_name: nombre,
		last_name:  apellido,
		document:   uint32(documento),
		birthdate:  fechaNacimiento,
		number:     uint32(numero),
	}
	return bet, nil
}
