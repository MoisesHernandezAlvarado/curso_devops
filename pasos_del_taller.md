# 🎟️ Guía de Replicación: Taller Serverless AWS + CI/CD

Esta es la recopilación exacta de todos los pasos y comandos que ejecutamos desde cero para lograr que el proyecto funcione en la nube con un flujo CI/CD automatizado.

---

## 1. Configuración de Base de Datos (Supabase)
AWS Lambda requiere que la conexión a la base de datos sea mediante **IPv4**.
1. Crear un proyecto en Supabase.
2. Ir al **SQL Editor** en el panel de Supabase, pegar el contenido de `scripts/schema.sql` y ejecutarlo para crear las tablas.
3. Ir a **Settings -> Database -> Connection Pooler**.
4. Seleccionar IPv4 y copiar el Host (ej. `aws-1-us-east-2.pooler.supabase.com`) y el usuario.

## 2. Configuración del Entorno Local
Actualizar el archivo `.env` en la raíz del proyecto para pruebas locales:
```env
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_NAME=postgres
DB_USER=tu_usuario_pooler
DB_PASSWORD=tu_password
```

## 3. Configuración de Accesos en AWS (IAM)
1. En la consola de AWS, ir a **IAM -> Users** y crear un nuevo usuario.
2. Otorgarle los siguientes permisos (políticas):
   - `AWSCloudFormationFullAccess`
   - `AmazonS3FullAccess`
   - `AWSLambda_FullAccess`
   - `AmazonAPIGatewayAdministrator`
   - `IAMFullAccess` *(Crucial para que pueda crear los roles de las Lambdas)*
3. Generar un **Access Key ID** y un **Secret Access Key**.
4. En tu computadora, vincular ese usuario ejecutando en la terminal:
```bash
aws configure
# Te pedirá: Access Key, Secret Key, Región (us-east-1), y formato (json)
```

## 4. Primer Despliegue Manual (AWS SAM)
Para crear la infraestructura inicial en AWS, usamos SAM CLI:
```bash
# 1. Empaquetar el código y sus dependencias (Python)
sam build

# 2. Desplegar interactivamente en AWS
sam deploy --guided
```
Durante las preguntas interactivas:
- **Stack Name:** `lambda-curso-stack`
- **Region:** `us-east-1`
- **Parámetros DB:** Pegar los valores del Connection Pooler de Supabase.
- **Allow SAM CLI IAM role creation:** `Y`
*(Al terminar, SAM imprime en color verde la URL pública de tu API).*

## 5. Pruebas de Funcionamiento de la API
Validar que la API pueda hablar con Supabase probando los endpoints con la URL resultante:
```bash
# Consultar Disponibilidad
curl -s https://[TU_URL_API].amazonaws.com/Prod/eventos/1/disponibilidad

# Comprar un Asiento
curl -X POST https://[TU_URL_API].amazonaws.com/Prod/eventos/1/comprar \
-H "Content-Type: application/json" \
-d '{"asiento_id": 10, "nombre_comprador": "Juan Perez", "email": "juan@ejemplo.com"}'
```

## 6. Automatización de CI/CD (GitHub Actions)
Para que los despliegues sean automáticos al hacer `git push`, realizamos dos correcciones en el archivo `.github/workflows/deploy.yml`:

1. **Arreglar los Tests:** Agregamos `PYTHONPATH=.` para que Python encontrara el módulo localmente.
2. **Arreglar el Deploy:** Agregamos explícitamente el nombre del stack y la región al comando `sam deploy` porque el bot no cuenta con el archivo local oculto de configuración.

El comando final en el workflow quedó así:
```yaml
sam deploy \
  --stack-name lambda-curso-stack \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    DBHost=${{ secrets.DB_HOST }} ...
```

### Configuración final en GitHub:
1. Ir al repositorio en GitHub -> **Settings -> Secrets and variables -> Actions**.
2. Crear 6 *Repository Secrets*:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `DB_HOST` (El IPv4 del pooler)
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`

### Ciclo Completado 🚀
A partir de aquí, cada vez que edites el código y corras:
```bash
git add .
git commit -m "Mi nuevo cambio"
git push
```
GitHub validará los tests en `pytest` y desplegará la nueva versión en AWS de manera 100% automática.
