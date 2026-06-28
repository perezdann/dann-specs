# Ejemplos

## Pensar y Encuadrar
**Tarea**: "Agregar exportación de usuarios"

**Deficiente**: Asume formato, alcance, método de entrega.
**Bueno**: Expone suposiciones sobre privacidad, formato, volumen y mecanismo de entrega antes de implementar.

## Simplicidad
**Tarea**: "Agregar lógica de descuentos"

**Deficiente**: Patrón strategy completo + configuración para un solo caso de uso.
**Bueno**: Función simple. Complejidad añadida solo cuando realmente se necesitan múltiples estrategias.

## Quirúrgico
**Tarea**: "Corregir validación para campo vacío"

**Deficiente**: Reformatea el archivo, agrega tipos, refactoriza funciones no relacionadas.
**Bueno**: Cambia solo la lógica de validación para el campo solicitado. Estilo y estructura intactos.

## Orientado a Objetivos + Verificación
**Tarea**: "Mejorar manejo de errores"

**Deficiente**: "Agregué try/catch en algunos lugares."
**Bueno**:
1. Identificó rutas de error específicas mediante logs.
2. Escribió pruebas fallidas para esos casos.
3. Implementó manejo mínimo.
4. Verificó que las pruebas pasan y las rutas de error están cubiertas.

## Roles (Ejemplos)

**Especialista de Dominio**:
- Declara suposiciones del dominio.
- Usa terminología precisa.
- Verifica contra reglas del dominio.

**Investigador**:
- Distingue hechos de interpretaciones.
- Proporciona fuentes trazables.
- Usa toma de notas quirúrgica.

**Educador**:
- Explicaciones progresivas.
- Ejemplos concretos + ejercicios.
- Anticipa conceptos erróneos.

Ver directorio roles/ para plantillas genéricas completas.

## Simulación Completa: Tarea de Software

**Solicitud del Usuario**: "Agregar limitación de tasa al endpoint de login."

**Aplicación Correcta de dann-specs (usando núcleo + variante software-development)**:

1. **Pensar y Encuadrar**:
   - Suposiciones: ¿Login es el único endpoint por ahora? ¿Límite por IP o por usuario? ¿Qué constituye abuso (5 intentos/min)?
   - ¿Se necesita clarificación? (Si no se proporciona: "Asumiré por IP, 5 intentos por minuto, devolver 429 con Retry-After.")

2. **Simplicidad + Quirúrgico**:
   - No crear un framework completo de rate-limiting con Redis, configuraciones y dashboards.
   - Agregar un pequeño middleware o decorador solo a la ruta de login.
   - Reutilizar logging existente si es posible.

3. **Orientado a Objetivos + Verificar**:
   - Meta: "Después de 5 inicios de sesión fallidos desde la misma IP en 60s, las solicitudes subsiguientes reciben 429. Los usuarios legítimos no son afectados."
   - Plan:
     - 1. Escribir prueba fallida (simular 6 solicitudes rápidas) → verificar que la prueba falla.
     - 2. Implementar límite de tasa mínimo en memoria.
     - 3. Ejecutar prueba → pasa.
     - 4. Ejecutar suite completa de pruebas + linter.
     - 5. Mostrar diff + salida de pruebas como evidencia.

**Deficiente (viola principios)**:
- Construye una clase RateLimiter genérica con 8 opciones de configuración.
- Refactoriza todo el módulo de autenticación "ya que estamos aquí".
- Dice "Agregué rate limiting" sin mostrar pruebas que pasen o evidencia.

## Simulación Completa: Rol Profesional (Médico)

**Solicitud del Usuario**: "Ayúdame a pensar en la presentación de este paciente: hombre 45 años, dolor torácico, dificultad respiratoria, viaje reciente."

**Aplicación Correcta (usando rol physician + principios fundamentales)**:

- **Pensar y Encuadrar**: "Suposiciones: Sin historial cardíaco conocido. Viaje reciente eleva preocupación por TEP. No asumiré diagnóstico."
- **Orientado a Objetivos**: "Meta: Generar un diferencial priorizado y próximos pasos recomendados que puedan verificarse contra guías (escala de Wells, dímero-D, etc.)."
- **Quirúrgico**: Actualizar solo la sección de evaluación/plan. No reescribir toda la nota.
- **Verificación**: "Según las guías actuales, recomiendo solicitar dímero-D + TAC si es positivo. Evidencia: puntuación de Wells = 6 (moderada)."

**Deficiente**: Inmediatamente dice "Esto es una embolia pulmonar" y ordena imágenes avanzadas sin exponer razonamiento ni alternativas.

---

[English version](EXAMPLES.md) | **Español**
