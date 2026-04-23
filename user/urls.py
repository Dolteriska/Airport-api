from django.urls import path

from user.views import (CreateUserView,
                        ManageUserView,
                        DecoratedTokenObtainPairView,
                        DecoratedTokenRefreshView,
                        DecoratedTokenVerifyView)

app_name = "user"

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("token/",
         DecoratedTokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path("token/refresh/",
         DecoratedTokenRefreshView.as_view(),
         name="token_refresh"),
    path("token/verify/",
         DecoratedTokenVerifyView.as_view(),
         name="token_verify"),
    path("me/", ManageUserView.as_view(), name="manage"),
]
