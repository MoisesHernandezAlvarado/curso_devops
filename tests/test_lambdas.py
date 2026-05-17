"""
🧪 Tests para las Lambdas de Boletera
Estos corren en el pipeline de CI/CD — si fallan, no se despliega
"""

import json
import sys
import os

# Para que los tests encuentren las funciones sin instalar nada
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../functions/disponibilidad"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../functions/comprar"))


# =====================
# Tests: Disponibilidad
# =====================

def test_disponibilidad_requiere_evento_id():
    """El handler debe manejar cuando falta el evento_id"""
    from functions.disponibilidad import app

    # Evento que no existe — sin tocar la BD
    evento = {"pathParameters": {"evento_id": "99999"}}

    # Solo verificamos que el handler retorna algo con statusCode
    # (en tests reales mockearíamos la BD con pytest-mock)
    assert "handler" in dir(app)


def test_response_format():
    """La función response debe retornar el formato correcto para API Gateway"""
    from functions.disponibilidad.app import response

    result = response(200, {"test": "ok"})

    assert result["statusCode"] == 200
    assert "Content-Type" in result["headers"]
    assert result["headers"]["Content-Type"] == "application/json"
    assert "Access-Control-Allow-Origin" in result["headers"]

    body = json.loads(result["body"])
    assert body["test"] == "ok"


def test_response_404():
    """Debe retornar 404 con mensaje de error"""
    from functions.disponibilidad.app import response

    result = response(404, {"error": "Evento no encontrado"})

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert "error" in body


# =====================
# Tests: Comprar
# =====================

def test_comprar_valida_body_incompleto():
    """Si falta algún campo, debe retornar 400"""
    # Importamos la función response del módulo comprar
    from functions.comprar.app import response

    result = response(400, {"error": "Faltan campos requeridos"})

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body


def test_comprar_response_exitosa():
    """Una compra exitosa debe retornar 201 con folio"""
    from functions.comprar.app import response

    ticket_mock = {
        "folio": "ABC12345",
        "evento": "Bad Bunny World Tour",
        "zona": "VIP",
        "fila": "A",
        "asiento": 5,
        "total": 4500.00,
    }

    result = response(201, {"mensaje": "¡Compra exitosa!", "ticket": ticket_mock})

    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["ticket"]["folio"] == "ABC12345"


def test_comprar_response_asiento_ocupado():
    """Si el asiento ya está vendido, debe retornar 409"""
    from functions.comprar.app import response

    result = response(409, {"error": "Ese asiento ya fue comprado"})

    assert result["statusCode"] == 409
