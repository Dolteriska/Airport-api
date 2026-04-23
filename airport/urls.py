from django.urls import path, include
from rest_framework import routers

from airport.views import (
    CrewViewSet,
    AirportViewSet,
    AirplaneViewSet,
    RouteViewSet,
    FlightViewSet,
    OrderViewSet,
    TicketViewSet,
    AirplaneTypeViewSet,
    OccupationViewSet,
)
router = routers.DefaultRouter()
router.register("crews", CrewViewSet)
router.register("airports", AirportViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)
router.register("tickets", TicketViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("occupations", OccupationViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
