import os.path
import uuid
from django.utils import timezone

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Occupation(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    occupation = models.ForeignKey(
        Occupation,
        on_delete=models.PROTECT,
        related_name="crews",
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} {self.occupation}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


def airplane_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("airplanes/", filename)


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.PROTECT,
        related_name="airplanes")
    image = models.ImageField(null=True, upload_to=airplane_image_file_path)

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"


class Airport(models.Model):
    name = models.CharField(max_length=255)
    closest_big_city = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="routes_from"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="routes_to"
    )
    distance = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(source=models.F("destination")),
                name="prevent_same_airport_route"
            )
        ]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["destination"]),
            models.Index(fields=["source", "destination"]),

        ]

    def __str__(self):
        return f"{self.source} → {self.destination}"


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights",
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(
        Crew,
        blank=True,
        related_name="flights"
    )

    def clean(self):
        self.validate_flight()

    def validate_flight(self):
        now = timezone.now()
        if self.pk is None and self.departure_time < now:
            raise ValidationError({
                "departure_time": "Departure time"
                                  " cannot be in the past."})

        if self.departure_time >= self.arrival_time:
            raise ValidationError({
                "arrival_time": "Arrival time must be"
                                " later than departure time."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["route"]),
            models.Index(fields=["departure_time"]),
            models.Index(fields=["route", "departure_time"]),
        ]

    def __str__(self):
        return f"{self.route} at {self.departure_time}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

    @property
    def total_tickets(self):
        return self.tickets.count()

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row", "seat"],
                name="unique_ticket_per_seat"
            )
        ]

    def validate_ticket(self):
        airplane = self.flight.airplane

        if not airplane:
            return
        if not (1 <= self.row <= airplane.rows):
            raise ValidationError({
                "row": f"Row must be in range 1..{airplane.rows}"
            })

        if not (1 <= self.seat <= airplane.seats_in_row):
            raise ValidationError({
                "seat": f"Seat must be in range 1..{airplane.seats_in_row}"
            })

    def clean(self):
        self.validate_ticket()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.flight} | row {self.row}, seat {self.seat}"
