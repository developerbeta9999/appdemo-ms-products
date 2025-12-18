from django.db import models
import uuid

class Product(models.Model):
    product_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
