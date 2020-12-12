from django.contrib import admin
from .models import CustomUser, Jwt, Favorite


admin.site.register((CustomUser, Jwt, Favorite))
