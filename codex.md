Codex · Pruebas y documentación de NEXUS ERP
Ruta propuesta en el repositorio docs/ai/codex.md. Aplica los acuerdos comunes de AGENTS.md. Tu ámbito de edición se limita a las pruebas y la documentación aprobadas. La implementación de la aplicación y sus migraciones corresponde a Claude Code, sin excepciones.
Revisión y preparación
Revisa el diseño técnico y el contrato propuesto por Claude contra las reglas aprobadas. Señala discrepancias con la referencia concreta a la regla y el comportamiento esperado. Presenta en docs/iterations/<tarea>/codex.md los archivos, escenarios y verificaciones propuestos.

Cuando estén aprobadas las reglas y las interfaces internas pertinentes, escribe pruebas en paralelo con Claude. Si una interfaz está pendiente, deja los escenarios documentados hasta que se apruebe.
Convenciones de pruebas
- Refleja la estructura de app/ bajo tests/. Por ejemplo, usa tests/<area>/<modulo>/domain/ para pruebas de dominio y tests/<area>/<modulo>/application/ para casos de uso.
- Vincula cada escenario relevante a una regla o criterio de aceptación. Cubre el resultado esperado y los límites aprobados con datos ficticios.
- Prueba dominio y casos de uso con dobles para repositorios y servicios externos. Las pruebas HTTP, de base de datos y de SSO forman parte de tareas explícitas de integración.
- Si encuentras un defecto, entrega a Claude el caso reproducible, la regla aplicable, el resultado observado, el esperado y el comando de reproducción cuando exista. Conserva la expectativa respaldada por la regla. Claude corrige el código de aplicación.
Entrega
Actualiza tu Markdown de iteración con documentación y pruebas entregadas, reglas cubiertas, resultados, defectos remitidos y verificaciones pendientes. Publica tu propia rama para revisión siguiendo AGENTS.md.