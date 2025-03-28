# Tecnologías y Conceptos Clave

## CRUD
Un acrónimo para las cuatro operaciones básicas de almacenamiento persistente:

- **C**reate (Crear): Agregar un nuevo registro a la base de datos.
- **R**ead (Leer o Consultar): Obtener datos desde la base de datos.
- **U**pdate (Actualizar): Modificar un registro existente.
- **D**elete (Eliminar): Eliminar un registro de la base de datos.

Estas operaciones son fundamentales en el desarrollo de aplicaciones web y están presentes en la mayoría de los sistemas que manejan datos.

---

## JSON (JavaScript Object Notation)
**JSON** es un formato ligero de intercambio de datos, basado en texto y fácil de leer tanto para humanos como para máquinas. Se utiliza ampliamente para la comunicación entre el frontend y el backend.

Ejemplo de un objeto JSON:

```json
{
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "juan@example.com"
}
```

JSON es el formato más común en APIs REST, permitiendo estructurar y transferir datos de manera eficiente.

---

## Python
**Python** es un lenguaje de programación interpretado, de alto nivel y multiparadigma. Se destaca por su sintaxis clara y legible, lo que facilita el desarrollo rápido de aplicaciones.

Ejemplo de código en Python:

```python
def saludar(nombre):
    return f"Hola, {nombre}!"

print(saludar("Mundo"))
```

Python es utilizado en múltiples áreas, como desarrollo web, inteligencia artificial, análisis de datos y automatización.

---

## Django (Framework)
**Django** es un framework de alto nivel para el desarrollo web en Python. Facilita la creación de aplicaciones robustas y escalables siguiendo el principio **"batteries included"** (viene con muchas funcionalidades listas para usar).

Características principales de Django:
- Utiliza el patrón **MTV (Modelo - Template - Vista)**.
- Incluye un ORM para interactuar con bases de datos sin escribir SQL manualmente.
- Proporciona autenticación de usuarios integrada.
- Permite la creación de APIs con Django REST Framework (DRF).

Ejemplo de una vista en Django:

```python
from django.http import JsonResponse

def saludo(request):
    return JsonResponse({"mensaje": "Hola desde Django!"})
```

---

## ¿Qué es un Patrón de Diseño?
Un **patrón de diseño** es una solución reutilizable a un problema común en el desarrollo de software. Los patrones ayudan a mejorar la organización del código, la mantenibilidad y la escalabilidad de las aplicaciones.

Ejemplo de patrones de diseño:
- **MVC (Model-View-Controller)**: Separación de datos, lógica y presentación.
- **Singleton**: Garantiza que una clase tenga solo una instancia.
- **Observer**: Permite la suscripción de eventos y notificaciones.

---

## Patrón MVT (Modelo - Vista - Template)
Django utiliza el patrón **MVT (Model - View - Template)**, una variación del conocido **MVC (Model - View - Controller)**.

Componentes del patrón MVT:
- **Modelo (Model)**: Representa la estructura de los datos y la lógica de la base de datos.
- **Vista (View)**: Contiene la lógica de negocio y responde a las solicitudes del usuario.
- **Template (Template)**: Define la presentación de los datos (HTML y frontend).

Ejemplo de cómo se relacionan:
1. Un usuario hace una petición a la URL.
2. Django ejecuta una **vista** correspondiente.
3. La vista consulta el **modelo** para obtener datos.
4. La vista envía esos datos a un **template**, que los renderiza en HTML.
5. El usuario recibe la página web generada.

---

## ORM (Object-Relational Mapping)
Un **ORM (Mapeo Objeto-Relacional)** es una herramienta que permite interactuar con bases de datos usando código en lugar de SQL.

### Beneficios del ORM:
- Evita escribir consultas SQL manualmente.
- Permite trabajar con bases de datos de forma más intuitiva usando clases y objetos.
- Facilita la migración entre distintos motores de bases de datos.

Ejemplo de un modelo en Django:

```python
from django.db import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
```

Consulta con el ORM:

```python
usuarios = Usuario.objects.all()  # Obtiene todos los usuarios
usuario = Usuario.objects.get(id=1)  # Obtiene un usuario específico
usuario.nombre = "Nuevo Nombre"
usuario.save()  # Guarda cambios en la base de datos
Usuario.objects.filter(email="test@example.com").delete()  # Elimina un usuario
```

---

## Framework vs. Librería
### ¿Qué es un Framework?
Un **framework** es un conjunto de herramientas y reglas que establecen una estructura base para el desarrollo de software. Un framework define el flujo de trabajo y la arquitectura de la aplicación, proporcionando componentes reutilizables.

Ejemplo de frameworks:
- **Django** (desarrollo web en Python).
- **Spring Boot** (desarrollo backend en Java).
- **React** (desarrollo frontend con JavaScript).

### ¿Qué es una Librería?
Una **librería** es un conjunto de funciones y utilidades que pueden ser utilizadas dentro de un programa sin imponer una estructura específica. A diferencia de un framework, una librería no define cómo se debe organizar el código.

Ejemplo de librerías:
- **NumPy** (cálculo numérico en Python).
- **Lodash** (utilidades para JavaScript).
- **Requests** (manejo de peticiones HTTP en Python).

Diferencia clave:
- Un **framework** dicta cómo se debe estructurar el código (inversión de control).
- Una **librería** es simplemente un conjunto de herramientas que el programador decide cómo y cuándo usar.

---

## ViewSet (Django REST Framework)
Un **ViewSet** es una clase que agrupa la lógica para las operaciones CRUD relacionadas con un modelo, simplificando la creación de endpoints de API.

Ejemplo de un `ViewSet` en Django REST Framework:

```python
from rest_framework import viewsets  
from .models import Usuario  
from .serializers import UsuarioSerializer  

class UsuarioViewSet(viewsets.ModelViewSet):  
    queryset = Usuario.objects.all()  
    serializer_class = UsuarioSerializer  
```

Esto crea automáticamente endpoints REST para listar, crear, actualizar y eliminar usuarios.

---

## Middleware (Django)
Un **middleware** es una capa de procesamiento de solicitudes y respuestas HTTP en Django. Se usa para funciones como autenticación, gestión de sesiones y seguridad.

Ejemplo de un middleware en `settings.py`:

```python
MIDDLEWARE = [  
    'django.middleware.security.SecurityMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',  
    'django.middleware.common.CommonMiddleware',  
    'django.middleware.csrf.CsrfViewMiddleware',  
    'django.middleware.auth.AuthenticationMiddleware',  
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  
]  
```

Un middleware comúnmente utilizado es **CORS**, para permitir peticiones desde dominios distintos.

---

## CORS (Cross-Origin Resource Sharing)
Es un mecanismo de seguridad del navegador que permite solicitudes HTTP entre diferentes dominios. Se debe configurar en el backend para permitir que el frontend (React) acceda a la API (Django).

Ejemplo de configuración en Django:

```python
INSTALLED_APPS = [  
    ...  
    'corsheaders',  
]  

MIDDLEWARE = [  
    ...  
    'corsheaders.middleware.CorsMiddleware',  
]  

CORS_ALLOWED_ORIGINS = [  
    "http://localhost:3000",  # React en desarrollo  
    "https://miappfrontend.com",  # Dominio en producción  
]  
```

---