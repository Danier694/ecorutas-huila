CREATE TABLE perfil (
  id_perfil INT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(80) UNIQUE NOT NULL,
  descripcion VARCHAR(180),
  estado TINYINT NOT NULL DEFAULT 1
);

CREATE TABLE persona (
  id_persona INT PRIMARY KEY AUTO_INCREMENT,
  tipo_documento VARCHAR(10) NOT NULL,
  numero_documento VARCHAR(20) UNIQUE NOT NULL,
  nombres VARCHAR(80) NOT NULL,
  apellidos VARCHAR(80) NOT NULL,
  correo VARCHAR(120) UNIQUE NOT NULL,
  telefono VARCHAR(20),
  estado TINYINT NOT NULL DEFAULT 1
);

CREATE TABLE usuario (
  id_usuario INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(120) NOT NULL,
  id_perfil INT NOT NULL,
  id_persona INT UNIQUE NOT NULL,
  estado TINYINT NOT NULL DEFAULT 1,
  CONSTRAINT fk_usuario_perfil FOREIGN KEY (id_perfil) REFERENCES perfil(id_perfil),
  CONSTRAINT fk_usuario_persona FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
);
