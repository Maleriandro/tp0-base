package common

import (
	"errors"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config  ClientConfig
	conn    net.Conn
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
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// // StartClientLoop Send messages to the client until some time threshold is met
// func (c *Client) StartClientLoop() {
// 	// There is an autoincremental msgID to identify every message sent
// 	// Messages if the message amount threshold has not been surpassed
// 	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
// 		if c.stopped {
// 			log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
// 			return
// 		}

// 		// Create the connection the server in every loop iteration. Send an
// 		c.createClientSocket()

// 		// TODO: Modify the send to avoid short-write
// 		fmt.Fprintf(
// 			c.conn,
// 			"[CLIENT %v] Message N°%v\n",
// 			c.config.ID,
// 			msgID,
// 		)
// 		msg, err := bufio.NewReader(c.conn).ReadString('\n')
// 		c.conn.Close()

// 		if err != nil {
// 			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
// 				c.config.ID,
// 				err,
// 			)
// 			return
// 		}

// 		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
// 			c.config.ID,
// 			msg,
// 		)

// 		// Wait a time between sending one message and the next one
// 		time.Sleep(c.config.LoopPeriod)

// 	}
// 	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
// }

func (c *Client) MakeBet() error {
	bet, err := newBetFromEnv(c.config.ID)
	if err != nil {
		log.Errorf("action: crear_apuesta | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return errors.New("failed to create bet")
	}

	// Send the bet to the server
	c.createClientSocket()

	serializedBet := bet.serialize()

	_, err = c.conn.Write(serializedBet)
	if err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)

		c.StopClient()
		return errors.New("failed to send bet to server")
	}

	// Receive a single byte from the server indicating success (0) or failure (other)
	resp := make([]byte, 1)
	_, err = c.conn.Read(resp)

	c.StopClient()

	if err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | error: %v",
			err,
		)
		return errors.New("failed to receive response from server")
	}
	if resp[0] != 0 {
		log.Errorf("action: apuesta_enviada | result: fail | code: %v",
			resp[0],
		)
		return errors.New("server returned error code")
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v", bet.document, bet.number)

	return nil
}

func (c *Client) StopClient() {
	log.Infof("action: stop_client | result: in_progress | client_id: %v", c.config.ID)

	c.stopped = true

	if c.conn != nil {
		c.conn.Close()
	}

}
