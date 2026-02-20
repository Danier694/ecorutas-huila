from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ecorutas-secret-key"
DB_PATH = Path("ecorutas.db")
MAIL_LOG = Path("correo_recuperacion.log")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS perfil (
            id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            estado INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS persona (
            id_persona INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT NOT NULL,
            numero_documento TEXT NOT NULL UNIQUE,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT,
            estado INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            id_perfil INTEGER NOT NULL,
            id_persona INTEGER NOT NULL UNIQUE,
            estado INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (id_perfil) REFERENCES perfil(id_perfil),
            FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
        );
        """
    )

    admin_perfil = conn.execute("SELECT id_perfil FROM perfil WHERE nombre='Administrador'").fetchone()
    if not admin_perfil:
        conn.execute(
            "INSERT INTO perfil (nombre, descripcion) VALUES (?, ?)",
            ("Administrador", "Acceso total al sistema"),
        )
        admin_perfil = conn.execute("SELECT id_perfil FROM perfil WHERE nombre='Administrador'").fetchone()

    admin_persona = conn.execute(
        "SELECT id_persona FROM persona WHERE numero_documento='1000000000'"
    ).fetchone()
    if not admin_persona:
        conn.execute(
            """INSERT INTO persona
                (tipo_documento, numero_documento, nombres, apellidos, correo, telefono)
                VALUES (?, ?, ?, ?, ?, ?)""",
            ("CC", "1000000000", "Admin", "Ecorutas", "admin@ecorutas.com", "3000000000"),
        )
        admin_persona = conn.execute(
            "SELECT id_persona FROM persona WHERE numero_documento='1000000000'"
        ).fetchone()

    admin_user = conn.execute("SELECT id_usuario FROM usuario WHERE username='admin'").fetchone()
    if not admin_user:
        conn.execute(
            "INSERT INTO usuario (username, password, id_perfil, id_persona) VALUES (?, ?, ?, ?)",
            ("admin", "admin123", admin_perfil["id_perfil"], admin_persona["id_persona"]),
        )

    conn.commit()
    conn.close()


@app.context_processor
def inject_now():
    return {"current_year": datetime.now().year}


def require_login():
    if "user_id" not in session:
        flash("Debe iniciar sesión para continuar.", "warning")
        return False
    return True


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Debe diligenciar usuario y contraseña.", "danger")
            return render_template("login.html")

        conn = get_db_connection()
        user = conn.execute(
            """SELECT u.*, p.nombres, p.apellidos, pr.nombre AS perfil_nombre
               FROM usuario u
               JOIN persona p ON p.id_persona = u.id_persona
               JOIN perfil pr ON pr.id_perfil = u.id_perfil
               WHERE u.username=? AND u.password=? AND u.estado=1 AND p.estado=1""",
            (username, password),
        ).fetchone()
        conn.close()

        if not user:
            flash("Usuario o contraseña inválidos, o usuario inactivo.", "danger")
            return render_template("login.html")

        session["user_id"] = user["id_usuario"]
        session["username"] = user["username"]
        session["nombre_completo"] = f"{user['nombres']} {user['apellidos']}"
        session["perfil"] = user["perfil_nombre"]
        return redirect(url_for("menu"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión finalizada.", "info")
    return redirect(url_for("login"))


@app.route("/menu")
def menu():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("menu.html")


@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Debe ingresar su usuario para recuperar credenciales.", "danger")
            return render_template("recuperar.html")

        conn = get_db_connection()
        user = conn.execute(
            """SELECT u.username, u.password, p.correo, p.nombres
               FROM usuario u
               JOIN persona p ON p.id_persona = u.id_persona
               WHERE u.username=?""",
            (username,),
        ).fetchone()
        conn.close()

        if not user:
            flash("El usuario no se encuentra registrado.", "danger")
            return render_template("recuperar.html")

        MAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with MAIL_LOG.open("a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat()}] Para: {user['correo']} | "
                f"Hola {user['nombres']}, su usuario es {user['username']} y su contraseña es {user['password']}\n"
            )

        flash("Su usuario y contraseña fue enviado al correo registrado.", "success")

    return render_template("recuperar.html")


@app.route("/perfiles", methods=["GET", "POST"])
def perfiles():
    if not require_login():
        return redirect(url_for("login"))
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO perfil (nombre, descripcion, estado) VALUES (?, ?, ?)",
            (
                request.form.get("nombre", "").strip(),
                request.form.get("descripcion", "").strip(),
                1 if request.form.get("estado") == "on" else 0,
            ),
        )
        conn.commit()
        flash("Perfil creado correctamente.", "success")
        conn.close()
        return redirect(url_for("perfiles"))

    data = conn.execute("SELECT * FROM perfil ORDER BY id_perfil DESC").fetchall()
    conn.close()
    return render_template("perfiles.html", perfiles=data)


@app.post("/perfiles/<int:perfil_id>/toggle")
def perfiles_toggle(perfil_id):
    if not require_login():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("UPDATE perfil SET estado = CASE WHEN estado=1 THEN 0 ELSE 1 END WHERE id_perfil=?", (perfil_id,))
    conn.commit()
    conn.close()
    flash("Estado del perfil actualizado.", "info")
    return redirect(url_for("perfiles"))


@app.route("/personas", methods=["GET", "POST"])
def personas():
    conn = get_db_connection()
    if request.method == "POST":
        conn.execute(
            """INSERT INTO persona
               (tipo_documento, numero_documento, nombres, apellidos, correo, telefono, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form.get("tipo_documento", "").strip(),
                request.form.get("numero_documento", "").strip(),
                request.form.get("nombres", "").strip(),
                request.form.get("apellidos", "").strip(),
                request.form.get("correo", "").strip(),
                request.form.get("telefono", "").strip(),
                1 if request.form.get("estado") == "on" else 0,
            ),
        )
        conn.commit()
        flash("Persona registrada correctamente.", "success")
        conn.close()
        return redirect(url_for("personas"))

    data = conn.execute("SELECT * FROM persona ORDER BY id_persona DESC").fetchall()
    conn.close()
    return render_template("personas.html", personas=data)


@app.post("/personas/<int:persona_id>/toggle")
def personas_toggle(persona_id):
    conn = get_db_connection()
    conn.execute("UPDATE persona SET estado = CASE WHEN estado=1 THEN 0 ELSE 1 END WHERE id_persona=?", (persona_id,))
    conn.commit()
    conn.close()
    flash("Estado de la persona actualizado.", "info")
    return redirect(url_for("personas"))


@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if not require_login():
        return redirect(url_for("login"))
    conn = get_db_connection()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO usuario (username, password, id_perfil, id_persona, estado) VALUES (?, ?, ?, ?, ?)",
            (
                request.form.get("username", "").strip(),
                request.form.get("password", "").strip(),
                int(request.form.get("id_perfil")),
                int(request.form.get("id_persona")),
                1 if request.form.get("estado") == "on" else 0,
            ),
        )
        conn.commit()
        flash("Usuario creado correctamente.", "success")
        conn.close()
        return redirect(url_for("usuarios"))

    usuarios_rows = conn.execute(
        """SELECT u.*, p.nombres, p.apellidos, pr.nombre AS perfil_nombre
           FROM usuario u
           JOIN persona p ON p.id_persona = u.id_persona
           JOIN perfil pr ON pr.id_perfil = u.id_perfil
           ORDER BY u.id_usuario DESC"""
    ).fetchall()
    perfiles_rows = conn.execute("SELECT id_perfil, nombre FROM perfil WHERE estado=1").fetchall()
    personas_rows = conn.execute(
        """SELECT p.id_persona, p.nombres, p.apellidos
           FROM persona p
           WHERE p.estado=1 AND p.id_persona NOT IN (SELECT id_persona FROM usuario)"""
    ).fetchall()

    conn.close()
    return render_template(
        "usuarios.html",
        usuarios=usuarios_rows,
        perfiles=perfiles_rows,
        personas=personas_rows,
    )


@app.post("/usuarios/<int:user_id>/toggle")
def usuarios_toggle(user_id):
    if not require_login():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("UPDATE usuario SET estado = CASE WHEN estado=1 THEN 0 ELSE 1 END WHERE id_usuario=?", (user_id,))
    conn.commit()
    conn.close()
    flash("Estado del usuario actualizado.", "info")
    return redirect(url_for("usuarios"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
