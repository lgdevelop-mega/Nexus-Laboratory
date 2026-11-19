NEXUS ERP · Acuerdos comunes para los agentes
Borrador v0.1 para incorporar al repositorio nuevo. El primer alcance funcional comprende Login y Conciliación bancaria. Los ejemplos de otros repositorios sirven como referencia.
Lectura y autoridad
Lee este archivo, tu guía especializada y las reglas, contratos o secciones técnicas pertinentes a la tarea. Consulta las guías de arquitectura, seguridad, estilo y pruebas solo cuando correspondan. Las decisiones explícitas del responsable y las especificaciones aprobadas determinan el comportamiento esperado. El código y las pruebas describen el comportamiento existente. Si hay una contradicción, identifica las fuentes y la decisión necesaria. Avanza con el trabajo que pueda hacerse de forma independiente.
Ciclo de trabajo
1. Presenta el objetivo, las rutas a modificar, los cambios propuestos, las reglas aplicables, los criterios de aceptación y las verificaciones previstas. Espera la aprobación del alcance antes de editar código, pruebas o documentación de producto.
2. Trabaja en tu propio worktree y rama. Una vez aprobado el alcance, puedes ajustar los archivos incluidos. Si necesitas ampliarlo, pide aprobación para los cambios adicionales.
3. Registra la propuesta en tu Markdown de iteración antes de implementar. Ambos agentes usan el mismo identificador de tarea. Claude usa docs/iterations/<tarea>/claude.md y Codex usa docs/iterations/<tarea>/codex.md. Actualiza ese mismo archivo al entregar.
4. Si una regla o interfaz sigue pendiente, documenta opciones y escenarios. Espera su aprobación para la parte que dependa de ella.
5. Con la tarea aprobada, puedes hacer commits locales, publicar tu propia rama y abrir una solicitud de PR para revisión. El responsable humano decide el merge.
6. Al entregar, registra la rama y el PR, los archivos modificados, lo acordado frente a lo entregado, las verificaciones ejecutadas y sus resultados, los pendientes y cualquier traspaso al otro agente.
Estructura común
Cada módulo nuevo vive en app/<area>/<modulo>/ o en la ubicación equivalente aprobada y se organiza en api/, application/, domain/ e infrastructure/. Las pruebas reflejan el área, el módulo y la capa bajo tests/.

Claude propone el diseño técnico y el contrato API. Codex los contrasta con las reglas aprobadas. El responsable decide qué propuesta se adopta. Cuando las reglas y las interfaces internas pertinentes estén aprobadas, los agentes pueden trabajar en paralelo.