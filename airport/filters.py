from django_filters import rest_framework as filters
from airport.models import Flight


class FlightFilter(filters.FilterSet):
    source = filters.CharFilter(
        field_name="route__source__closest_big_city",
        lookup_expr="icontains")
    destination = filters.CharFilter(
        field_name="route__destination__closest_big_city",
        lookup_expr="icontains")

    class Meta:
        model = Flight
        fields = ["source", "destination"]
