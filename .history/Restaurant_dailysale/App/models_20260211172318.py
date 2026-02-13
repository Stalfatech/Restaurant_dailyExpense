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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)

    username = None
    email = models.EmailField(unique=True, max_length=191, null=True)

    user_type = models.IntegerField(null=True)

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