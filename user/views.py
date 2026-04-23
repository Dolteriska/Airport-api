from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView,
                                            TokenVerifyView)

from user.serializers import UserSerializer


@extend_schema(tags=["User Authentication & Profile"],
               summary="requires unique login and password to register")
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )


@extend_schema(tags=["User Authentication & Profile"])
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(tags=["User Auth"], summary="Obtain JWT token pair")
class DecoratedTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["User Auth"], summary="Refresh JWT token")
class DecoratedTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(tags=["User Auth"], summary="Verify JWT token")
class DecoratedTokenVerifyView(TokenVerifyView):
    pass
