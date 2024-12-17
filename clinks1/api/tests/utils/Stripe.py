from ...utils import Constants

# for enabled test > acct_1KW0in2fgxhFyEMV, dev >acct_1KVz4MRWqTWQY2XW
# for disabled test > acct_1KW0de2c6XEyVEdg, dev > acct_1KVw0lDHi43VvSmK


def payments_enabled_account(company, stripe_account_id="acct_1KW0in2fgxhFyEMV"):
    company.stripe_account_id = stripe_account_id
    company.stripe_charges_enabled = True
    company.save()


def payments_disabled_account(company, stripe_account_id="acct_1KVw0lDHi43VvSmK"):
    company.stripe_account_id = stripe_account_id
    company.stripe_charges_enabled = False
    company.save()
