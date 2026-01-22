from django.contrib.gis.db import models as gis_models
from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

# -------------------------------
# Филиалы (Branches)
# -------------------------------
class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    club_id = models.UUIDField()  # можно сделать FK на Club
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    location = gis_models.PointField(null=True, blank=True)  # PostGIS Point
    work_hours = models.JSONField(default=dict, blank=True)  # {"mon": "9-18", "tue": "9-18"}
    icafe_api_url = models.URLField(blank=True, null=True)
    icafe_auth_token = models.CharField(max_length=255, blank=True)  # можешь шифровать через Fernet
    photos = models.JSONField(default=list, blank=True)  # массив URL

    def __str__(self):
        return self.name

# -------------------------------
# Зоны (Zones)
# -------------------------------
class Zone(models.Model):
    ZONE_TYPES = (
        ('PC', 'PC'),
        ('CONSOLE', 'Console'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=50)  # VIP, Standard
    type = models.CharField(max_length=10, choices=ZONE_TYPES)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    specs = models.JSONField(default=dict, blank=True)  # {"gpu": "RTX 4090", "monitor": "240Hz"}

    def __str__(self):
        return f"{self.branch.name} - {self.name}"

# -------------------------------
# Сидения / места (Seats)
# -------------------------------
class Seat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='seats')
    number = models.CharField(max_length=10)  # "A1", "B2"
    icafe_pc_name = models.CharField(max_length=50, blank=True)  # "PC-01" для iCafe
    map_x = models.FloatField(default=0.0)
    map_y = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.zone.name} - {self.number}"
