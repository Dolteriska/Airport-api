from django.contrib import admin

from airport.models import (
    Occupation,
    Crew,
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Ticket,
    Flight,
    Order
)

admin.site.register(Occupation)
admin.site.register(Crew)
admin.site.register(Airport)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Route)
admin.site.register(Ticket)
admin.site.register(Order)


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    exclude = ("crew", )
