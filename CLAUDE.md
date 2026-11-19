Claude Code · Diseño e implementación de NEXUS ERP
Aplica los acuerdos comunes de AGENTS.md. Implementa el backend y las migraciones autorizadas para tu tarea.
Antes de implementar
Propón el diseño técnico y el contrato API con ejemplos de entradas, resultados y errores. Indica las interfaces internas que Codex necesita para preparar las pruebas y cita las reglas de negocio que respaldan cada decisión. Documenta la propuesta en docs/iterations/<tarea>/claude.md. Codex revisa la propuesta y el responsable aprueba el alcance.
Estructura y dependencias
Capa	Responsabilidad
api/	Rutas y esquemas HTTP. Valida la forma de la petición, invoca el caso de uso y traduce su resultado a HTTP. Justifica cualquier lógica excepcional en la ruta.
application/	Casos de uso, coordinación y puertos para sus dependencias. Invoca las reglas de dominio y coordina los pasos del caso de uso.
domain/	Entidades, valores y reglas de negocio en Python puro, independientes de FastAPI, del ORM y de proveedores externos.
infrastructure/	Adaptadores que implementan los puertos para persistencia y servicios como SSO o correo.


La API depende de aplicación y aplicación depende de dominio. Los adaptadores implementan los puertos definidos en aplicación. Conecta implementaciones concretas en el punto de composición de la aplicación.

Usa principios SOLID para mantener responsabilidades claras y dependencias intercambiables donde aporten valor. Usa el caso de uso directo para secuencias sencillas. Introduce un pipeline cuando las etapas necesiten componerse, probarse o reutilizarse por separado, y un orquestador cuando el flujo requiera coordinación explícita entre pasos o servicios. Explica qué problema resuelve cada patrón y mantén legible el recorrido de una petición.
Traspaso
Si Codex reporta un defecto, revisa el caso reproducible y su regla. Corrige la implementación dentro del alcance autorizado y devuelve la referencia del cambio para que Codex verifique el caso. Actualiza tu resumen con decisiones, interfaces, verificaciones y resultados. Publica tu rama para revisión siguiendo AGENTS.md.