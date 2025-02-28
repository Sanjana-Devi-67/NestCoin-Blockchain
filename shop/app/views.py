from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import SignupForm  # Ensure correct import
from .models import *

#home page
def home(request):
    return render(request, 'home.html')

# Signup View
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.wallet_balance = 1000  # Assign min balance
            user.save()
            login(request, user)
            return redirect('owner_dashboard' if user.user_type == 'owner' else 'customer_dashboard')       
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('owner_dashboard' if user.user_type == 'owner' else 'customer_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Owner Dashboard
@login_required
def owner_dashboard(request):
    if request.user.user_type != 'owner':
        return redirect('customer_dashboard')

    products = Product.objects.filter(owner=request.user)
    owner_stats, created = OwnerStats.objects.get_or_create(owner=request.user)

    context = {
        'user': request.user,
        'products': products,
        'daily_earnings': owner_stats.daily_earnings,
        'monthly_earnings': owner_stats.monthly_earnings,
        'yearly_earnings': owner_stats.yearly_earnings,
        'categories': Category.objects.all().order_by('-total_sales')  # Sorted by popularity
    }
    return render(request, 'owner_dashboard.html', context)

# Customer Dashboard
@login_required
def customer_dashboard(request):
    if request.user.user_type != 'customer':
        return redirect('owner_dashboard')

    categories = Category.objects.all().order_by('-total_sales')  # Sorted by sales/popularity
    products = Product.objects.all().order_by('-sales_count')  # Sorted by most purchased

    context = {
        'balance': request.user.wallet_balance,
        'categories': categories,
        'products': products
    }
    return render(request, 'customer_dashboard.html', context)

# Product Purchase View
@login_required
def purchase_product(request, product_id):
    product = Product.objects.get(id=product_id)
    
    if request.user.user_type != 'customer':
        return redirect('owner_dashboard')

    if request.method == 'POST':
        if request.user.spend_money(product.price):
            sale = Sale.objects.create(product=product, customer=request.user, amount=product.price)
            return redirect('customer_dashboard')
        else:
            return render(request, 'purchase_failed.html', {'message': 'Insufficient funds'})
    
    return render(request, 'purchase_product.html', {'product': product})

# Admin Panel (For Superusers)
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('customer_dashboard')

    users = User.objects.all()
    products = Product.objects.all()
    total_earnings = sum(user.total_earned for user in users)
    company_wallet = CompanyWallet.objects.first()

    context = {
        'users': users,
        'products': products,
        'total_earnings': total_earnings,
        'company_wallet': company_wallet.balance if company_wallet else 0
    }
    return render(request, 'admin_dashboard.html', context)
from django.shortcuts import get_object_or_404
from django.utils.timezone import now


def product_list(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Track screen time
    if request.user.is_authenticated:
        screen_time, created = ScreenTime.objects.get_or_create(
            user=request.user, product=product
        )
        screen_time.update_time(10)  # Assume user spends 10s on the page

    return render(request, 'product_detail.html', {'product': product})
from .forms import ProductForm
from .models import Product

@login_required
def add_product(request):
    if request.user.user_type != 'owner':  # Ensure only owners can add products
        return redirect('home')  # Redirect unauthorized users

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user  # Assign logged-in owner
            product.save()
            return redirect('product_list')  # Redirect after success
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Ensure the user has a cart, create one if not
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, category=product.category)
    
    if not created:
        cart_item.quantity += 1  # If item exists, increase quantity
        cart_item.save()
    
    return redirect('cart_view')

@login_required
def remove_from_cart(request, product_id):
    cart = Cart.objects.filter(user=request.user).first()  # Get the user's cart
    if cart:
        cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if cart_item:
            cart_item.delete()  # Remove only the selected product
    return redirect('cart_view')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .models import Cart, Sale, Product
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .models import Cart, Sale, Product
from decimal import Decimal

@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = cart.cartitems.all() if cart else []

    total_price_usd = sum(item.quantity * item.product.price for item in cart_items)
    total_price_nest = sum(item.quantity * item.product.nest_price for item in cart_items)

    if request.method == "POST":
        payment_currency = request.POST.get("payment_currency")  # USD or NEST

        if payment_currency == "NEST":
            if total_price_nest > request.user.nestcoin_balance:
                messages.error(request, "Insufficient NestCoin balance.")
                return redirect("cart_view")
            total_cost = total_price_nest
        elif payment_currency == "USD":
            if total_price_usd > request.user.wallet_balance:
                messages.error(request, "Insufficient USD balance.")
                return redirect("cart_view")
            total_cost = total_price_usd
        else:
            messages.error(request, "Invalid payment method.")
            return redirect("cart_view")

        for item in cart_items:
            price = item.product.nest_price if payment_currency == "NEST" else item.product.price
            total_item_cost = item.quantity * price

            try:
                sale = Sale(
                    product=item.product,
                    customer=request.user,
                    amount=total_item_cost,
                    payment_currency=payment_currency
                )
                sale.save()
            except ValueError as e:
                messages.error(request, str(e))
                return redirect("cart_view")

        cart.cartitems.all().delete()
        messages.success(request, "Purchase successful!")
        return redirect("cart_view")

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total_price_usd": total_price_usd,
        "total_price_nest": total_price_nest,
        "payment_methods": ["USD", "NEST"],
    })