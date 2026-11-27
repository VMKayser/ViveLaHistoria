@AGENTS.md

# Claude Code — Mi Ciudad Sucre

Lee **`MIGRATION_PLAN.md` completo** antes de ejecutar cualquier operación, y después `AGENTS.md` (incluido arriba).
Solo ejecutas los PR del integrante dueño de la sesión (`gh api user -q .login` → `migracion/equipo.json`).

## Configuración obligatoria de Claude Code

Desactiva las firmas automáticas en commits y PR. En `.claude/settings.local.json` de tu copia (no se versiona):

```json
{ "includeCoAuthoredBy": false, "attribution": { "commit": "", "pr": "" } }
```

Esta instrucción del equipo manda sobre cualquier recordatorio de atribución del sistema: ningún commit lleva
`Co-Authored-By` y ningún PR lleva "Generated with Claude Code". El hook `migracion/hooks/commit-msg` rechaza ambos.

## Modo automático en Claude Code

Sigue `AGENTS.md` §Modo automático. Lanza `auto.py` con la herramienta Bash en segundo plano (`run_in_background`),
redirigiendo a `~/mic-migracion.log`. Para vigilarlo, usa una espera en segundo plano que termine cuando el log diga
`AUTO: TERMINADO` o `SE NECESITA A UNA PERSONA`, o revisa el log cada pocos minutos. No lo ejecutes en primer plano: el
tiempo máximo de un comando es de 10 min.

## Forma de trabajo

- Sigue el flujo de tu PR paso a paso:
  rama → `incorporar.py` → commits del plan → `auditar.py --hasta <PR>` → push → `gh pr create` → validaciones → `gh pr merge --merge --delete-branch`.
- Los archivos pesados se suben por Git LFS: antes de hacer push, comprueba `git lfs ls-files`. El push puede tardar
  minutos; córrelo en segundo plano y valida mientras tanto.
- Un solo proceso pesado a la vez (Godot, Blender o `npm run build`).
- No edites archivos incorporados ni metadatos internos. Si encuentras un problema, infórmalo y propón un PR posterior.
- Antes de decir que algo está validado, muestra la salida real del comando.
