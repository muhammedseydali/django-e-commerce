import json 

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone

from shop.models import Product, ProductImage, Category, Wishlist, Cart, OrderStatus, Order, Payment, PaymentMethod
from user.models import Address, Coupon, CustomUser, CouponUsage
from main.functions import paginate_instances



def product_all(request):
    sort_by_price = request.GET.get('sort_by_price')
    category_param = request.GET.get('category')
    q = request.GET.get('q')

    products = Product.objects.filter(is_show=True, category__is_blocked=False, is_deleted=False)

    if category_param and category_param != 'All':
        products = products.filter(category__name=category_param)

    if sort_by_price == 'low-to-high':
        products = products.order_by('price')
    elif sort_by_price == 'high-to-low':
        products = products.order_by('-price')
    
    if q:
        products = products.filter(Q(title__icontains=q))

    instances = paginate_instances(request, products, per_page=1)
    categories = Category.objects.filter(is_blocked=False, is_deleted=False)
    print(request.session.get('cart_count'))
    context = {
        'title': 'Male Fashion | Products',
        'products': instances,
        'categories': categories,
        'active_menu_item': "shop",
    }
    
    return render(request, 'product/shop.html', context)

   
def product_details(request, slug):
    product = get_object_or_404(Product, slug=slug)
    product_images = ProductImage.objects.filter(product=product)
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]

    context = {
        'title': f'Male Fashion | {product.title}',
        'product': product,
        'product_images': product_images,
        'related_products': related_products
    }
    return render(request, 'product/shop-details.html', context)


@login_required(login_url="/user/login/")
def product_wishlist(request):
    if request.user.is_authenticated:
        products = Wishlist.objects.filter(user=request.user, is_deleted=False)
        context = {
            'title': 'Male Fashion | Wishlist',
            'products': products
        }
        return render(request, 'product/shop-wishlist.html', context)
    else:
        return redirect('user:login')
    

@login_required(login_url="/user/login/")
def product_wishlist_add(request, pk):
    product = get_object_or_404(Product, id=pk)

    if Wishlist.objects.filter(user=request.user, product=product).exists():
        instance = Wishlist.objects.filter(user=request.user, product=product).first()
        instance.is_deleted = False
        instance.save()
    else:
        Wishlist.objects.create(
            product=product,
            user=request.user
        )

    data = {
        "success": True,
        "message": "success"
    }

    return JsonResponse(data)


@login_required(login_url="/user/login/")
def product_wishlist_remove(request, pk):
    product = get_object_or_404(Wishlist, id=pk, user=request.user)

    product.is_deleted = True
    product.save()

    wishlist_items = Wishlist.objects.filter(user=request.user, is_deleted=False)
    wishlist_count = wishlist_items.count()

    data = {
        "success": True,
        "message": "success",
        "count": wishlist_count
    }

    return JsonResponse(data)

@login_required(login_url="/user/login/")
def product_cart(request):
    products = Cart.objects.filter(user=request.user, is_deleted=False)

    total_amount = products.aggregate(
        total_amount=Sum(
            ExpressionWrapper(
                F('product__price') * F('qty'),
                output_field=DecimalField()
            )
        )
    )['total_amount'] or 0

    for item in products:
        item.total_price_of_product = item.product.price * item.qty
        item.save()
   
    context = {
        "title": "Male Fashion | Cart",
        "products" : products,
        'total_amount': total_amount

    }
    return render(request, 'product/shopping-cart.html', context)


@login_required(login_url="/user/login/")
def product_cart_add(request, pk):
    product = get_object_or_404(Product, id=pk)
    if Cart.objects.filter(user=request.user, product=product).exists():
        instance = Cart.objects.filter(user=request.user, product=product).first()
        instance.is_deleted = False
        if instance.qty < 1:
            instance.qty = 1
        instance.total_price_of_product = instance.product.price * instance.qty
        instance.save()
    else:
        Cart.objects.create(
            product=product,
            user=request.user,
            total_price_of_product=product.price
        )
    
    cart_count = Cart.objects.filter(user=request.user, is_deleted=False).count()
    request.session['cart_count'] = cart_count

    response_data = {
        "success": True,
        "title": "Added to Cart",
        "message": "Product is in cart now",
        "status": "success",
        "cart_count": cart_count
    }

    return JsonResponse(response_data)



@login_required(login_url="user/login/")
def update_product_quantity(request, pk):
    product = get_object_or_404(Cart, id=pk)

    action = request.POST.get('action') 

    if action == 'increment':
        if product.product.stock_unit - product.qty > 0:
            if product.qty < 10:
                product.qty += 1
            else:
                data = {
                    "exceeded": True,
                    "title" : "Quantity limit exceeded",
                    "message" : "Only 10 quantity per order is allowed",
                    "status" : "warning",
                }

                return JsonResponse(data)
        else:
            data = {
                    "exceeded": True,
                    "title" : "Quantity Not there",
                    "message" : "Sorry this much qty is not there",
                    "status" : "warning",
                }

            return JsonResponse(data)
        
    elif action == 'decrement':
        if product.qty > 1:
            product.qty -= 1
    
    product.total_price_of_product = product.product.price * product.qty

    product.save()

    products = Cart.objects.filter(user=request.user, is_deleted=False)

    total_amount = products.aggregate(
        total_amount=Sum(
            ExpressionWrapper(
                F('product__price') * F('qty'),
                output_field=DecimalField()
            )
        )
    )['total_amount'] or 0
    
    data = {
        'exceeded': False,
        'message' : "success",
        'qty' : product.qty,
        'amount': product.product.price * product.qty,
        'total_amount' : total_amount
    }

    return JsonResponse(data)


@login_required(login_url="/user/login/")
def product_cart_remove(request, pk):
    product = get_object_or_404(Cart, id=pk, user=request.user)

    product.is_deleted = True

    product.save()

    cart_count = Cart.objects.filter(user=request.user, is_deleted=False).count()
    request.session['cart_count'] = cart_count

    response_data = {
            "status" : "success",
            "title" : "Successfully Removed",
            "message" : "Product has been Successfully removed.",
            "cart_count" : cart_count
        }

    return HttpResponse(json.dumps(response_data), content_type="application/json")


#checkout
@login_required(login_url="/user/login/")
def product_checkout(request):

    user_addresses = Address.objects.filter(user=request.user, is_default=False)
    user_default_address = Address.objects.filter(user=request.user, is_default=True).first()


    current_datetime = timezone.now()

    valid_coupons = Coupon.objects.filter(active=True, valid_to__gte=current_datetime)
    products = Cart.objects.filter(user=request.user, is_deleted=False)

    total_amount = products.aggregate(
        total_amount=Sum(
            ExpressionWrapper(
                F('product__price') * F('qty'),
                output_field=DecimalField()
            )
        )
    )['total_amount'] or 0

    print(total_amount, 'amount')

    discount_amount = 0
    for item in products:
        print(item.total_price_of_product)
        discount_amount += item.total_price_of_product

    discount = False
    if discount_amount != total_amount:
        discount = True

    print(discount, discount_amount, total_amount, 'amount')

    context = {
        "title" : "Male Fashion | Product Checkout",
        "user_addresses": user_addresses,
        "user_default_address": user_default_address,
        "products": products,
        "coupons": valid_coupons,
        "total_amount": total_amount,
        "discount_amount": discount_amount,
        "discount" : discount
    }
    return render(request, 'product/checkout.html', context)


def product_discount(request):
    if request.method == 'POST':
        code = request.POST.get('coupon')

        # Check if the coupon exists or return an error
        coupon = get_object_or_404(Coupon, code=code)
        
        user = request.user
        products = Cart.objects.filter(user=user, is_deleted=False)

        # Calculate the total amount of the cart
        total_amount = sum(item.product.price * item.qty for item in products)

        # Check if the coupon has already been used by the user
        if CouponUsage.objects.filter(user=user).exists():
            response_data = {
                "error": True,
                "title": "Already used one coupon",
                "status": "warning",
            }
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        current_datetime = timezone.now()

        # Check if the coupon is valid
        if current_datetime > coupon.valid_to:
            response_data = {
                "title": "Coupon not available",
                "status": "error",
            }
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        # Check if the cart meets the minimum purchase amount requirement
        if total_amount <= coupon.min_purchase_amount:
            response_data = {
                "title": f"Minimum amount for this coupon is {coupon.min_purchase_amount}",
                "status": "error",
            }
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        # Apply the discount based on the coupon type
        discount_amount = 0
        if coupon.discount_type == 'amount':
            discount = coupon.amount_or_percent / 2
            for item in products:
                item.total_price_of_product -= discount
                discount_amount += item.total_price_of_product 
                item.save()
        else:
            for item in products:
                item.total_price_of_product = item.total_price_of_product - (item.total_price_of_product * (coupon.amount_or_percent / 200))
                discount_amount += item.total_price_of_product 
                item.save()

        # Create a coupon usage record for the user
        CouponUsage.objects.create(user=user, coupon=coupon)

        response_data = {
            "error": False,
            "title": "Discount applied",
            "status": "success",
            "total_amount": float(discount_amount),
        }

        return HttpResponse(json.dumps(response_data), content_type="application/json")
    else:
        # Handle other HTTP methods or return an appropriate response
        pass



@login_required(login_url="/user/login/")
def product_order(request):
    if request.method == 'POST':
        user = request.user
        payment_method = request.POST.get('payment_method')
        address = request.POST.get('address')

        products = Cart.objects.filter(user=user, is_deleted=False)
        if not products.exists():
            return JsonResponse({
                "status": "error",
                "title": "Cart Empty",
                "message": "Your cart is empty."
            })

        shipping_address = None
        if address:
            shipping_address = Address.objects.filter(user=user, id=address).first()
        if not shipping_address:
            shipping_address = Address.objects.filter(user=user, is_default=True).first() or Address.objects.filter(user=user).first()

        if not shipping_address:
            return JsonResponse({
                "status": "error",
                "title": "Address Required",
                "message": "Please add a shipping address before ordering."
            })

        order_status, _ = OrderStatus.objects.get_or_create(status="Pending")
        payment_type, _ = PaymentMethod.objects.get_or_create(payment_type="COD")

        if payment_method == "cash" or True:
            total_amount = 0
            order = None
            for item in products:
                order = Order.objects.create(
                    product=item.product,
                    user=user,
                    shipping_address=shipping_address,
                    order_status=order_status,
                    product_qty=item.qty,
                    order_total_price=item.product.price * item.qty
                )
                item.product.stock_unit = max(0, item.product.stock_unit - item.qty)
                item.product.save()
                total_amount += item.total_price_of_product

            if order:
                Payment.objects.create(
                    order=order,
                    user=user,
                    payment_method=payment_type,
                    transaction_id="COD",
                    purchased_price=total_amount
                )
            
            products.update(is_deleted=True)
            request.session['cart_count'] = 0
            
            response_data = {
                "status": "success",
                "title": "Order Placed Successfully",
                "message": "Thank you for your order! Your items will be delivered shortly.",
            }

            return JsonResponse(response_data)
        
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)



    
