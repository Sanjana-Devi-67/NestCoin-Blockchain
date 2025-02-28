from django.urls import path
from .views import (
    home,signup_view, login_view, owner_dashboard, customer_dashboard, purchase_product, admin_dashboard,product_detail,product_list,add_product,cart_view,add_to_cart,remove_from_cart
)
from . import blockchain_views 
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('owner_dashboard/', owner_dashboard, name='owner_dashboard'),
    path('customer_dashboard/', customer_dashboard, name='customer_dashboard'),
    path('purchase/<int:product_id>/', purchase_product, name='purchase_product'),
    
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),  # Admin Panel

    path('products/', product_list, name='product_list'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),

     path('add_product/', add_product, name='add_product'),

     path('cart/', cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),

    path("payment/", blockchain_views.payment_page, name="payment_page"),
    # path("check-balance/", blockchain_views.check_balance, name="check_balance"),
    # path("apply-loan/", blockchain_views.apply_for_loan, name="apply_for_loan"),
    path("make-transaction/", blockchain_views.make_transaction, name="make_transaction"),
    path("buy-product/", blockchain_views.buy_product, name="buy_product"),
    # path("register-user/", blockchain_views.register_user, name="register_user"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)