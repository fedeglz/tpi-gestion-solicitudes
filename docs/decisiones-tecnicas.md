# Decisiones técnicas

| ID | Decisión | Motivo | Alternativa descartada |
|----|----------|--------|------------------------|
| D-01 | Python 3 + solo librería estándar + `unittest` | Cero dependencias, corre en cualquier PC de la cátedra | pytest (agrega instalación) |
| D-02 | Escribir pruebas de caracterización y un *golden master* **antes** de refactorizar | Red de seguridad objetiva: demuestra que el comportamiento externo no cambia | Probar a mano |
| D-03 | Conservar el formato JSON y los mensajes de salida | Compatibilidad con datos existentes y con el contrato del usuario | Rediseñar el formato |
| D-04 | Refactorizar en pasos pequeños (R1…R5), cada uno con pruebas en verde | Un commit = un refactoring; fácil de revisar y revertir | Reescritura total |
| D-05 | Capas dominio / repositorio / servicio / reporte / cli | SRP y límites claros entre componentes | Mantener un módulo |
| D-06 | Inyección de dependencias por constructor (repositorio y reloj) | DIP; permite pruebas con repositorio en memoria y fecha fija | Singleton global |
| D-07 | Transiciones de estado como tabla (`TRANSICIONES`) | OCP: agregar un estado es agregar una fila | `if/elif` anidados |
| D-08 | **Cambio intencional**: JSON corrupto ahora se informa y no se pisa | Evita pérdida silenciosa de datos (smell #8) | Mantener el comportamiento heredado |
| D-09 | Mantener exit code 0 en errores | Cambiarlo altera el contrato; queda como mejora pendiente | Cambiar a exit 1 sin versionar |
