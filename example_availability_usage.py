"""
Ejemplo de uso del sistema de Availability para Hyperfunnel

Este script muestra cómo usar los nuevos endpoints de availability
para gestionar la disponibilidad de habitaciones de hotel.
"""

import httpx
import asyncio
from datetime import date, timedelta
from uuid import UUID
import json

# Configuración de la API
BASE_URL = "http://localhost:8000"


async def create_sample_data():
    """Crear datos de ejemplo: hotel y habitaciones"""
    async with httpx.AsyncClient() as client:
        # 1. Crear un hotel
        hotel_data = {
            "name": "Hotel Paradise",
            "country": "España",
            "city": "Barcelona",
            "stars": 4,
            "images": [
                "https://example.com/hotel1.jpg",
                "https://example.com/hotel2.jpg",
            ],
        }

        hotel_response = await client.post(f"{BASE_URL}/hotels/", json=hotel_data)
        hotel = hotel_response.json()
        hotel_id = hotel["id"]
        print(f"✓ Hotel creado: {hotel['name']} (ID: {hotel_id})")

        # 2. Crear habitaciones (diferentes tipos)
        room_types = [
            {
                "name": "Habitación Estándar",
                "description": "Habitación cómoda con todas las comodidades básicas",
                "price": 80.0,
                "images": [
                    "https://example.com/standard1.jpg",
                    "https://example.com/standard2.jpg",
                ],
            },
            {
                "name": "Habitación Deluxe",
                "description": "Habitación espaciosa con vista al mar",
                "price": 120.0,
                "images": [
                    "https://example.com/deluxe1.jpg",
                    "https://example.com/deluxe2.jpg",
                ],
            },
            {
                "name": "Suite Ejecutiva",
                "description": "Suite lujosa con sala de estar separada",
                "price": 200.0,
                "images": [
                    "https://example.com/suite1.jpg",
                    "https://example.com/suite2.jpg",
                ],
            },
        ]

        room_ids = []
        for room_data in room_types:
            room_response = await client.post(
                f"{BASE_URL}/rooms/hotels/{hotel_id}/", json=room_data
            )
            room = room_response.json()
            room_ids.append(room["id"])
            print(
                f"✓ Habitación creada: {room['name']} (ID: {room['id']}) - €{room['price']}/noche"
            )

        return hotel_id, room_ids


async def setup_availability(room_ids):
    """Configurar disponibilidad para las habitaciones"""
    async with httpx.AsyncClient() as client:
        today = date.today()
        start_date = today + timedelta(days=1)  # Empezar mañana
        end_date = start_date + timedelta(days=30)  # 30 días de disponibilidad

        print(f"\n🗓️  Configurando disponibilidad del {start_date} al {end_date}")

        for i, room_id in enumerate(room_ids):
            # Configurar disponibilidad básica para cada tipo de habitación
            availability_data = {
                "room_id": room_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_rooms": 5,  # 5 habitaciones de cada tipo
                "available_rooms": 5,
                "is_blocked": False,
            }

            response = await client.post(
                f"{BASE_URL}/availability/range", json=availability_data
            )
            created_records = response.json()
            print(
                f"✓ Creados {len(created_records)} registros de disponibilidad para habitación {i+1}"
            )

            # Configurar precios especiales para algunos fines de semana
            weekend_dates = []
            current = start_date
            while current <= end_date:
                if current.weekday() >= 5:  # Sábado=5, Domingo=6
                    weekend_dates.append(current)
                current += timedelta(days=1)

            # Aumentar precio 30% los fines de semana para habitaciones Deluxe y Suite
            if i >= 1:  # Solo para habitaciones Deluxe y Suite (índices 1 y 2)
                for weekend_date in weekend_dates[
                    :5
                ]:  # Solo los primeros 5 fines de semana
                    # Obtener el precio base de la habitación
                    room_response = await client.get(f"{BASE_URL}/rooms/{room_id}")
                    room = room_response.json()
                    base_price = room["price"]
                    weekend_price = base_price * 1.3  # +30%

                    # Buscar el registro de disponibilidad para esta fecha
                    availability_response = await client.get(
                        f"{BASE_URL}/availability/?room_id={room_id}&start_date={weekend_date}&end_date={weekend_date}"
                    )
                    availability_records = availability_response.json()

                    if availability_records:
                        availability_id = availability_records[0]["id"]
                        update_data = {"price_override": weekend_price}

                        await client.put(
                            f"{BASE_URL}/availability/{availability_id}",
                            json=update_data,
                        )
                        print(
                            f"  🏷️  Precio especial weekend {weekend_date}: €{weekend_price:.2f}"
                        )


async def demonstrate_availability_search():
    """Demostrar búsqueda de disponibilidad"""
    async with httpx.AsyncClient() as client:
        print(f"\n🔍 Demostrando búsqueda de disponibilidad")

        # Buscar disponibilidad para los próximos 7 días
        today = date.today()
        search_start = today + timedelta(days=1)
        search_end = search_start + timedelta(days=7)

        search_data = {
            "start_date": search_start.isoformat(),
            "end_date": search_end.isoformat(),
            "min_rooms": 2,  # Necesitamos al menos 2 habitaciones
        }

        response = await client.post(
            f"{BASE_URL}/availability/search", json=search_data
        )
        availability_results = response.json()

        print(
            f"✓ Encontradas {len(availability_results)} opciones disponibles para {search_data['min_rooms']} habitaciones"
        )

        # Mostrar las primeras 5 opciones
        for i, result in enumerate(availability_results[:5]):
            effective_price = result.get("price_override") or result["room"]["price"]
            print(
                f"  📅 {result['date']}: {result['room']['name']} - {result['available_rooms']} disponibles - €{effective_price}/noche"
            )


async def demonstrate_room_blocking():
    """Demostrar bloqueo de habitaciones"""
    async with httpx.AsyncClient() as client:
        print(f"\n🚫 Demostrando bloqueo de fechas")

        # Obtener la primera habitación
        rooms_response = await client.get(f"{BASE_URL}/rooms/")
        rooms = rooms_response.json()

        if rooms:
            room_id = rooms[0]["id"]
            room_name = rooms[0]["name"]

            # Bloquear los próximos 3 días para mantenimiento
            today = date.today()
            block_start = today + timedelta(days=10)
            block_end = block_start + timedelta(days=2)

            response = await client.post(
                f"{BASE_URL}/availability/room/{room_id}/block-dates"
                f"?start_date={block_start}&end_date={block_end}"
            )
            result = response.json()

            print(
                f"✓ Bloqueadas fechas para {room_name} del {block_start} al {block_end}"
            )
            print(f"  Registros actualizados: {result['updated_records']}")
            print(f"  Registros creados: {result['created_records']}")


async def main():
    """Función principal del ejemplo"""
    print("🏨 Ejemplo de Sistema de Availability - Hyperfunnel")
    print("=" * 55)

    try:
        # 1. Crear datos de ejemplo
        hotel_id, room_ids = await create_sample_data()

        # 2. Configurar disponibilidad
        await setup_availability(room_ids)

        # 3. Demostrar búsqueda
        await demonstrate_availability_search()

        # 4. Demostrar bloqueo
        await demonstrate_room_blocking()

        print(f"\n✅ Ejemplo completado exitosamente!")
        print(f"\n📖 Endpoints disponibles:")
        print(f"   GET  /availability/ - Listar disponibilidad")
        print(f"   POST /availability/ - Crear disponibilidad individual")
        print(f"   POST /availability/range - Crear disponibilidad por rango")
        print(f"   POST /availability/search - Buscar disponibilidad")
        print(
            f"   GET  /availability/room/{{room_id}}/calendar - Calendario de habitación"
        )
        print(f"   POST /availability/room/{{room_id}}/block-dates - Bloquear fechas")
        print(f"   PUT  /availability/{{id}} - Actualizar disponibilidad")
        print(f"   DELETE /availability/{{id}} - Eliminar disponibilidad")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Asegúrate de que la API esté ejecutándose en http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())
