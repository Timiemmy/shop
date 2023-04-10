from django.contrib import admin
from django.urls import reverse
import csv
import datetime
from django.http import HttpResponse
from .models import Order, OrderItem
from django.utils.safestring import mark_safe


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    ''''
    create an instance of HttpResponse, specifying the text/csv content type, to tell the 
    browser that the response has to be treated as a CSV file.
    '''
    response = HttpResponse(content_type='text/csv')
    # add a Content-Disposition header to indicate that the HTTP response contains an attached file
    response['Content-Disposition'] = content_disposition
    # ThisCSV writer object that will write to the response object.
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not
              field.many_to_many and not field.one_to_many]
    ''''
    #get the model fields dynamically using the get_fields() method of the model’s _meta
    options, and exclude many-to-many and one-to-many relationships.
    '''
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # Write data rows
    for obj in queryset:  # iterate over the given QuerySet
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response


# customize the display name for the action in the actions drop-down element of the administration site
export_to_csv.short_description = 'Export to CSV'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


def order_payment(obj):
    url = obj.get_stripe_url()
    if obj.stripe_id:
        html = f'<a href="{url}" target="_blank">{obj.stripe_id}</a>'
        return mark_safe(html)
    return ''


order_payment.short_description = 'Stripe payment'


def order_detail(obj):
    url = reverse('orders:admin_order_detail', args=[obj.id])
    return mark_safe(f'<a href="{url}">View</a>')


''''
def order_pdf(obj):
    url = reverse('orders:admin_order_pdf', args=[obj.id])
    return mark_safe(f'<a href="{url}">PDF</a>')


order_pdf.short_description = 'Invoice'
'''


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email',
                    'address', 'postal_code', 'city', 'paid', order_payment, 'created', 'updated', order_detail]
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]
    actions = [export_to_csv]
