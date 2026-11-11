# Piloto hídrico personalizado — plan de implementación

**Objetivo:** comparar dos escenarios de riego sin registro, con previsión de la zona y supuestos explícitos, sin presentar recomendaciones profesionales.

**Arquitectura:** reutilizar el balance de juego sobre copias independientes del estado; obtener una única previsión para ambos escenarios. La interfaz reemplaza la pantalla anterior, sin borrar su código ni los cambios locales existentes.

**Restricciones:** nunca sustituir silenciosamente una previsión incompleta por clima ficticio; informar fuente, fecha, zona y supuestos; no estimar volumen a partir de duración sin caudal; mantener el modo profesional bloqueado.

## Tareas

1. **Previsión y ubicación:** incorporar búsqueda de municipio y datos meteorológicos, validar cobertura y procedencia, detenerse ante errores o huecos. Probar municipio inexistente, proveedor indisponible, series incompletas y fechas.
2. **Comparador no destructivo:** definir entradas acotadas y simular ambos escenarios desde estados independientes usando la misma previsión. Probar reproducibilidad, igualdad de entradas, ordenación y ausencia de modificaciones en partidas.
3. **Interfaz:** presentar finca de ejemplo o formulario gradual, opciones de riego y evolución por día; explicar incertidumbre y datos omitidos. Probar teclado, móvil, entradas incompletas y errores de proveedor.
4. **Verificación:** ejecutar suite, compilación y pruebas del flujo en navegador; comprobar que la tabla previa y los cambios locales no se pierden. No desplegar automáticamente sin comprobación del proveedor y del comportamiento de producción.
