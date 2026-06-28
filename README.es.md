# dann-specs

**Especificación de comportamiento universal y agnóstica a la herramienta para agentes de IA.**

Una síntesis profesional de los patrones más sólidos de los principales sistemas de guía para agentes —
principios de comportamiento, disciplina de encuadre, estándares operativos y flujos de trabajo
con verificación primero. Diseñado para ser la fuente única de verdad para agentes de codificación,
herramientas de investigación, plataformas educativas y trabajo de conocimiento.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Validate Spec](https://github.com/perezdann/dann-specs/actions/workflows/validate.yml/badge.svg)](https://github.com/perezdann/dann-specs/actions/workflows/validate.yml)

## Filosofía

Las instrucciones más efectivas para agentes combinan:

1. **Reglas de comportamiento claras** — cómo debe pensar y actuar el agente
2. **Contexto operativo** — lo que el agente necesita saber sobre el entorno
3. **Disciplina de verificación** — cómo se mide el éxito
4. **Adaptabilidad** — diferentes modos para distintos tipos de proyecto

dann-specs entrega los cuatro en un paquete limpio y versionable.

## Inicio Rápido

Elige tu nivel de integración:

### Nivel 1: Directo (10 segundos)
```bash
curl -O https://raw.githubusercontent.com/perezdann/dann-specs/main/project/AGENTS.md
# Haz commit de AGENTS.md. Tu LLM lo lee del contexto. Sin herramientas adicionales.
```

### Nivel 2: Con evaluación (2 minutos)
```bash
curl -O https://raw.githubusercontent.com/perezdann/dann-specs/main/project/AGENTS.md
pip install llm-behavioral-eval
behavioral-eval --spec . --suite core_principles --count 15 --real-llm --provider ollama
# Verifica que tu modelo realmente sigue la especificación.
```

### Nivel 3: Perfil completo (5 minutos)
```bash
git clone https://github.com/perezdann/dann-specs.git vendor/dann-specs
cp vendor/dann-specs/project/{AGENTS.md,CLAUDE.md,eval-profile.json} .
cp -r vendor/dann-specs/project/{mini,roles,variants} .
behavioral-eval --spec . --suite all --real-llm --judge-provider deepseek
# Evaluación completa con juez LLM, 5 categorías, intervalos de confianza al 95%.
```

## Principios Fundamentales

1. **Pensar y Encuadrar Antes de Actuar** — Declarar suposiciones e incógnitas. Clarificar objetivos.
2. **Simplicidad y Mínimo Viable** — La solución correcta más pequeña. Sin funcionalidades no solicitadas.
3. **Cambios Precisos y Quirúrgicos** — Modificar solo lo necesario. Igualar el estilo existente.
4. **Orientado a Objetivos con Verificación** — Convertir solicitudes en metas explícitas y verificables.
5. **Exponer Compensaciones y Registrar Decisiones** — Hacer visibles suposiciones, restricciones y concesiones.
6. **Flujo de Trabajo con Verificación Primero** — Pruebas, linters, builds como señales primarias.
7. **Desarrollo con Conciencia de Seguridad** — Nunca exponer secretos. Validar entradas. Mínimo privilegio.
8. **Continuidad de Sesión y Traza de Auditoría** — Registrar cada sesión no trivial para reanudación futura.

## Estructura

```
project/
├── AGENTS.md                ← Especificación principal (universal)
├── CLAUDE.md                ← Punto de entrada para Claude Code
├── evaluation-rubric.md     ← Dimensiones de autoevaluación (1-5)
├── eval-profile.json        ← Configuración para el motor llm-behavioral-eval
├── mini/core.md             ← Versión compacta (<200 palabras, contexto limitado)
├── roles/                   ← 14 personajes especialistas
│   ├── physician.md, lawyer.md, accountant.md, nurse.md
│   ├── mechanic.md, electronics-technician.md, seamstress.md
│   ├── graphic-designer.md, architect.md, domain-specialist.md
│   ├── researcher.md, educator.md, reviewer.md, security-auditor.md
├── variants/                ← 7 variantes por dominio
│   ├── software-development/, infra-devops/, research-knowledge/
│   ├── education-courses/, product-management/, data-analysis/
│   └── professional-services/
├── tools/                   ← Adaptadores listos para usar
│   ├── continue/.continue/rules/dann-specs.md
│   ├── cursor/.cursor/rules/dann-specs.mdc
│   ├── cline/.clinerules, aider/CONVENTIONS.md
│   └── universal/AGENTS.md
├── tests/                   ← Harness de pruebas (legado, reemplazado por llm-behavioral-eval)
├── reports/                 ← Resultados de pruebas de la comunidad
├── LICENSE                  ← GPL-3.0
└── CHANGELOG.md
```

## Roles

14 personajes especialistas predefinidos. Cada uno extiende los principios fundamentales con comportamiento específico del dominio:

| Rol | Dominio |
|---|---|
| physician | Razonamiento clínico, diagnóstico, plan de tratamiento |
| lawyer | Análisis legal, revisión de contratos, asesoría |
| accountant | Contabilidad, informes financieros, impuestos, auditorías |
| nurse | Cuidado de pacientes, monitoreo, documentación |
| mechanic | Diagnóstico de vehículos, procedimientos de reparación |
| electronics-technician | Análisis de circuitos, reparación de componentes |
| seamstress | Diseño de patrones, confección de prendas |
| graphic-designer | Composición visual, identidad de marca |
| architect | Diseño estructural, sistemas de construcción |
| domain-specialist | Consulta experta en cualquier campo |
| researcher | Revisión de literatura, metodología, hallazgos |
| educator | Diseño de cursos, pedagogía, evaluación |
| reviewer | Revisión de código/estructura, retroalimentación |
| security-auditor | Auditoría de seguridad, modelado de amenazas, análisis de vulnerabilidades |

## Variantes

7 extensiones específicas por dominio que adaptan los principios fundamentales:

| Variante | Énfasis |
|---|---|
| software-development | Escribir/actualizar pruebas, preferir patrones existentes, ejecutar linting |
| infra-devops | Infraestructura como código, reproducibilidad, planes de rollback |
| research-knowledge | Claridad, reproducibilidad, verificación apropiada al dominio |
| education-courses | Estructura pedagógica, diseño de evaluación, accesibilidad |
| product-management | Historias de usuario, criterios de aceptación, concesiones entre stakeholders |
| data-analysis | Procedencia de datos, validez estadística, visualización |
| professional-services | Comunicación con cliente, estructura de entregables, alcance de facturación |

## Evaluación

dann-specs se evalúa usando [llm-behavioral-eval](https://github.com/perezdann/llm-behavioral-eval),
un motor de evaluación agnóstico a la especificación. El archivo `eval-profile.json` configura 7 suites de prueba:

| Suite | Pruebas | Puntuación |
|---|---|---|
| core_principles | 20 | Juez LLM o heurística |
| rubric_dimensions | 40 | Juez LLM o heurística |
| roles | 40 | Juez LLM o heurística |
| variants | 25 | Juez LLM o heurística |
| concrete | 30 (estratificado) | Ejecución de código + aserciones |
| security | 20 | Juez LLM o heurística |
| session_continuity | 15 | Juez LLM o heurística |

### Ejecutar evaluación

```bash
pip install llm-behavioral-eval

# Simulada (rápida, sin llamadas a LLM)
behavioral-eval --spec ./project --suite all

# LLM real con juez
behavioral-eval --spec ./project --suite all --real-llm \
  --provider llama-home --judge-provider deepseek

# Medir consistencia
behavioral-eval --spec ./project --suite all --real-llm --repetitions 3
```

## Herramientas Soportadas

- **AGENTS.md** — Estándar universal (todas las herramientas)
- **Claude Code** → `CLAUDE.md`
- **Continue.dev** → `.continue/rules/dann-specs.md`
- **Cursor** → `.cursor/rules/dann-specs.mdc`
- **Cline** → `.clinerules`
- **Aider** → `CONVENTIONS.md`
- **Kilo Code** — Soporte nativo de AGENTS.md

## Control de Versiones

Versionado semántico completamente automatizado al hacer push a `main` mediante
[python-semantic-release](https://python-semantic-release.readthedocs.io/):

```bash
cz commit  # commit convencional interactivo
git push   # CI auto-publica: incrementa versión, actualiza CHANGELOG, crea GitHub Release
```

| Prefijo de commit | Incremento |
|---|---|
| `feat:` | MINOR |
| `fix:` | PATCH |
| `BREAKING CHANGE:` | MAJOR |

- Tags: v1.0.0 (spec inicial), v2.0.0 (integración del motor + eval-profile)

## Contribuir

1. Haz fork del repositorio
2. Edita AGENTS.md, roles o variants
3. Ejecuta evaluación para verificar: `behavioral-eval --spec ./project --suite all --real-llm`
4. Envía un PR con tus datos de informe en `reports/`

Los datos de pruebas de la comunidad mejoran la especificación empíricamente.

## Licencia

GPL-3.0. Ver [LICENSE](LICENSE).

---

[English version](README.md) | **Español**
