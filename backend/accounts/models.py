from common.models import BaseModel
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required!")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        has_password_login = True if password else False
        extra_fields.setdefault("has_password_login", has_password_login)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin, BaseModel):
    phone_regex = RegexValidator(
        regex=r"^\d{6,18}$", message="Phone number must be between 6 to 18 digits!"
    )

    username = None
    email = models.EmailField(unique=True)

    phone_number = models.CharField(
        validators=[phone_regex], max_length=18, blank=True, null=True
    )

    has_password_login = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    # @property
    # def cart_size(self):
    #     if not hasattr(self, "cart"):
    #         return 0

    #     from django.db.models import Sum

    #     return self.cart.items.aggregate(total=Sum("CartItem.quantity"))["total"] or 0


class Profile(BaseModel):
    """
    Model to represents user profile information.
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="user_profile"
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        null=True,
        blank=True,
    )
    bio = models.TextField(null=True, blank=True)
    # settings
    receive_emails = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"


class Address(BaseModel):
    ADDRESS_TYPES = [
        ("home", "Home"),
        ("postal", "Postal"),
        ("work", "Work"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address_type = models.CharField(
        max_length=10, choices=ADDRESS_TYPES, default="home"
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        # one address type per user — no duplicates
        unique_together = [["user", "address_type"]]

    def save(self, *args, **kwargs):
        # if this is set as default, unset all others
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.address_type}"
