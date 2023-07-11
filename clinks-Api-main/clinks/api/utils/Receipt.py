import os

from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML

import uuid
from ..utils import File


def generate(order):
    data = get_pdf_data(order)

    template_url = str(settings.BASE_DIR) + '/api/templates/order.html'
    html_string = render_to_string(template_url, data)

    filename = f'order_receipt_{order.id}.pdf'
    html = HTML(string=html_string)
    html.write_pdf(target=f'/tmp/{filename}')

    fs = FileSystemStorage('/tmp')

    file = fs.open(filename, 'rb')
    file.__setattr__('content_type', 'application/pdf')

    uid = uuid.uuid4()
    full_path_name = f"/files/orders/receipt_{uid}.pdf"

    File.upload(file.read(), full_path_name, file.content_type)

    order.receipt = full_path_name
    order.save()


def get_pdf_data(order):
    customer = order.customer
    customer_full_name = customer.user.first_name + " " + customer.user.last_name

    total_item_count = 0

    for item in order.data["items"]:
        total_item_count += item["quantity"]

    data = {
        "order": order,
        "payment": order.payment,
        "customer_full_name": customer_full_name,
        "currency": order.payment.currency,
        "total_item_count": total_item_count,
        "clinks_logo": f"https://{os.environ['AWS_CLOUD_FRONT_DOMAIN']}/images/clinks/pdf_logo.png"
    }

    return data




