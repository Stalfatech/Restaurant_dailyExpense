from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Sum
from django.conf import settings
from datetime import date, timedelta, timezone
from django.core.exceptions import ValidationError
from django.utils import timezone



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

    user_type = models.IntegerField(null=True,choices=USER_TYPE_CHOICES)
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True)

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
    ('Yoghurt - NFPC', 'Yoghurt - NFPC'),
    ('Grocery', 'Grocery'),
    ('Gas', 'Gas'),
    ('Vegetables', 'Vegetables'),
    ('Friday - Atta', 'Friday - Atta'),
    ('Pepsi / Cola', 'Pepsi / Cola'),
    ('Plastic', 'Plastic'),
    ('Meat & Chicken - Coral', 'Meat & Chicken - Coral'),
    ('Mutton / Paya / Liver', 'Mutton / Paya / Liver'),
    ('Porotta', 'Porotta'),
    ('Noodles', 'Noodles'),
    ('Jalebi', 'Jalebi'),
    ('Paneer', 'Paneer'),
    ('Water', 'Water'),
    ('Fish', 'Fish'),
    ('Rainbow Milk', 'Rainbow Milk'),
    ('Sweets - Gulab Jamun', 'Sweets - Gulab Jamun'),
    ('Bakery - Biscuits', 'Bakery - Biscuits'),
    ('Charcoal', 'Charcoal'),
    ('Grease Trap', 'Grease Trap'),
    ('Pest Control', 'Pest Control'),
    ('Petrol Bike 1', 'Petrol Bike 1'),
    ('Petrol Bike 2', 'Petrol Bike 2'),
    ('Misc Exp 1', 'Misc Exp 1'),
    ('Misc Exp 2', 'Misc Exp 2'),
    ('Grocery & Inventory', 'Grocery & Inventory'), ('Utilities', 'Utilities'), ('Rent', 'Rent'), ('Salaries', 'Salaries'), ('Miscellaneous', 'Miscellaneous'),
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
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    date = models.DateField()
    category = models.CharField(max_length=100, choices=EXPENSE_CATEGORIES)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], blank=True,
    null=True)
    purchase_type = models.CharField(max_length=10, choices=PURCHASE_TYPE)
    description = models.TextField(blank=True)
    amount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True,
    null=True
)
    amount_text = models.CharField(max_length=255, blank=True, null=True) 
    invoice = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_settled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    # APPROVAL SYSTEM
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def balance(self):
        if not self.amount:
         return 0
        return self.amount - self.paid_amount


    def save(self, *args, **kwargs):
        if self.amount and self.balance() <= 0:
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

    opening_balance = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0
)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_closed = models.BooleanField(default=False)
    class Meta:
        unique_together = ('branch', 'date')
        ordering = ['-date']
    def calculate_expenses(self):
        total = Expense.objects.filter(
            branch=self.branch,
            date=self.date,
            status="Approved"
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        self.expenses = total
    def calculate_closing(self):
        self.closing_balance = (
            (self.opening_balance or 0) +
            (self.cash_sales or 0) -
            (self.expenses or 0)
        )
    def get_opening_balance(branch, selected_date):
    
        previous_day = selected_date - timedelta(days=1)

        previous_cashbook = CashBook.objects.filter(
          branch=branch,
          date=previous_day
        ).first()

        if previous_cashbook:
           return previous_cashbook.closing_balance

        return 0

    def save(self, *args, **kwargs):
        self.calculate_expenses()
        self.calculate_closing()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch.name} - {self.date}"
    
class Staff(models.Model):

    ROLE_CHOICES = [
        ('Chef', 'Chef'),
        ('Helper', 'Helper'),
        ('Delivery', 'Delivery'),
        
    ]

    SALARY_TYPE_CHOICES = [
        ('Daily', 'Daily'),
        ('Monthly', 'Monthly'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='added_staff')
    staff_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    contact = models.CharField(max_length=10)
    dob = models.DateField(null=True, blank=True)  # Not mandatory
    joining_date = models.DateField()
    gender = models.CharField(max_length=10,choices=GENDER_CHOICES,default='Male')   # ✅ Add default
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,null=True,blank=True)
    def __str__(self):
        return self.name
    
    
    

class DailySale(models.Model):
    POS_TYPE_CHOICES = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
    )

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Dining
    breakfast = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dinner = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Delivery
    delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    breakfast_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lunch_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dinner_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # POS (Card Payments)
    pos_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pos_type = models.CharField(max_length=10, choices=POS_TYPE_CHOICES, default='Cash')

    # Auto Calculated
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    
    def calculate_totals(self):
    
        self.breakfast_total = self.items.filter(
            meal_type='Breakfast'
        ).aggregate(total=Sum('amount'))['total'] or 0

        self.lunch_total = self.items.filter(
            meal_type='Lunch'
        ).aggregate(total=Sum('amount'))['total'] or 0

        self.dinner_total = self.items.filter(
            meal_type='Dinner'
        ).aggregate(total=Sum('amount'))['total'] or 0

        self.delivery_total = self.deliveries.aggregate(
            total=Sum('amount')
        )['total'] or 0

        cash_part = (
            self.breakfast_total +
            self.lunch_total +
            self.dinner_total +
            self.delivery_total
        )

        self.cash_sales = cash_part
        self.total_sales = cash_part + self.pos_amount




    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.calculate_totals()
        super().save(update_fields=[
            'breakfast_total',
            'lunch_total',
            'dinner_total',
            'delivery_total',
            'cash_sales',
            'total_sales'
        ])

    def __str__(self):
        return f"{self.branch.name} - {self.date}"
    
    
class DailySaleItem(models.Model):
    
    MEAL_CHOICES = (
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
    )

    sale = models.ForeignKey(
        DailySale,
        on_delete=models.CASCADE,
        related_name='items'
    )

    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    item_name = models.CharField(max_length=100,null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)

    def __str__(self):
        return f"{self.sale.date} - {self.meal_type} - {self.item_name}"



class DeliveryPlatform(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class DeliverySale(models.Model):
    sale = models.ForeignKey(
        DailySale,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )
   staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Delivery'}
    )

    platform = models.ForeignKey(DeliveryPlatform, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)

    def __str__(self):
        return f"{self.sale.date} - {self.platform.name}"





class Salary(models.Model):
    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]


    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="salaries")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)

    salary_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # salary_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adjusted_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    salary_month = models.CharField(
    max_length=20,
    choices=MONTH_CHOICES,
    null=True,
    blank=True
)

    salary_year = models.IntegerField(
    null=True,
    blank=True
)
    payment_date = models.DateField(default=timezone.now)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True, blank=True)
    next_month_advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    next_month = models.CharField(
        max_length=20,
        choices=MONTH_CHOICES,
        null=True,
        blank=True
    )

    next_month_year = models.IntegerField(
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):

        if self.staff and self.staff.branch:
            self.branch = self.staff.branch

        self.balance_salary = self.salary_amount - (
            self.adjusted_advance + self.paid_amount
        )
        if self.next_month_advance_amount and self.next_month_advance_amount > 0:

            month_list = [m[0] for m in self.MONTH_CHOICES]
            current_index = month_list.index(self.salary_month)

            if current_index == 11:  # December
                self.next_month = month_list[0]
                self.next_month_year = self.salary_year + 1
            else:
                self.next_month = month_list[current_index + 1]
                self.next_month_year = self.salary_year
        else:
            self.next_month = None
            self.next_month_year = None

        super().save(*args, **kwargs)

        

    def __str__(self):
        return f"{self.staff.name} - {self.salary_month} {self.salary_year}"


    

class SalaryAdvance(models.Model):

    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    staff = models.ForeignKey(
        'Staff',
        on_delete=models.CASCADE,
        related_name="advances"
    )

    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # 🔥 How many months advance taken
    start_month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    start_year = models.IntegerField()
    months_covered = models.IntegerField(default=1)
    remaining_months = models.IntegerField(default=1)

    remaining_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    advance_date = models.DateField(default=timezone.now)

    payment_mode = models.CharField(
        max_length=10,
        choices=[('Cash', 'Cash'), ('Bank', 'Bank')]
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.remaining_amount = self.advance_amount
            self.remaining_months = self.months_covered

        if self.staff and self.staff.branch:
            self.branch = self.staff.branch

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff.name} - {self.start_month} {self.start_year} ({self.months_covered} months)"