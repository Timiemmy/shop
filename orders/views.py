from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
# import weasyprint
from .models import OrderItem, Order
from .forms import OrderCreateForm
from .tasks import order_created
from cart.cart import Cart


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                         product=item['product'],
                                         price=item['price'],
                                         quantity=item['quantity'])
            # clear the cart
            cart.clear()
            # launch asynchronous task
            order_created.delay(order.id)
            # set the order in the session
            request.session['order_id'] = order.id
            # redirect for payment
            return redirect(reverse('payment:process'))
    else:
        form = OrderCreateForm()
    return render(request,
                  'orders/order/create.html',
                  {'cart': cart, 'form': form})


# decorator checks that both the is_active and is_staff fields of the user requesting the page are set to True.
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request,
                  'admin/orders/order/detail.html',
                  {'order': order})


''''
@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html',
                            {'order': order})  # use the render_to_string() function provided by Django to render orders/order/pdf.html.
    # generate a new HttpResponse object specifying the application/pdf content type
    response = HttpResponse(content_type='application/pdf')
    # the Content-Disposition header to specify the filename.
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    # use WeasyPrint to generate a PDF file from the rendered HTML code and write the file to the HttpResponse object
    weasyprint.HTML(string=html).write_pdf(response,
                                           stylesheets=[weasyprint.CSS(
                                               settings.STATIC_ROOT / 'css/pdf.css')])
    # You use the static file css/pdf.css to add CSS styles to the generated PDF file. Then, you load it from
    # the local path by using the STATIC_ROOT setting.
    return response
'''
