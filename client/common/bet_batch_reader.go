package common

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
)

type BetBatchReader struct {
	file      *os.File
	reader    *csv.Reader
	batchSize int
	agencyID  uint32
	closed    bool
}

// NewBetBatchReader abre el archivo y crea el reader
func NewBetBatchReader(agencyID uint32, batchSize int) (*BetBatchReader, error) {
	filePath := getAgencyCsvFilePath()
	f, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	return &BetBatchReader{
		file:      f,
		reader:    csv.NewReader(f),
		batchSize: batchSize,
		agencyID:  agencyID,
		closed:    false,
	}, nil
}

// NextBatch devuelve el próximo batch de apuestas
func (b *BetBatchReader) NextBatch() ([]Bet, error) {
	if b.closed {
		// Si ya fue cerrado, devolvemos slice vacío y sin error
		return []Bet{}, nil
	}
	bets := make([]Bet, 0, b.batchSize)

	for len(bets) < b.batchSize {
		record, err := b.reader.Read()
		if err != nil {
			b.Close() // Cierra el archivo si termina o hay error
			// Si es EOF, devolvemos los bets que hayamos leído, y no devuelvo error
			if err == os.ErrClosed || err.Error() == "EOF" {
				return bets, nil
			}
			// Solo devolvemos error si es irrecuperable
			return nil, err
		}
		if len(record) < 5 {
			fmt.Printf("Warning: invalid data in record: %v (expected 5 fields, got %d)\n", record, len(record))
			continue
		}
		document_int, errDoc := strconv.Atoi(record[2])
		number_int, errNum := strconv.Atoi(record[4])
		if errDoc != nil || errNum != nil {
			fmt.Printf("Warning: invalid data in record: %v (document_int err: %v, number_int err: %v)\n", record, errDoc, errNum)
			continue
		}
		bet := NewBet(b.agencyID, record[0], record[1], uint32(document_int), record[3], uint32(number_int))
		bets = append(bets, bet)
	}
	return bets, nil
}

// Close cierra el file descriptor si no fue cerrado antes
func (b *BetBatchReader) Close() {
	if b.closed {
		return
	}
	b.closed = true
	b.file.Close()
}

func getAgencyCsvFilePath() string {
	return "./agency.csv"
}
