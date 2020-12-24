from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from message_control.models import GenericFileUpload
from django.utils import timezone


class CustomUserManager(BaseUserManager):

    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("Username field is required")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_online = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "username"
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    class Meta:
        ordering = ("created_at",)


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, related_name="user_profile", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    caption = models.CharField(max_length=250)
    about = models.TextField()
    profile_picture = models.ForeignKey(
        GenericFileUpload, related_name="user_image", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ("created_at",)


class Favorite(models.Model):
    user = models.OneToOneField(CustomUser, related_name="user_favorites", on_delete=models.CASCADE)
    favorite = models.ManyToManyField(CustomUser, related_name="user_favoured")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        ordering = ("created_at",)


class Jwt(models.Model):
    user = models.OneToOneField(
        CustomUser, related_name="login_user", on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
