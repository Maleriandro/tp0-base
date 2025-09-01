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
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		if c.stopped {

			log.Infof("parado en MSGid: %v", msgID)
			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
			return
		}

		err := c.MakeBet()

		if err != nil {
			log.Errorf("action: loop_finished | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) MakeBet() error {
	log.Infof("action: crear_apuesta | result: in_progress | client_id: %v", c.config.ID)
	bet, err := ReadBetsOfAgency(c.config.ID)

	if err != nil {
		log.Errorf("action: crear_apuesta | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return errors.New("failed to read bets from agency")
	}

	batches := divideBetsInBatches(bet, c.config.MaxBetsPerBatch)

	// Send the bet to the server
	c.createClientCommunication()

	apuestas_enviadas := 0

	for _, batch := range batches {
		if c.stopped {
			log.Infof("action: apuesta_enviada | result: stopped | client_id: %v", c.config.ID)
			return errors.New("client stopped")
		}

		err = c.comm.SendBetsBatch(batch)
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			c.StopClient()
			return errors.New("failed to send bet batch to server")
		}

		resp, err := c.comm.RecieveConfirmation()
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | error: %v",
				err,
			)
			c.StopClient()
			return errors.New("failed to receive response from server")
		}
		if resp != 0 {
			log.Errorf("action: apuesta_enviada | result: fail | code: %v",
				resp,
			)
			c.StopClient()
			return errors.New("server returned error code")
		}

		apuestas_enviadas += len(batch)
		log.Infof("action: apuesta_enviada | result: in_progress | cantidad_acumulada: %v", apuestas_enviadas)

		if err := c.comm.ResetConnection(); err != nil {
			log.Errorf("action: apuesta_enviada | result: fail | error: %v",
				err,
			)
			c.StopClient()
			return errors.New("failed to reset connection")
		}
	}

	log.Infof("action: apuesta_enviada | result: success | cantidad_total: %v", apuestas_enviadas)

	c.StopClient()

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
