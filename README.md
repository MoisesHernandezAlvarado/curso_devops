# 🎟️ Boletera Serverless
### Demo para taller universitario — Lambda + API Gateway + RDS + CI/CD

---

## Estructura del proyecto

```
boletera/
├── template.yaml                    # SAM: define las Lambdas y la API
├── functions/
│   ├── disponibilidad/
│   │   ├── app.py                   # GET /eventos/{id}/disponibilidad
│   │   └── requirements.txt
│   └── comprar/
│       ├── app.py                   # POST /eventos/{id}/comprar
│       └── requirements.txt
├── scripts/
│   └── schema.sql                   # Tablas + datos de prueba
├── tests/
│   └── test_lambdas.py              # Tests del pipeline CI/CD
└── .github/
    └── workflows/
        └── deploy.yml               # CI/CD con GitHub Actions
```

---

## Setup antes del taller (15 min)

### 1. RDS PostgreSQL
```bash
# Crea una instancia RDS PostgreSQL en AWS (db.t3.micro es suficiente)
# Corre el schema con tus datos de conexión:
psql -h TU_HOST -U admin -d boletera -f scripts/schema.sql
```

### 2. Variables de entorno locales
```bash
export DB_HOST=tu-rds-host.amazonaws.com
export DB_NAME=boletera
export DB_USER=admin
export DB_PASSWORD=tu_password
```

### 3. Probar localmente con SAM
```bash
# Instalar SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
sam build
sam local start-api
```

### 4. GitHub Secrets (para el CI/CD)
En tu repo → Settings → Secrets → Actions:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

---

## Endpoints de la demo

### Consultar disponibilidad
```bash
GET /eventos/1/disponibilidad

# Respuesta:
{
  "evento": {
    "nombre": "Bad Bunny World Tour 2026",
    "fecha": "2026-08-15",
    "venue": "Foro Sol, Ciudad de México"
  },
  "total_disponibles": 127,
  "zonas": {
    "VIP": { "disponibles": 17, "precio": 4500.00 },
    "General": { "disponibles": 95, "precio": 1200.00 },
    "Palco": { "disponibles": 5, "precio": 8000.00 }
  }
}
```

### Comprar ticket
```bash
POST /eventos/1/comprar
Content-Type: application/json

{
  "asiento_id": 10,
  "nombre_comprador": "Ana García",
  "email": "ana@ejemplo.com"
}

# Respuesta exitosa:
{
  "mensaje": "🎟️ ¡Compra exitosa!",
  "ticket": {
    "folio": "A3F9B21C",
    "evento": "Bad Bunny World Tour 2026",
    "zona": "VIP",
    "fila": "A",
    "asiento": 10,
    "total": 4500.00
  }
}

# Si el asiento ya está vendido:
HTTP 409
{ "error": "Lo sentimos, ese asiento ya fue comprado 😔" }
```

---

## El momento estrella del taller 🌟

En `functions/comprar/app.py` busca el comentario `⚠️ MOMENTO ESTRELLA`:

```python
# SELECT FOR UPDATE bloquea el asiento mientras procesamos
# Si dos Lambdas llegan al mismo tiempo, una espera — no hay doble venta
cursor.execute("""
    SELECT ... FROM asientos
    WHERE id = %s FOR UPDATE
""", (asiento_id,))
```

**Pregúntales:** *"¿Qué pasa si 500 personas intentan comprar el mismo asiento al mismo tiempo?"*
Luego muéstrales cómo `SELECT FOR UPDATE` resuelve exactamente eso.

---

## CI/CD — El flujo completo

```
git push → GitHub Actions
              ├── Job 1: pytest tests/
              │     ✅ pasa → continúa
              │     ❌ falla → NO despliega (producción protegida)
              └── Job 2: sam build + sam deploy
                        → Lambda actualizada en AWS ✨
```

**Demo en vivo:** rompe un test a propósito, haz push, muestra cómo el pipeline falla y protege producción.
