from datetime import date
import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models import Sum
from datetime import date




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, 'Admin'),
        (1, 'Manager'),
        (2, 'Staff'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)

    username = None
    email = models.EmailField(unique=True, max_length=191)

    user_type = models.IntegerField(null=True, choices=USER_TYPE_CHOICES)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class Register(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=191, null=True)
    contact = models.BigIntegerField(null=True)
    loginid = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registrations")

class Manager(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="manager_profile"
    )

    phone = models.BigIntegerField()
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    joining_date = models.DateField()
    photo = models.ImageField(upload_to='managers/')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name
    
    
    
    
from django.db import models
from django.core.validators import MinValueValidator
class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()

    def __str__(self):
        return self.name

PURCHASE_TYPE = (
    ('Cash', 'Cash'),
    ('Credit', 'Credit'),
)

EXPENSE_CATEGORIES = (
    ('Grocery & Inventory', 'Grocery & Inventory'),
    ('Utilities', 'Utilities'),
    ('Rent', 'Rent'),
    ('Salaries', 'Salaries'),
    ('Miscellaneous', 'Miscellaneous'),
)

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Expense(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    date = models.DateField()
    category = models.CharField(max_length=100, choices=EXPENSE_CATEGORIES)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    purchase_type = models.CharField(max_length=10, choices=PURCHASE_TYPE)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(0.01)])
    invoice = models.FileField(upload_to='invoices/')
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_settled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    # APPROVAL SYSTEM
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def balance(self):
        return self.amount - self.paid_amount

    def save(self, *args, **kwargs):
        if self.balance() <= 0:
            self.is_settled = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"



class CreditPayment(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField(default=date.today)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    total_paid = self.expense.payments.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    self.expense.paid_amount = total_paid
    self.expense.save()



class CashBook(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)

    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    is_closed = models.BooleanField(default=False)

    def calculate_closing(self):
        cash_expenses = Expense.objects.filter(
            branch=self.branch,
            date=self.date,
            purchase_type='Cash',
            status='Approved'
        ).aggregate(total=Sum('amount'))['total'] or 0

        self.closing_balance = self.opening_balance - cash_expenses
        self.save()
