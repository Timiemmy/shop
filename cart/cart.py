from decimal import Decimal
from django.conf import settings
from ecom.models import Product
from coupons.models import Coupon


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session  # This store the current session to make it accessible to the other methods of the Cart class.
        # This try to get the cart from the current session using
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session If no cart is present in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        # get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            # This converts each item’s price back into decimal,
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0,
                                     'price': str(product.price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    @property
    # If the cart contains a coupon_id attribute, the Coupon object with the given ID is returned.
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    # If the cart contains a coupon, you retrieve its discount rate and return the amount to be deducted from the total amount of the cart.
    def get_discount(self):
        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()
        return Decimal(0)

    # Return the total amount of the cart after deducting the amount returned by the get_discount() method.
    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()
