# ecorutas-huila

Aplicación base para el **Parcial I**: acceso al sistema, cargue de menú y CRUD de **Perfil, Persona y Usuario** con base de datos relacional.

## Requisitos
- Python 3.10+
- pip

## Ejecutar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir en: `http://localhost:5000`

## Credenciales por defecto
- Usuario: `admin`
- Contraseña: `admin123`

## Funcionalidades incluidas
- Acceso al sistema con validaciones de campos vacíos y credenciales inválidas.
- Menú principal con acceso a gestiones:
  - Gestión Perfil
  - Gestión Persona
  - Gestión Usuario
- Registro de persona (desde el botón **Registrarse** en login).
- Recuperación de usuario/contraseña:
  - Si existe el usuario, registra evidencia de “envío” en `correo_recuperacion.log`.
  - Si no existe, informa que no está registrado.
- Borrado lógico por campo `estado` para Perfil, Persona y Usuario (inhabilitar/habilitar).

## Base de datos
La app usa SQLite para ejecución local (`ecorutas.db`) y contiene el modelo relacional solicitado:
- Un perfil puede estar en varios usuarios.
- Cada usuario solo tiene un perfil.
- Una persona puede tener un solo usuario y cada usuario pertenece a una persona.

También se incluye script SQL genérico para motores relacionales en `sql/schema.sql`.
