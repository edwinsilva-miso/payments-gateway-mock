# Mock de Pasarela de Pagos

Este proyecto implementa un mock (simulación) de una pasarela de pagos con autenticación JWT. El mock permite realizar operaciones básicas de procesamiento de pagos en un entorno de desarrollo o pruebas.

## Características

- **Autenticación JWT**: Protección de endpoints mediante tokens JWT
- **Control de acceso basado en roles**: Diferentes permisos según el tipo de cliente
- **Operaciones soportadas**:
  - Aprobar pagos
  - Consultar detalles de pagos
  - Reversar pagos (solo administradores)
  - Cancelar pagos
- **Dockerizado**: Fácil de desplegar y aislar del resto de la aplicación

## Requisitos

- Docker y Docker Compose
- Python 3.11+ (solo si quieres ejecutarlo sin Docker)

## Estructura del proyecto

```
payment-gateway-mock/
├── app.py                # Código principal del mock
├── requirements.txt      # Dependencias de Python
├── Dockerfile            # Configuración para construir la imagen Docker
└── docker-compose.yml    # Configuración para orquestar el contenedor
```

## Instalación y ejecución

### Con Docker (recomendado)

1. Clona este repositorio o copia los archivos en tu directorio de trabajo
2. Construye y ejecuta el contenedor:

```bash
docker-compose up -d
```

3. El mock estará disponible en http://localhost:8080

### Sin Docker

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación:

```bash
python app.py
```

3. El mock estará disponible en http://localhost:8080

## Autenticación

El mock utiliza autenticación basada en JWT (JSON Web Tokens). Para usar la API:

1. Obtén un token JWT usando tus credenciales de cliente
2. Incluye el token en todas las peticiones posteriores

### Credenciales predefinidas

El sistema incluye dos clientes predefinidos:

- **Admin**: 
  - client_id: `client1`
  - client_secret: `password1`
  - roles: `["admin"]`

- **Solo lectura**:
  - client_id: `client2`
  - client_secret: `password2`
  - roles: `["read-only"]`

## Endpoints de la API

### Autenticación

```
POST /api/v1/auth/token
```

**Request**:
```json
{
  "client_id": "client1",
  "client_secret": "password1"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5c...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Health Check

```
GET /health
```

**Response (200 OK)**:
```json
{
  "status": "UP",
  "timestamp": "2025-04-07T12:00:00.123456"
}
```

### Aprobar un pago

```
POST /api/v1/payments
```

**Headers**:
```
Authorization: Bearer {tu_token_jwt}
Content-Type: application/json
```

**Request**:
```json
{
  "amount": 100.50,
  "cardNumber": "4111111111111111",
  "cvv": "123",
  "expiryDate": "12/25",
  "currency": "USD"
}
```

**Response (201 Created o 402 Payment Required)**:
```json
{
  "id": "abc123...",
  "amount": 100.50,
  "currency": "USD",
  "cardNumber": "************1111",
  "status": "APPROVED",
  "timestamp": "2025-04-07T12:00:00.123456",
  "transactionReference": "TX-abc123...",
  "lastUpdated": "2025-04-07T12:00:00.123456",
  "processedBy": "client1"
}
```

### Consultar detalles de un pago

```
GET /api/v1/payments/{payment_id}
```

**Headers**:
```
Authorization: Bearer {tu_token_jwt}
```

**Response (200 OK)**:
```json
{
  "id": "abc123...",
  "amount": 100.50,
  "currency": "USD",
  "cardNumber": "************1111",
  "status": "APPROVED",
  "timestamp": "2025-04-07T12:00:00.123456",
  "transactionReference": "TX-abc123...",
  "lastUpdated": "2025-04-07T12:00:00.123456",
  "processedBy": "client1"
}
```

### Reversar un pago

```
POST /api/v1/payments/{payment_id}/reverse
```
> Nota: Solo disponible para clientes con rol de administrador

**Headers**:
```
Authorization: Bearer {tu_token_jwt}
```

**Response (200 OK)**:
```json
{
  "id": "abc123...",
  "amount": 100.50,
  "currency": "USD",
  "cardNumber": "************1111",
  "status": "REVERSED",
  "timestamp": "2025-04-07T12:00:00.123456",
  "transactionReference": "TX-abc123...",
  "lastUpdated": "2025-04-07T12:05:00.123456",
  "processedBy": "client1",
  "reversedBy": "client1"
}
```

### Cancelar un pago

```
POST /api/v1/payments/{payment_id}/cancel
```

**Headers**:
```
Authorization: Bearer {tu_token_jwt}
```

**Response (200 OK)**:
```json
{
  "id": "abc123...",
  "amount": 100.50,
  "currency": "USD",
  "cardNumber": "************1111",
  "status": "CANCELLED",
  "timestamp": "2025-04-07T12:00:00.123456",
  "transactionReference": "TX-abc123...",
  "lastUpdated": "2025-04-07T12:10:00.123456",
  "processedBy": "client1",
  "cancelledBy": "client1"
}
```

## Código de ejemplo para integración

### Cliente en Python

```python
import requests

class PaymentGatewayClient:
    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        
    def authenticate(self):
        """Obtiene un token JWT del servidor"""
        auth_url = f"{self.base_url}/api/v1/auth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(auth_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            return True
        else:
            print(f"Authentication failed: {response.text}")
            return False
    
    def _get_headers(self):
        """Genera los headers necesarios para autenticación"""
        if not self.token:
            self.authenticate()
            
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def process_payment(self, amount, card_number, cvv, expiry_date, currency="USD"):
        """Procesa un nuevo pago"""
        url = f"{self.base_url}/api/v1/payments"
        payload = {
            "amount": amount,
            "cardNumber": card_number,
            "cvv": cvv,
            "expiryDate": expiry_date,
            "currency": currency
        }
        
        response = requests.post(url, json=payload, headers=self._get_headers())
        
        if response.status_code in [201, 402]:  # Ambos son respuestas válidas (aprobado o rechazado)
            return response.json()
        else:
            # Reintentar si el token expiró
            if response.status_code == 401 and "expired" in response.text.lower():
                self.authenticate()
                return self.process_payment(amount, card_number, cvv, expiry_date, currency)
            
            print(f"Payment processing failed: {response.text}")
            return None
```

### Ejemplo de uso

```python
# Crear cliente
client = PaymentGatewayClient(
    base_url="http://localhost:8080",
    client_id="client1", 
    client_secret="password1"
)

# Procesar un pago
payment = client.process_payment(
    amount=129.99,
    card_number="4111111111111111",
    cvv="123",
    expiry_date="12/25"
)

if payment:
    payment_id = payment["id"]
    print(f"Payment processed: {payment}")
```

## Comportamientos simulados

### Tarjetas de prueba

- **Tarjetas aprobadas**: Cualquier número que no termine en `0000`
- **Tarjetas rechazadas**: Cualquier número que termine en `0000`

## Consideraciones de seguridad

- Este es un mock para desarrollo y pruebas, no para producción
- En un entorno de producción, considera:
  - Usar HTTPS/TLS para todas las comunicaciones
  - Implementar rate limiting
  - Utilizar un sistema de almacenamiento seguro para las credenciales
  - Rotar periódicamente las claves JWT

## Variables de entorno

- `JWT_SECRET_KEY`: Clave para firmar los tokens JWT (valor por defecto: `dev-secret-key`)

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.