import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager



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
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Expense(models.Model):
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

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"
