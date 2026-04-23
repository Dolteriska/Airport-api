from django.db import transaction
from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError

from airport.filters import FlightFilter
from airport.models import (Crew,
                            Airport,
                            Airplane,
                            Flight,
                            Order,
                            Route, Ticket, AirplaneType
                            )
from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from airport.serializers import (
    CrewSerializer,
    AirportSerializer,
    AirplaneSerializer,
    RouteSerializer,
    FlightSerializer,
    OrderSerializer,
    AssignCrewSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    AirplaneImageSerializer,
    TicketSerializer,
    AdminOrderSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    AirplaneTypeSerializer
)


@extend_schema(
    tags=["Crew Management"],
    description="**RESTRICTED**:"
                " Operations with crew members are only"
                " available for staff/admin users."
)
class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminUser, )


@extend_schema(tags=["Airplane Types"])
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminUser, )

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete airplane"
                          " because it is used in existing routes."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(summary="Get list of airports"),
    create=extend_schema(summary="Create new airport"),
    retrieve=extend_schema(summary="Get airport details"),
    update=extend_schema(summary="Update airport"),
    partial_update=extend_schema(summary="Partially update airport"),
    destroy=extend_schema(
        summary="Delete airport",
        responses={
            204: None,
            400: extend_schema(
                description="Cannot delete airport (Protected Error)")
        }
    ),
)
@extend_schema(tags=["Airports"])
class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete airport because"
                          " it is used in existing routes."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(summary="List all airplanes"),
    create=extend_schema(summary="Add a new airplane"),
    retrieve=extend_schema(summary="Get airplane details"),
    update=extend_schema(summary="Full update of an airplane"),
    partial_update=extend_schema(summary="Partial update of an airplane"),
    destroy=extend_schema(summary="Delete an airplane"),
    upload_image=extend_schema(
        summary="Upload an image to a specific airplane",
        description="Allows uploading an image file. Only for admin users.",
        responses={200: AirplaneImageSerializer}
    ),
)
@extend_schema(tags=["Airplanes"])
class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminUser, )

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Route Management"],
    description="**RESTRICTED**: Non safe operations with routes"
                " (delete, create) are only available for staff/admin users."
)
class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


@extend_schema_view(
    list=extend_schema(summary="List all flights"),
    create=extend_schema(summary="Add a new flight"),
    retrieve=extend_schema(summary="Get flight details"),
    update=extend_schema(summary="Full update of a flight"),
    partial_update=extend_schema(summary="Partial update of a flight"),
    destroy=extend_schema(summary="Delete a flight"),
    assign_crew=extend_schema(
        summary="assign crew to a flight",
        description="Allows assigning crew members"
                    " for a specific flight. Every flight"
                    " must have at least one pilot and one "
                    "flight attendant. Only for admin users.",
        responses={200: AssignCrewSerializer}
    ),
)
@extend_schema(tags=["Flights"])
class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects
    filter_backends = (DjangoFilterBackend, )
    filterset_class = FlightFilter

    @action(detail=True, methods=["POST"], url_path="assign-crew")
    def assign_crew(self, request, pk=None):
        flight = self.get_object()
        serializer = AssignCrewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            crew = serializer.validated_data["crew"]
            flight.crew.set(crew)
            try:
                flight.full_clean()
            except ValidationError as e:
                raise DRFValidationError(e.message_dict)
            flight.save()
        return Response({"status": "crew assigned"}, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Flight.objects.select_related(
            "route__source",
            "route__destination",
            "airplane"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "assign_crew":
            return AssignCrewSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List orders",
        description="Users see only their own orders."
                    " Staff sees all orders in the system."
    ),
    create=extend_schema(
        summary="Create an order",
        description="Users create orders for themselves."
                    " Staff can specify a user in the data."
    ),
    retrieve=extend_schema(
        summary="Get order details"),
    update=extend_schema(
        summary="Update an order (Staff only)"),
    partial_update=extend_schema(
        summary="Partially update an order (Staff only)"),
    destroy=extend_schema(
        summary="Delete an order (Staff only)"),
)
@extend_schema(
    tags=["Orders"],
    request=OrderSerializer,
    responses={200: OrderSerializer}
)
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()

    def get_permissions(self):
        if not self.request.user.is_staff and self.action == "create":
            return [IsAuthenticated()]
        return [IsAdminOrIfAuthenticatedReadOnly()]

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminOrderSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            user = serializer.validated_data.get("user", self.request.user)
            serializer.save(user=user)
        else:
            serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List tickets",
        description="Get a list of tickets."
                    " Regular users see only"
                    " tickets from their own orders."
    ),
    retrieve=extend_schema(
        summary="Get ticket details",
        description="Get detailed information"
                    " about a specific ticket"
                    " including flight and order details."
    ),
    create=extend_schema(
        summary="Create a new ticket",
        description="Book a seat on a flight."
                    " Requires a flight ID and an order"
                    " ID belonging to the user."
    ),
    update=extend_schema(summary="Update ticket (Admin only)"),
    partial_update=extend_schema(
        summary="Partially update ticket (Admin only)"),
    destroy=extend_schema(summary="Delete ticket (Admin only)"),
)
@extend_schema(tags=["Tickets"])
class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("flight__route", "order__user")

    def get_permissions(self):
        if not self.request.user.is_staff and self.action == "create":
            return [IsAuthenticated()]
        return [IsAdminOrIfAuthenticatedReadOnly()]

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(order__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketDetailSerializer
        return TicketSerializer
