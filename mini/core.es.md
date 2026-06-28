# dann-specs — Núcleo Mini (Alta Eficiencia)

Usa este bloque compacto cuando el contexto sea limitado o como base global.

**Reglas Fundamentales (aplicar siempre):**

1. **Pensar y Encuadrar** — Declarar suposiciones e incógnitas. Clarificar el objetivo real antes de actuar. Preguntar ante la incertidumbre.

2. **Simplicidad Primero** — Solución correcta más pequeña. Sin funcionalidades, abstracciones o complejidad no solicitadas.

3. **Quirúrgico** — Cambiar solo lo necesario. Igualar el estilo existente. No tocar código no relacionado.

4. **Orientado a Objetivos + Verificar** — Convertir la tarea en metas explícitas y verificables. Proporcionar evidencia (pruebas, salida, métricas) de que los criterios se cumplen antes de finalizar.

5. **Concesiones y Evidencia** — Exponer suposiciones y concesiones importantes. Mostrar resultados de verificación, no solo afirmaciones.

6. **Seguridad** — Nunca exponer secretos. Usar variables de entorno para credenciales. Validar todas las entradas.

7. **Registro de Sesión** — Al final de la sesión, registrar qué se hizo, decidió y queda pendiente en `SESSION_LOG.md`. Leerlo al inicio de la sesión.

**Flujo de trabajo**: Investigar/planificar cuando el alcance no esté claro → implementar mínimamente → verificar contra objetivos.

Preferir patrones establecidos. Ser explícito. Igualar el estilo del trabajo.

(Versión completa en AGENTS.md)

---

[English version](core.md) | **Español**
