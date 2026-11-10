# 0012 — Cuentas, guardado y captación (Fase 6)

Fecha: 2026-11-10. Estado: juego con cuenta verificada; producción pendiente de asesor legal.

- Registro estándar: teléfono E.164 verificado por código 6 dígitos (10 min, 5 envíos/hora,
  5 intentos, bloqueo temporal). Correo opcional. Sin DNI (rechazado por diseño).
  Teléfono verificado obligatorio para guardar versionado; efímeras sin cuenta siguen abiertas.
- Sesiones opacas 24 h (Bearer), sin claves en cliente; recuperación por nuevo código.
  Acceso por propietario: partida con cuenta exige su sesión (403 ajenos, cuentas aisladas).
- Guardado versionado `POST /games/{id}/save`, `GET /versions`, restauración con
  conflicto 409 si la copia es anterior y sin `force` (nunca pérdida silenciosa).
  Backup exporta estado+historial+versiones; restaura migrando partidas antiguas
  (campos ausentes → valores actuales). SMS simulado devuelve `code_debug` solo dev/test.
- Consentimiento comercial separado, opcional, no premarcado, con prueba y revocación
  (`POST /accounts/me/consent`); revocación detiene envíos (OUTBOX solo con consentimiento).
  Contacto con finalidad clara obligatoria. CRM bloqueado 503 sin proveedor/base/acuerdo/retención.
  Analítica agregada sin datos personales.
- Privacidad (`GET /privacy`): tratamiento, recuperación, retención hasta borrado,
  derechos acceso/export/borrado, revisión legal pendiente antes de producción.
