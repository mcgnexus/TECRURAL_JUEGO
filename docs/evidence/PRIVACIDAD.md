# Privacidad y captación — juego (Fase 6, pendiente asesor antes de producción)

## Datos
Teléfono verificado (E.164) para guardar/recuperar; correo opcional. No se solicita DNI.
Finalidad: cuenta de juego, nunca recomendación real.

## Sesiones y abuso
Códigos 6 dígitos/10 min, 5 envíos por hora, 5 intentos, bloqueo temporal.
Sesiones opacas 24 h por cabecera Bearer. Sin secretos en cliente ni logs.

## Guardado
Efímera sin cuenta; con cuenta verificada: versionado, restauración con 409 ante
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
y reglas del canal SMS/correo con asesor competente; verificar legislación aplicable.
