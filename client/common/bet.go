package common

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
)

type Bet struct {
	agency     uint32
	first_name string
	last_name  string
	document   uint32
	birthdate  string
	number     uint32
}

// NewBet es un constructor para Bet que valida los tamaños de los campos string.
func NewBet(agency uint32, firstName, lastName string, document uint32, birthdate string, number uint32) Bet {
	const (
		maxNameLen      = 29
		maxBirthdateLen = 10
	)

	if len(firstName) > maxNameLen {
		firstName = firstName[:maxNameLen]
	}
	if len(lastName) > maxNameLen {
		lastName = lastName[:maxNameLen]
	}
	if len(birthdate) > maxBirthdateLen {
		birthdate = birthdate[:maxBirthdateLen]
	}

	return Bet{
		agency:     agency,
		first_name: firstName,
		last_name:  lastName,
		document:   document,
		birthdate:  birthdate,
		number:     number,
	}
}

// ReadBetsFromCSV lee el archivo .data/agency-{id}.csv y devuelve un slice de bets.Bet
func ReadBetsOfAgency(agencyID uint32) ([]Bet, error) {
	filePath := getAgencyCsvFilePath(agencyID)
	f, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("no se pudo abrir el archivo %s: %w", filePath, err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	reader.TrimLeadingSpace = true
	lines, err := reader.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("error leyendo CSV: %w", err)
	}

	bets := make([]Bet, 0, len(lines))
	for _, row := range lines {
		if len(row) < 5 {
			log.Warningf("salteando fila con menos de 5 columnas: %v", row)
			continue
		}

		document_int, err := strconv.Atoi(row[2])
		if err != nil {
			log.Warningf("salteando fila con documento inválido: %v", row)
			continue
		}

		number_int, err := strconv.Atoi(row[4])
		if err != nil {
			log.Warningf("salteando fila con número inválido: %v", row)
			continue
		}

		b := NewBet(agencyID, row[0], row[1], uint32(document_int), row[3], uint32(number_int))

		bets = append(bets, b)
	}
	return bets, nil
}

func getAgencyCsvFilePath(agencyID uint32) string {
	return "./agency.csv"
}
