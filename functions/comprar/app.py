"""
🎟️ Lambda: Comprar Ticket
POST /eventos/{evento_id}/comprar

Body:
{
    "asiento_id": 42,
    "nombre_comprador": "Ana García",
    "email": "ana@ejemplo.com"
}

⚠️  El momento estrella del taller:
    Usamos SELECT FOR UPDATE para evitar que dos personas
    compren el mismo asiento al mismo tiempo.
    Esto es concurrencia real — el problema que Lambda resuelve a escala.
"""

import json
import os
import uuid
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

    # Validar body
    try:
        body = json.loads(event.get("body", "{}"))
        asiento_id = body["asiento_id"]
        nombre_comprador = body["nombre_comprador"]
        email = body["email"]
    except (KeyError, json.JSONDecodeError):
        return response(400, {
            "error": "Faltan campos requeridos: asiento_id, nombre_comprador, email"
        })

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ⚠️ MOMENTO ESTRELLA DEL TALLER:
        # SELECT FOR UPDATE bloquea el asiento mientras procesamos
        # Si dos Lambdas llegan al mismo tiempo, una espera — no hay doble venta
        cursor.execute(
            """
            SELECT a.*, e.nombre as evento_nombre, e.fecha
            FROM asientos a
            JOIN eventos e ON e.id = a.evento_id
            WHERE a.id = %s AND a.evento_id = %s
            FOR UPDATE
            """,
            (asiento_id, evento_id)
        )
        asiento = cursor.fetchone()

        if not asiento:
            return response(404, {"error": "Asiento no encontrado"})

        if asiento["estado"] != "disponible":
            return response(409, {
                "error": "Lo sentimos, ese asiento ya fue comprado 😔",
                "estado_actual": asiento["estado"],
            })

        # Generar folio único
        folio = str(uuid.uuid4())[:8].upper()

        # Marcar asiento como vendido
        cursor.execute(
            "UPDATE asientos SET estado = 'vendido' WHERE id = %s",
            (asiento_id,)
        )

        # Registrar la compra
        cursor.execute(
            """
            INSERT INTO tickets (folio, evento_id, asiento_id, nombre_comprador, email, total)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (folio, evento_id, asiento_id, nombre_comprador, email, asiento["precio"])
        )
        ticket = cursor.fetchone()

        conn.commit()
        cursor.close()

        return response(201, {
            "mensaje": "¡Compra exitosa!",
            "ticket": {
                "folio": folio,
                "evento": asiento["evento_nombre"],
                "fecha": str(asiento["fecha"]),
                "zona": asiento["zona"],
                "fila": asiento["fila"],
                "asiento": asiento["numero"],
                "comprador": nombre_comprador,
                "email": email,
                "total": float(asiento["precio"]),
                "comprado_en": str(ticket["created_at"]),
            }
        })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
        return response(500, {"error": "Error interno del servidor"})

    finally:
        if conn:
            conn.close()


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
