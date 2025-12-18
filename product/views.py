from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer

# CLAVE: ReadOnlyModelViewSet (Solo permite GET, bloquea POST/PUT/DELETE)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
