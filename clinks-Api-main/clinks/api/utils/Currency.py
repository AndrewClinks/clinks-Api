def format(amount_in_cents, symbol="£"):
    return symbol + '{:0,.2f}'.format(amount_in_cents / 100)
