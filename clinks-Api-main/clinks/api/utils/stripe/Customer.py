from ..stripe import Connect, Card


def add_card(student, source, default=False):
    if not student.stripe_customer_id:
        card = Connect.create_account(student, source)
    else:
        card = Card.create(student, source, default)

    return card
