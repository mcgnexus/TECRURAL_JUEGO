# 0012 — Cuentas, guardado y captación (Fase 6, revisada: correo y contraseña)

Fecha: 2026-11-10. Estado: juego con cuenta; producción pendiente de asesor legal.

- Registro con correo y contraseña (hash PBKDF2+salt, mínimo 8 caracteres, 5 intentos
  de acceso con bloqueo temporal de 15 min). Sin DNI (rechazado por diseño).
  Cuenta con sesión obligatoria para guardar versionado; efímeras sin cuenta siguen abiertas.
- Sesiones opacas 24 h (Bearer), sin contraseñas en cliente, logs o respuestas.
  Recuperación por enlace al correo (30 min, simulado en desarrollo).
  Acceso por propietario: partida con cuenta exige su sesión (403 ajenos, cuentas aisladas).
- Guardado versionado `POST /games/{id}/save`, `GET /versions`, restauración con
  conflicto 409 si la copia es anterior y sin `force` (nunca pérdida silenciosa).
  Backup exporta estado+historial+versiones; restaura migrando partidas antiguas
  (campos ausentes → valores actuales). Recuperación simulada devuelve `reset_debug` solo dev/test.
- Consentimiento comercial separado, opcional, no premarcado, con prueba y revocación
  (`POST /accounts/me/consent`); revocación detiene envíos (OUTBOX solo con consentimiento).
  Contacto con finalidad clara obligatoria. CRM bloqueado 503 sin proveedor/base/acuerdo/retención.
  Analítica agregada sin datos personales.
- Privacidad (`GET /privacy`): tratamiento, recuperación, retención hasta borrado,
  derechos acceso/export/borrado, revisión legal pendiente antes de producción.
