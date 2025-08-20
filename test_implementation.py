#!/usr/bin/env python3
"""
Script de prueba para verificar la implementación de la entidad Room
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from models import Hotel, Room
from database import engine, SessionLocal
from sqlalchemy.orm import sessionmaker


def test_models():
    """Prueba que los modelos se pueden crear correctamente"""
    print("✅ Verificando modelos...")

    # Verificar que Hotel tiene la relación rooms
    if hasattr(Hotel, "rooms"):
        print("  ✅ Hotel tiene relación 'rooms'")
    else:
        print("  ❌ Hotel NO tiene relación 'rooms'")

    # Verificar que Room tiene la relación hotel
    if hasattr(Room, "hotel"):
        print("  ✅ Room tiene relación 'hotel'")
    else:
        print("  ❌ Room NO tiene relación 'hotel'")

    # Verificar campos de Room
    room_fields = [
        "id",
        "hotel_id",
        "name",
        "description",
        "price",
        "images",
        "created_at",
        "updated_at",
    ]
    for field in room_fields:
        if hasattr(Room, field):
            print(f"  ✅ Room tiene campo '{field}'")
        else:
            print(f"  ❌ Room NO tiene campo '{field}'")


def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("\n✅ Verificando conexión a base de datos...")
    try:
        # Crear sesión
        Session = sessionmaker(bind=engine)
        session = Session()

        # Probar consulta simple
        result = session.execute("SELECT 1")
        print("  ✅ Conexión a base de datos exitosa")

        session.close()
        return True
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        return False


def test_table_creation():
    """Prueba la creación de tablas"""
    print("\n✅ Verificando creación de tablas...")
    try:
        from models import Base

        Base.metadata.create_all(bind=engine)
        print("  ✅ Tablas creadas/verificadas exitosamente")
        return True
    except Exception as e:
        print(f"  ❌ Error creando tablas: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Probando implementación de la entidad Room...\n")

    test_models()

    if test_database_connection():
        test_table_creation()

    print("\n✨ Pruebas completadas!")
