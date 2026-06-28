# Variante de Desarrollo de Software

Los principios fundamentales del AGENTS.md raíz aplican completamente.

## Énfasis Adicional
- Escribir o actualizar pruebas para comportamiento modificado.
- Preferir patrones existentes en el código base.
- Ejecutar linting/type-checking como parte de la verificación.
- Mantener los cambios revisables (diffs pequeños y enfocados).
- Nunca hacer commit de secretos o credenciales. Usar archivos `.env` (en gitignore) o variables de entorno.
- Validar todas las entradas. Sanitizar salida orientada al usuario.
- Usar hooks pre-commit: `detect-private-key`, `detect-secrets`, `lint-staged`.

---

[English version](AGENTS.md) | **Español**
