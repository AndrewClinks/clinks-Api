from django import template
import decimal

from ..utils import DateUtils

register = template.Library()


@register.filter(name='get_currency_representation')
def get_currency_representation(price_in_cents, currency):
    price = decimal.Decimal(price_in_cents) / 100
    return f"{currency.symbol}{price: .2f}"


@register.filter(name='get_price')
def get_price(price, price_sale):
    price_to_show = price_sale if price_sale else price
    return price_to_show


@register.filter(name="convert_to_local_time")
def convert_to_local_time(created_at):
    print(created_at, DateUtils.convert_to_dublin_time(created_at))
    return DateUtils.convert_to_dublin_time(created_at)