from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal

type_choices = (
    ('owner', 'Owner'),
    ('customer', 'Customer'),
)

class User(AbstractUser):
    user_type = models.CharField(max_length=10, choices=type_choices, default='customer')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Loan Tracking
    loan_taken = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loan_repaid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Blockchain details
    blockchain_address = models.CharField(max_length=255, unique=True, blank=True, null=True)
    nestcoin_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",
        blank=True
    )

    def add_money(self, amount):
        self.wallet_balance += amount
        self.save()
    
    def spend_money(self, amount):
        if self.wallet_balance >= amount:
            self.wallet_balance -= amount
            self.save()
            return True
        return False
    def increase_nestcoin(self, amount):
        self.nestcoin_balance += amount
        self.save()
    def spend_nestcoin(self, amount):
        if self.nestcoin_balance >= amount:
            self.nestcoin_balance -= amount
            self.save()
            return True
        return False
    def earn_money(self, amount,currency):
        self.total_earned += amount
        self.wallet_balance += amount
        if currency == 'NEST':
            self.nestcoin_balance += amount
        self.save()

    def take_loan(self, amount):
        """Allows a user to take a loan from the company."""
        loan = Loan.objects.create(user=self, amount=amount)
        self.loan_taken += amount
        self.wallet_balance += amount
        self.save()

        CompanyWallet.issue_loan(amount)  # Update company wallet
        return loan

    def repay_loan(self, amount):
        """Allows a user to repay their loan."""
        if self.wallet_balance < amount:
            raise ValueError("Insufficient funds to repay loan.")
        
        if amount > self.loan_taken - self.loan_repaid:
            raise ValueError("Repayment amount exceeds remaining loan balance.")

        self.wallet_balance -= amount
        self.loan_repaid += amount
        self.save()

        CompanyWallet.receive_loan_repayment(amount)  # Update company wallet
        return True

    def outstanding_loan(self):
        """Returns the remaining loan balance for the user."""
        return self.loan_taken - self.loan_repaid
    def increase_nestcoin(self, amount):
        """Increase NestCoin balance by 2% of transaction amount."""
        nestcoin_earned = amount * Decimal('0.02')
        self.nestcoin_balance += nestcoin_earned
        self.save()

# Company Wallet Model
class CompanyWallet(models.Model):
    blockchain_address = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Separate balances for USD and NestCoin
    balance_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_nest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    loans_given = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loans_repaid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @classmethod
    def add_commission(cls, amount, currency):
        """Adds commission earnings to the company wallet based on currency type."""
        company_wallet, created = cls.objects.get_or_create(id=1)
        if currency == 'USD':
            company_wallet.balance_usd += amount
        elif currency == 'NEST':
            company_wallet.balance_nest += amount
        company_wallet.save()

    @classmethod
    def issue_loan(cls, amount, currency):
        """Deducts loan amount from company wallet based on the currency."""
        company_wallet, created = cls.objects.get_or_create(id=1)
        if currency == 'USD':
            if company_wallet.balance_usd < amount:
                raise ValueError("Company wallet has insufficient USD funds for the loan.")
            company_wallet.balance_usd -= amount
        elif currency == 'NEST':
            if company_wallet.balance_nest < amount:
                raise ValueError("Company wallet has insufficient NestCoin funds for the loan.")
            company_wallet.balance_nest -= amount

        company_wallet.loans_given += amount
        company_wallet.save()

    @classmethod
    def receive_loan_repayment(cls, amount, currency):
        """Records loan repayment and adds money back to the correct wallet balance."""
        company_wallet, created = cls.objects.get_or_create(id=1)
        if currency == 'USD':
            company_wallet.balance_usd += amount
        elif currency == 'NEST':
            company_wallet.balance_nest += amount

        company_wallet.loans_repaid += amount
        company_wallet.save()

    def __str__(self):
        return f"Company Wallet - USD: {self.balance_usd}, NestCoin: {self.balance_nest}, Loans Given: {self.loans_given}, Loans Repaid: {self.loans_repaid}"



# Loan Model
class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateTimeField(auto_now_add=True)
    repaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Blockchain transaction ID for tracking
    blockchain_transaction_id = models.CharField(max_length=255, blank=True, null=True)

    def remaining_balance(self):
        """Returns remaining balance to be paid."""
        return self.amount - self.repaid_amount

    def __str__(self):
        return f"Loan({self.user.username}) - Taken: {self.amount}, Repaid: {self.repaid_amount}"

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    total_sales = models.PositiveIntegerField(default=0)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)  # Image upload directory

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # USD price
    nest_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # NestCoin price
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'owner'})
    created_at = models.DateTimeField(auto_now_add=True)
    sales_count = models.PositiveIntegerField(default=0)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

    # Blockchain integration
    blockchain_address = models.CharField(max_length=255, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name


class Sale(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'Standard Currency'),
        ('NEST', 'NestCoin'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'customer'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES,default=0)  # User-selected payment currency
    timestamp = models.DateTimeField(auto_now_add=True)

    # Blockchain transaction ID for tracking sale on-chain
    blockchain_transaction_id = models.CharField(max_length=255, blank=True, null=True)

    COMMISSION_RATE = Decimal('0.05')  # 5% commission to the company
    NESTCOIN_RATE = Decimal('0.02')  # 2% reward in NestCoin

    def save(self, *args, **kwargs):
        commission = self.amount * self.COMMISSION_RATE  # Calculate commission
        seller_earnings = self.amount - commission  # Amount after commission

        # Deduct money from customer based on chosen payment type
        if self.payment_currency == 'NEST':
            success = self.customer.spend_nestcoin(self.amount)
        else:
            success = self.customer.spend_money(self.amount)

        if success:
            self.product.sales_count += 1
            self.product.total_earned += seller_earnings
            self.product.owner.earn_money(seller_earnings, self.payment_currency)

            # Reward NestCoin based on purchase amount
            self.customer.increase_nestcoin(self.amount * self.NESTCOIN_RATE)

            # Update category earnings and sales count
            self.product.category.total_sales += 1
            self.product.category.total_earned += seller_earnings

            # Add commission to company wallet
            CompanyWallet.add_commission(commission, self.payment_currency)

            # Save all updates
            self.product.save()
            self.product.category.save()
            self.product.owner.save()
            super().save(*args, **kwargs)
        else:
            raise ValueError("Insufficient funds")



# Screen Time Tracking
class ScreenTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    time_spent = models.PositiveIntegerField(default=0)  # in seconds
    last_active = models.DateTimeField(default=now)

    def update_time(self, duration):
        self.time_spent += duration
        self.last_active = now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.category.name if self.category else 'Overall'} - {self.product.name if self.product else 'General'}: {self.time_spent}s"


# Owner Dashboard Stats
class OwnerStats(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'owner'})
    daily_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    yearly_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def update_earnings(self, amount):
        self.daily_earnings += amount
        self.monthly_earnings += amount
        self.yearly_earnings += amount
        self.save()

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def total_price(self):
        """Calculates total cart value."""
        return sum(item.total_price() for item in self.cartitems.all())

    def __str__(self):
        return f"{self.user.username}'s Cart"

class CartItem(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, related_name="cartitems", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        """Returns total price of a product based on quantity."""
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} --{self.category.name}"