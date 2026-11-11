# Privacidad y captación — juego (Fase 6 revisada: cuenta por correo y contraseña)

## Datos
Cuenta con correo y contraseña (mínimo 8 caracteres, guardada con hash+salt, nunca en claro). No se solicita DNI ni teléfono.
Finalidad: guardar partidas y recuperarlas, nunca recomendación real.

## Sesiones y abuso
Contraseña con hash PBKDF2+salt, 5 intentos de acceso con bloqueo temporal de 15 min.
Sesiones opacas 24 h por cabecera Bearer. Sin secretos ni contraseñas en cliente ni logs.

## Guardado
Efímera sin cuenta; con cuenta y sesión: versionado, restauración con 409 ante
conflicto salvo `force`, backup exportable e importable con migración de esquemas
antiguos (v1/v2 → v3 por `_restore_state`).

## Comercial y CRM
Consentimiento marketing separado, `false` por defecto, prueba con fecha y revocación
simple. Sin consentimiento no hay envíos comerciales. Contacto exige finalidad.
Sin salida a CRM hasta elegir proveedor y definir base jurídica, acuerdo encargado y retención.

## Derechos
Acceso (`GET /accounts/me`), exportación (`/export`), borrado (`DELETE /accounts/me`
elimina cuenta+sesiones+contactos). Retención: hasta borrado. Analítica solo agregada.

## Pendiente producción
Política de privacidad, contratos encargados, retención detallada, canales de contacto
y reglas del canal de correo con asesor competente; verificar legislación aplicable.
