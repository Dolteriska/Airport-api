from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.relations import SlugRelatedField

from airport.models import (
    Crew,
    Airport,
    Airplane,
    Order,
    Ticket,
    Flight,
    Route,
    Occupation,
    AirplaneType
)


class CrewSerializer(serializers.ModelSerializer):
    occupation = serializers.SlugRelatedField(
        many=False, queryset=Occupation.objects.all(),
        slug_field="name"
    )

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name", "occupation")


class AirplaneTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class OccupationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Occupation
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type =\
        serializers.SlugRelatedField(many=False,
                                     queryset=AirplaneType.objects.all(),
                                     slug_field="name")

    class Meta:
        model = Airplane
        fields = ("id", "name", "capacity", "airplane_type", "image")
        read_only_fields = ("image", )


class AirplaneImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    source = SlugRelatedField(many=False, queryset=Airport.objects.all(),
                              slug_field="name")
    destination = SlugRelatedField(many=False, queryset=Airport.objects.all(),
                                   slug_field="name")

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class FlightSerializer(serializers.ModelSerializer):
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True, slug_field="full_name"
    )

    class Meta:
        model = Flight
        fields = ("id",
                  "route",
                  "airplane",
                  "departure_time",
                  "arrival_time",
                  "crew")

        def validate(self, attrs):
            return attrs


class AssignCrewSerializer(serializers.Serializer):
    crew = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Crew.objects.all()
    )

    def validate(self, attrs):
        crew = attrs.get("crew", [])

        pilots = [m for m in crew if
                  m.occupation.name == "Pilot"]
        attendants = [m for m in crew if
                      m.occupation.name == "Flight attendant"]

        errors = {}
        if not pilots:
            errors["crew"] = "At least one pilot is required."
        if not attendants:
            current_errors = errors.get("crew", [])
            if isinstance(current_errors, str):
                current_errors = [current_errors]
            current_errors.append("At least one flight attendant is required.")
            errors["crew"] = current_errors
        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FlightListSerializer(FlightSerializer):
    route = serializers.StringRelatedField()
    airplane = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request and not request.user.is_staff:
            data.pop("crew", None)
        return data


class FlightDetailSerializer(FlightSerializer):
    route = serializers.StringRelatedField()
    airplane = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )

    class Meta:
        model = Flight
        fields = ("id",
                  "route",
                  "airplane",
                  "departure_time",
                  "arrival_time",
                  "crew")


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")

    class Meta:
        model = Order
        fields = ("id", "created_at", "user")


class AdminOrderSerializer(OrderSerializer):
    user = serializers.SlugRelatedField(
        queryset=get_user_model().objects.all(),
        slug_field="username"
    )

    class Meta(OrderSerializer.Meta):
        fields = ("id", "created_at", "user")


class TicketListSerializer(serializers.ModelSerializer):
    flight = serializers.StringRelatedField()
    order = OrderSerializer(many=False, read_only=False)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")


class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    def __init__(self, *args, **kwargs):
        super(TicketSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user and not request.user.is_staff:
            self.fields["order"].queryset\
                = Order.objects.filter(user=request.user)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")

    def validate_order(self, value):
        user = self.context["request"].user
        if not user.is_staff and value.user != user:
            raise serializers.ValidationError(
                "You can only add tickets to your own orders.")
        return value


class TicketDetailSerializer(TicketSerializer):
    flight = FlightDetailSerializer(many=False, read_only=True)
    order = OrderSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")
