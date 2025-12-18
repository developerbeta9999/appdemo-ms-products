from django.core.management.base import BaseCommand
from confluent_kafka import Consumer
import json
import os
from product.models import Product

# IMPLEMENTACIÓN DE CQRS (Command Query Responsibility Segregation)
# Mientras que la LECTURA(HTTP) (Query) sigue siendo sincrona
# las peticiones de ESCRITURA (kafka) (Command) serán asincronas ya que se van a completar segun su turno en la cola de mensajeria
class Command(BaseCommand):
    '''Escucha productos creados desde Kafka'''
    def handle(self, *args, **options):
        conf = {
            'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'group.id': 'products-group',
            'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(conf)
        consumer.subscribe(['product-updates'])

        print('🚀 Worker iniciado. Esperando mensajes...')
        self.stdout.write(self.style.SUCCESS('Consumer escuchando...'))

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None: continue
                if msg.error():
                    print(f"Error: {msg.error()}")
                    continue

                # Procesar datos
                data = json.loads(msg.value().decode('utf-8'))
                print(f"📦 Recibido: {data}")

                if data['method'] == 'create':
                    body = data['body']
                    product, created = Product.objects.update_or_create(
                        product_uuid=body['product_uuid'],
                        defaults={
                        'name':body['name'],
                        'price':body['price']
                        }
                    )
                    # --- TU LÓGICA DE CONTROL ---
                    if created:
                        print(f"🔥 [NUEVO] He creado el producto '{product.name}' con ID: {product.id}")
                    else:
                        print(f"♻️ [ACTUALIZADO] El producto '{product.name}' ya existía. Datos actualizados.")

                    if product.price > 1000:
                         print("💰 ¡Es un producto caro!")

        except KeyboardInterrupt:
            pass
        finally:
            consumer.close()
