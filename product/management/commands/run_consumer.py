from django.core.management.base import BaseCommand
from confluent_kafka import Consumer
import json
import os
from product.models import Product

# IMPLEMENTACIÓN DE CQRS (Command Query Responsibility Segregation)
# Mientras que la LECTURA(HTTP) (Query) sigue siendo síncrona,
# las peticiones de ESCRITURA (kafka) (Command) serán asíncronas.
class Command(BaseCommand):
    help = 'Escucha productos creados desde Kafka'

    def handle(self, *args, **options):
        # Configuración del consumidor
        conf = {
            'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'group.id': 'products-group',
            'auto.offset.reset': 'earliest'
        }
        
        consumer = Consumer(conf)
        consumer.subscribe(['product-updates']) # Suscripción al tópico

        # Mensajes de inicio
        print('🚀 Worker iniciado. Esperando mensajes...')
        self.stdout.write(self.style.SUCCESS('Consumer escuchando...'))

        try:
            while True:
                # Polling de mensajes (espera 1.0s)
                msg = consumer.poll(1.0)
                
                if msg is None: 
                    continue
                
                if msg.error():
                    print(f"⚠️ Error de Kafka: {msg.error()}")
                    continue

                # --- BLOQUE DE PROCESAMIENTO PROTEGIDO ---
                try:
                    # 1. Decodificar el mensaje
                    raw_value = msg.value().decode('utf-8')
                    data = json.loads(raw_value)
                    print(f"📦 Recibido: {data}")

                    # 2. Validar método (Usamos .get para evitar crash si no existe la clave)
                    if data.get('method') == 'create':
                        body = data.get('body', {})
                        
                        # Validar que existan los datos mínimos antes de intentar crear
                        if not body.get('product_uuid'):
                            print("❌ Error: El mensaje no tiene 'product_uuid'. Saltando...")
                            continue

                        # 3. Lógica de Persistencia (Idempotencia)
                        product, created = Product.objects.update_or_create(
                            product_uuid=body['product_uuid'],
                            defaults={
                                'name': body.get('name', 'Sin Nombre'),
                                'price': body.get('price', 0.00)
                            }
                        )

                        # --- LÓGICA DE CONTROL ---
                        if created:
                            print(f"🔥 [NUEVO] He creado el producto '{product.name}' con ID: {product.id}")
                        else:
                            print(f"♻️ [ACTUALIZADO] El producto '{product.name}' ya existía. Datos actualizados.")

                        if product.price > 1000:
                             print("💰 ¡Es un producto caro!")
                    
                    else:
                        print(f"ℹ️ Método '{data.get('method')}' no soportado o ignorado.")

                except json.JSONDecodeError as e:
                    # ESTO ES LO QUE TE FALTABA: Captura errores de formato JSON
                    self.stdout.write(self.style.ERROR(f"❌ Error de formato JSON: {e}"))
                    print(f"   Contenido basura recibido: {msg.value()}")
                    continue # Importante: Sigue al siguiente mensaje, no cierra el programa

                except Exception as e:
                    # Captura cualquier otro error de lógica (base de datos, etc)
                    print(f"❌ Error inesperado procesando el mensaje: {e}")
                    continue

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("🛑 Deteniendo worker..."))
        finally:
            consumer.close()