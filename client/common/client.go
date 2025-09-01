package common

import (
	"errors"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID              uint32
	ServerAddress   string
	LoopAmount      int
	LoopPeriod      time.Duration
	MaxBetsPerBatch int
}

// Client Entity that encapsulates how
type Client struct {
	config  ClientConfig
	comm    *Communication
	stopped bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:  config,
		stopped: false,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientCommunication() error {
	comm, err := CreateCommunication(c.config.ServerAddress, c.config.MaxBetsPerBatch)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return errors.New("failed to create communication")
	}
	c.comm = comm
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() error {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed

	defer c.StopClient()

	bets, err := ReadBetsOfAgency(c.config.ID)
	if err != nil {
		log.Errorf("action: leer_apuestas | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	err = c.createClientCommunication()
	if err != nil {
		log.Errorf("action: crear_comunicacion | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	batches := divideBetsInBatches(bets, c.config.MaxBetsPerBatch)

	bets_made := 0

	for msgID := 1; msgID <= c.config.LoopAmount && msgID <= len(batches); msgID++ {
		if c.stopped {
			log.Infof("action: loop_finished | result: stopped | client_id: %v", c.config.ID)
			return nil
		}

		c.comm.startConnection()

		err := c.MakeBetBatch(batches[msgID-1])

		if err != nil {
			log.Errorf("action: loop_finished | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}

		c.comm.stopConnection()

		bets_made += len(batches[msgID-1])
		log.Infof("action: apuesta_enviada | result: in_progress | cantidad_acumulada: %v", bets_made)

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	log.Infof("action: apuesta_enviada | result: success | cantidad_total: %v", bets_made)
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)

	return nil
}

func (c *Client) MakeBetBatch(bets []Bet) error {
	if c.comm == nil {
		return errors.New("communication not initialized")
	}

	err := c.comm.SendBetsBatch(bets)
	if err != nil {
		return errors.New("failed to send bet batch to server")
	}

	resp, err := c.comm.RecieveConfirmation()
	if err != nil {
		return errors.New("failed to receive response from server")
	}
	if resp != 0 {
		return errors.New("server returned error code")
	}

	return nil
}

func (c *Client) StopClient() {
	log.Infof("action: stop_client | result: in_progress | client_id: %v", c.config.ID)

	c.stopped = true

	if c.comm != nil {
		c.comm.Close()
		c.comm = nil
	}

}

func divideBetsInBatches(bets []Bet, batchSize int) [][]Bet {
	var batches [][]Bet
	for i := 0; i < len(bets); i += batchSize {
		end := i + batchSize
		if end > len(bets) {
			end = len(bets)
		}
		batches = append(batches, bets[i:end])
	}
	return batches
}
