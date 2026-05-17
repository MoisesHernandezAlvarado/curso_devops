"""
🎟️ Lambda: Consultar Disponibilidad
GET /eventos/{evento_id}/disponibilidad

Retorna los asientos disponibles para un evento.
"""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def handler(event, context):
    evento_id = event["pathParameters"]["evento_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Consultar el evento
        cursor.execute(
            "SELECT * FROM eventos WHERE id = %s",
            (evento_id,)
        )
        evento = cursor.fetchone()

        if not evento:
            return response(404, {"error": "Evento no encontrado"})

        # Consultar asientos disponibles
        cursor.execute(
            """
            SELECT id, fila, numero, zona, precio
            FROM asientos
            WHERE evento_id = %s AND estado = 'disponible'
            ORDER BY zona, fila, numero
            """,
            (evento_id,)
        )
        asientos = cursor.fetchall()

        # Agrupar por zona para presentación más clara
        zonas = {}
        for asiento in asientos:
            zona = asiento["zona"]
            if zona not in zonas:
                zonas[zona] = {"disponibles": 0, "precio": asiento["precio"], "asientos": []}
            zonas[zona]["disponibles"] += 1
            zonas[zona]["asientos"].append({
                "id": asiento["id"],
                "fila": asiento["fila"],
                "numero": asiento["numero"],
            })

        cursor.close()
        conn.close()

        return response(200, {
            "evento": {
                "id": evento["id"],
                "nombre": evento["nombre"],
                "fecha": str(evento["fecha"]),
                "venue": evento["venue"],
            },
            "total_disponibles": len(asientos),
            "zonas": zonas,
        })

    except Exception as e:
        print(f"Error: {e}")
        return response(500, {"error": "Error interno del servidor"})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # Para apps móviles
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
