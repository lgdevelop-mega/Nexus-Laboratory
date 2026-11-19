NEXUS ERP · Login y acceso por empresa
Borrador funcional v0.1 · 18 de noviembre de 2026 · Backend

Claude implementa los casos aprobados. Codex deriva pruebas unitarias y mantiene la documentación. Los escenarios siguientes expresan resultados esperados y están pendientes de verificación.
Modelo funcional
Una identidad central en users puede tener una membresía por empresa en users_enterprises. El correo identifica al usuario entre vías de ingreso. Una membresía vigente habilita el acceso a una empresa activa. La empresa predeterminada es una preferencia global. La empresa activa de la sesión determina los permisos empresariales, configuraciones, borradores y solicitudes que corresponden al usuario.
Reglas de negocio
ID	Comportamiento
LOG-01	El despliegue habilita la empresa y su estructura de tenant antes de registrar usuarios en ella.
LOG-02	Un administrador registra al usuario convencional y le asigna su primera empresa, que queda como predeterminada.
LOG-03	El ingreso convencional utiliza correo y contraseña. Abre directamente en la única empresa disponible o, si hay varias, en la predeterminada.
LOG-04	Desde su configuración global, el usuario puede elegir como predeterminada una de sus empresas disponibles.
LOG-05	Cuando pierde acceso a la predeterminada, NEXUS guarda la empresa de su membresía vigente más antigua. Con cero membresías disponibles, deniega el ingreso convencional.
LOG-06	Para una empresa activa con SSO habilitado, un ticket válido para NEXUS basta para el alta inicial del usuario o de la membresía. El SSO abre en la empresa de origen.
LOG-07	El backend utiliza el correo obtenido al validar el ticket y aplica la tabla de decisión siguiente.
LOG-08	El usuario creado por SSO puede seguir entrando por esa vía y habilitar el acceso convencional al configurar su contraseña. Ambas vías comparten la identidad.
LOG-09	El permiso global usuario_multitenant se concede automáticamente con dos o más membresías vigentes y se revoca al quedar menos de dos.
LOG-10	Ese permiso permite cambiar a otra empresa disponible y operar con los permisos de destino. La selección de empresa predeterminada es una acción independiente.
LOG-11	Permisos especiales, cambios de rol y reactivaciones se solicitan por correo al administrador fuera de NEXUS. El usuario gestiona sus preferencias desde su perfil.
LOG-12	En ambas vías de alta, el usuario configura su primera contraseña mediante un enlace de un solo uso con vencimiento enviado al correo registrado. El administrador gestiona el reenvío.
LOG-13	El administrador inicia la recuperación por olvido. El usuario establece su contraseña con el enlace. Al completarla se cierra la sesión actual de NEXUS y continúa la sesión del proveedor SSO.
LOG-14	El cierre voluntario termina la sesión actual de NEXUS y conserva la del proveedor SSO.
LOG-15	Suspender al usuario bloquea el acceso global por ambas vías. Suspender o revocar una membresía bloquea el acceso a su empresa.
LOG-16	Si se desactiva la empresa de la sesión o se suspende o revoca la membresía activa, NEXUS cierra esa sesión y exige un nuevo ingreso.


Decisión ante un ticket SSO
Condición	Resultado
Ticket inválido, empresa inactiva o SSO deshabilitado	Rechazar el acceso y el alta por esa vía.
Usuario suspendido globalmente	Rechazar antes de crear membresías.
Correo nuevo	Crear usuario y membresía con perfil básico. La empresa de origen queda como predeterminada y activa.
Usuario existente sin membresía previa en origen	Reutilizar usuario y crear membresía básica. Abrir en origen y conservar la predeterminada vigente.
Membresía vigente en origen	Abrir en origen con el rol y permisos existentes.
Membresía suspendida o revocada en origen	Rechazar. Solo el administrador puede reactivar la membresía.


Casos de aceptación
Caso	Acción y resultado esperado	Reglas
CA-01	Ana tiene Saga predeterminada y Mega vigente. Por contraseña entra en Saga. Por SSO de Mega entra en Mega y conserva Saga como preferencia.	03, 04, 06
CA-02	Un correo nuevo llega por SSO de Mega. Se crea un usuario con membresía básica en Mega, su primera empresa.	06–08
CA-03	Un usuario de Saga entra por primera vez por SSO de Mega. Obtiene la segunda membresía y usuario_multitenant.	07, 09
CA-04	Un usuario vuelve por SSO a una empresa donde tiene rol especial. Conserva su rol.	07, 10
CA-05	Se revoca la membresía activa de Mega y solo queda Saga. Se cierra la sesión y se revoca usuario_multitenant. Un ticket de Mega no reactiva el acceso.	07, 09, 15, 16
CA-06	Se desactiva la predeterminada y quedan dos empresas. La de membresía vigente más antigua pasa a ser la predeterminada.	05
CA-07	Un usuario suspendido presenta contraseña correcta o ticket válido. Ambos ingresos se rechazan.	15
CA-08	Tras una recuperación gestionada por el administrador, se cierra la sesión actual de NEXUS y continúa la del proveedor SSO.	13


Decisiones pendientes
Quedan por confirmar la invalidación del enlace anterior al reenviar uno nuevo y la vigencia de la contraseña actual hasta completar el restablecimiento. La revocación de sesiones en otros dispositivos tras una recuperación se evaluará en una iteración posterior.