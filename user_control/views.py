import jwt
from .models import Jwt, CustomUser, Favorite
from datetime import datetime, timedelta
from django.conf import settings
import random
import string
from rest_framework.views import APIView
from .serializers import (
    LoginSerializer, RegisterSerializer, RefreshSerializer, UserProfileSerializer, UserProfile, FavoriteSerializer
)
from django.contrib.auth import authenticate
from rest_framework.response import Response
from .authentication import Authentication
from chatapi.custom_methods import IsAuthenticatedCustom
from rest_framework.viewsets import ModelViewSet
import re
from django.db.models import Q, Count, Subquery, OuterRef


def get_random(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_access_token(payload):
    return jwt.encode(
        {"exp": datetime.now() + timedelta(minutes=5), **payload},
        settings.SECRET_KEY,
        algorithm="HS256"
    )


def get_refresh_token():
    return jwt.encode(
        {"exp": datetime.now() + timedelta(days=365), "data": get_random(10)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )


def decodeJWT(bearer):
    if not bearer:
        return None

    token = bearer[7:]
    decoded = jwt.decode(token, key=settings.SECRET_KEY)
    if decoded:
        try:
            return CustomUser.objects.get(id=decoded["user_id"])
        except Exception:
            return None


class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'])

        if not user:
            return Response({"error": "Invalid username or password"}, status="400")

        Jwt.objects.filter(user_id=user.id).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(
            user_id=user.id, access=access.decode(), refresh=refresh.decode()
        )

        return Response({"access": access, "refresh": refresh})


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.pop("username")

        CustomUser.objects.create_user(username=username, **serializer.validated_data)

        return Response({"success": "User created."}, status=201)


class RefreshView(APIView):
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            active_jwt = Jwt.objects.get(
                refresh=serializer.validated_data["refresh"])
        except Jwt.DoesNotExist:
            return Response({"error": "refresh token not found"}, status="400")
        if not Authentication.verify_token(serializer.validated_data["refresh"]):
            return Response({"error": "Token is invalid or has expired"})

        access = get_access_token({"user_id": active_jwt.user.id})
        refresh = get_refresh_token()

        active_jwt.access = access.decode()
        active_jwt.refresh = refresh.decode()
        active_jwt.save()

        return Response({"access": access, "refresh": refresh})


class UserProfileView(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedCustom, )

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()
        data.pop("page", None)
        keyword = data.pop("keyword", None)

        if keyword:
            search_fields = (
                "user__username", "first_name", "last_name", "user__email"
            )
            query = self.get_query(keyword, search_fields)
            try:
                return self.queryset.filter(query).filter(**data).exclude(
                    Q(user_id=self.request.user.id) |
                    Q(user__is_superuser=True)
                ).annotate(
                    fav_count=Count(self.user_fav_query(self.request.user))
                ).order_by("-fav_count")
            except Exception as e:
                raise Exception(e)

        result = self.queryset.filter(**data).exclude(
            Q(user_id=self.request.user.id) |
            Q(user__is_superuser=True)
        ).annotate(
            fav_count=Count(self.user_fav_query(self.request.user))
        ).order_by("-fav_count")
        return result

    @staticmethod
    def user_fav_query(user):
        try:
            return user.user_favorites.favorite.filter(id=OuterRef("user_id")).values("pk")
        except Exception:
            return []


    @staticmethod
    def get_query(query_string, search_fields):
        query = None  # Query to search for every search term
        terms = UserProfileView.normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    @staticmethod
    def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


class MeView(APIView):
    permission_classes = (IsAuthenticatedCustom, )
    serializer_class = UserProfileSerializer

    def get(self, request):
        data = {}
        try:
            data = self.serializer_class(request.user.user_profile).data
        except Exception:
            data = {
                "user": {
                    "id": request.user.id
                }
            }
        return Response(data, status=200)


class LogoutView(APIView):
    permission_classes = (IsAuthenticatedCustom, )

    def get(self, request):
        user_id = request.user.id

        Jwt.objects.filter(user_id=user_id).delete()

        return Response("logged out successfully", status=200)


class UpdateFavoriteView(APIView):
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = FavoriteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            favorite_user = CustomUser.objects.get(id=serializer.validated_data["favorite_id"])
        except Exception:
            raise Exception("Favorite user does not exist")

        try:
            fav = request.user.user_favorites
        except Exception:
            fav = Favorite.objects.create(user_id=request.user.id)

        favorite = fav.favorite.filter(id=favorite_user.id)
        if favorite:
            fav.favorite.remove(favorite_user)
            return Response("removed")

        fav.favorite.add(favorite_user)
        return Response("added")


class CheckIsFavoriteView(APIView):
    permission_classes = (IsAuthenticatedCustom,)

    def get(self, request, *args, **kwargs):
        favorite_id = kwargs.get("favorite_id", None)
        try:
            favorite = request.user.user_favorites.favorite.filter(id=favorite_id)
            if favorite:
                return Response(True)
            return Response(False)
        except Exception:
            return Response(False)

