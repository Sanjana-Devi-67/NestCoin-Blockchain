from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Product, Sale, ScreenTime, OwnerStats, CompanyWallet,Cart,CartItem,Order


# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'wallet_balance', 'total_earned', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email','blockchain_address')
    ordering = ('id',)

admin.site.register(User)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_sales', 'total_earned')
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(Category, CategoryAdmin)


# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'price', 'sales_count', 'total_earned', 'created_at')
    list_filter = ('category', 'owner')
    search_fields = ('name', 'owner__username')
    ordering = ('-created_at',)

admin.site.register(Product, ProductAdmin)


# Sale Admin
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'amount', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('product__name', 'customer__username')
    ordering = ('-timestamp',)

admin.site.register(Sale, SaleAdmin)


# Screen Time Admin
class ScreenTimeAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'product', 'time_spent', 'last_active')
    list_filter = ('last_active',)
    search_fields = ('user__username', 'category__name', 'product__name')

admin.site.register(ScreenTime, ScreenTimeAdmin)


# Owner Stats Admin
class OwnerStatsAdmin(admin.ModelAdmin):
    list_display = ('owner', 'daily_earnings', 'monthly_earnings', 'yearly_earnings')
    search_fields = ('owner__username',)

admin.site.register(OwnerStats, OwnerStatsAdmin)


# Company Wallet Admin
class CompanyWalletAdmin(admin.ModelAdmin):
    list_display = ('balance_usd', 'balance_nest', 'loans_given', 'loans_repaid')

admin.site.register(CompanyWallet, CompanyWalletAdmin)


# Customize Admin Panel Title
admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Dashboard"
admin.site.index_title = "Manage Store Data"
