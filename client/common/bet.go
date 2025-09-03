package common

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
