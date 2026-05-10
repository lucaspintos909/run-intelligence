---
stepsCompleted: [1, 2, 3, 4]
session_status: 'COMPLETED'
next_recommended_skill: 'bmad-create-prd'
next_phase: '2-planning'
inputDocuments: []
session_topic: 'Running Analytics + AI Coach con Especialización en Asma'
session_goals: 'Explorar giros creativos, enfoques alternativos y profundizar features para un sistema integrado de análisis de carreras (.fit Coros) + agente IA especializado en fisiología del running y manejo del asma durante el ejercicio'
selected_approach: 'progressive-flow'
techniques_used: ['What If Scenarios', 'Cross-Pollination', 'Mind Mapping', 'SCAMPER Method', 'Decision Tree Mapping']
ideas_generated: ['sub-agente-cientifico-evidence-based', 'analisis-cruzado-metricas-asmaticas', 'sub-agente-perfil-asmatico', 'sub-agente-perfil-runner', 'reporte-mensual-usuario', 'langgraph-orquestador', 'sistema-hipotesis-cientificas', 'actualizacion-post-reporte', 'sintesis-estado-unificado', 'revision-cientifica-interna', 'perfiles-con-capas', 'perfil-corregible-usuario', 'simulador-riesgo', 'eliminacion-rag-ondemand']
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** lpintos
**Date:** 2026-05-09

## Session Overview

**Topic:** Running Analytics + AI Coach con Especialización en Asma
**Goals:** Explorar giros creativos, enfoques alternativos y profundizar features para un sistema integrado de análisis de carreras (.fit Coros) + agente IA especializado en fisiología del running y manejo del asma durante el ejercicio

### Context Guidance

- **Componente 1:** Pipeline Python que parsea archivos .fit de Coros, extrae métricas clave y persiste en base de datos/JSON estructurada.
- **Componente 2:** Agente conversacional (OpenAI API / OpenCode) con base de conocimiento embebida sobre fisiología del running, periodización y manejo del asma. Lee datos del Componente 1 y genera recomendaciones + status del atleta.
- **Condición médica relevante:** Asma crónico — factor diferenciador clave del sistema.
- **Hardware:** Reloj Coros (exporta .fit nativamente).
- **Base científica documentada:** `asma_running_base_teorica.md` (719 líneas) + `base_cientifica_running.md` (499 líneas) — cubren GINA 2024, fisiopatología BIE, protocolos anti-BIE, periodización, biomecánica, nutrición, psicología del deporte.

### Session Setup

Sesión orientada a descubrir enfoques alternativos, profundizar features existentes y validar si el diseño actual de dos componentes es óptimo o si existen arquitecturas/funcionalidades más innovadoras.

## Technique Selection

**Approach:** Progressive Technique Flow
**Journey Design:** Systematic development from exploration to action

**Progressive Techniques:**

- **Phase 1 - Exploration:** What If Scenarios + Cross-Pollination for maximum idea generation
- **Phase 2 - Pattern Recognition:** Mind Mapping for organizing insights
- **Phase 3 - Development:** SCAMPER Method for refining concepts
- **Phase 4 - Action Planning:** Decision Tree Mapping for implementation planning

**Journey Rationale:** El proyecto combina 3 dominios raramente integrados (running de alto rendimiento, asma crónico, IA conversacional). El flujo progresivo permite explorar cada dominio por separado, encontrar conexiones inesperadas, y validar si la arquitectura de 2 componentes es óptima o si existen alternativas más innovadoras.

## Technique Execution Results

### What If Scenarios — Phase 1: Expansive Exploration

**Interactive Focus:** Explorar giros creativos cuestionando suposiciones del diseño actual de 2 componentes

---

**[Categoría #1]**: Sub-Agente Científico Evidence-Based → **APROBADO para Fase 2**
_Concept_: Un sub-agente especializado que consulta la base teórica científica (GINA 2024, guías ACSM, protocolos anti-BIE) antes de emitir cualquier recomendación. No es un LLM genérico que "sabe de running" — es un agente que CITA sus fuentes, verifica que sus recomendaciones respeten los protocolos establecidos (ej: calentamiento específico anti-BIE de 6-8 × 30s sprint al 90-100% FCmáx con 90s recuperación), y flaggea cuando una recomendación podría contraindicarse con el nivel de control del asma del atleta.
_Novelty_: Diferente de apps genéricas (Strava, TrainingPeaks) porque integra evidencia médica específica de asma + running. Diferente de coaches humanos porque tiene acceso instantáneo a toda la literatura y puede correlacionar datos históricos del atleta con estudios poblacionales.

**[Categoría #2]**: Módulo de Contexto Ambiental Automático → **DESCARTADO**
_Razón_: Overkill para MVP. Se puede integrar más adelante si el core funciona.

**[Categoría #3]**: Pipeline Automático de Planificación Semanal → **DESCARTADO**
_Razón_: Demasiado complejo para la arquitectura actual. Requiere cron jobs, notificaciones, etc. Se puede agregar después.

**[Categoría #4]**: Análisis Cruzado de Métricas Running + Asma → **APROBADO para Fase 2**
_Concept_: El pipeline no solo extrae pace/FC/distancia del .fit — también calcula derivadas relevantes para asmáticos: variabilidad de FC durante la carrera (¿hay picos inexplicables que correlacionen con sensación de opresión?), relación pace/FC (¿se está desacoplando?), ratio de cadencia vs zancada (¿cambios biomecánicos compensatorios?), y las cruza con reportes subjetivos post-carrera (RPE, síntomas asmáticos 0-3, uso de rescate).
_Novelty_: Métricas estándar de running + métricas "asma-aware" que ninguna plataforma comercial calcula.

**[Categoría #5]**: Perfil Fisiológico de Asma Personalizado + Memoria Persistente → **APROBADO para Fase 2 (REDISEÑADO)**
_Concept_: **NO es un script — es un sub-agente especializado.** Después de cada ingesta de datos (.fit procesado), un sub-agente independiente analiza la nueva carrera vs. todo el historial y emite conclusiones en lenguaje natural: "En las últimas 3 carreras con temp <10°C, tu FC se desacopló del pace (+15 bpm). Esto sugiere que el frío es un trigger confirmado para vos. Probabilidad: alta. Voy a agregar 'frío seco' como trigger principal en tu perfil." Estas conclusiones se escriben en `asma_profile.md` (~500 tokens), un archivo legible que el Agente Coach lee al inicio de cada sesión.
_Arquitectura_: 3 componentes, no 2: (1) Pipeline de datos → (2) Sub-agente de Perfil Fisiológico → (3) Agente Coach IA. El sub-agente #2 es el cerebro que aprende; el agente #3 es el coach que conversa.
_Novelty_: Ninguna app comercial genera un perfil fisiológico asmático personalizado basado en datos propios. La clave: el perfil es escrito por un agente, no calculado por un script.

**[Categoría #6]**: Reporte Mensual para Médico (controlado por el usuario) → **APROBADO para Fase 2**
_Concept_: El sistema genera un "Running Report" mensual con: sesiones totales, síntomas asmáticos, uso de rescate, cumplimiento de protocolos, recomendaciones del coach. **El usuario decide si compartirlo con su médico o no.** No se envía automáticamente a nadie.
_Novelty_: Empodera al atleta con datos estructurados para la consulta médica, sin invadir la relación médico-paciente.

**[Categoría #7]**: Perfil Runner Separado (Sub-agente independiente) → **APROBADO para Fase 2**
_Concept_: Un sub-agente SEPARADO del perfil asmático, con contexto limpio y sin ruido, dedicado exclusivamente a analizar la evolución del runner: VO2 estimado, zonas de FC, progresión de VDOT, economía de carrera, cadencia preferida, lesiones históricas. Escribe `runner_profile.md` (~500 tokens). El Agente Coach lee AMBOS perfiles al inicio de cada sesión. El sub-agente de perfil runner detecta interacciones con el perfil asmático: "Tu VDOT subió 5% pero tu FC de reposo subió 8 bpm y tenés 2 síntomas asmáticos esta semana. Posible acumulación de fatiga."
_Arquitectura_: 4 componentes: (1) Pipeline de datos → (2) Sub-agente Perfil Asmático → (3) Sub-agente Perfil Runner → (4) Agente Coach IA.
_Rationale_: Separación de responsabilidades. Cada agente tiene un dominio claro. Evita que el contexto del asma "contamine" el análisis de rendimiento y viceversa.

---

## Decisiones Arquitectónicas Clave (Deep Dive — Sistema de Memoria)

### Formato de Perfiles
**Opción A: Markdown narrativo legible** — Elegida. El perfil es human-readable y audit por el usuario.

### Frecuencia de Actualización
**Después de cada carrera** — El sub-agente corre inmediatamente post-ingesta y actualiza el perfil si detecta patrones nuevos.

### Resolución de Conflictos
**Escalación al usuario** — Cuando el Perfil Asmático y el Perfil Runner se contradicen (ej: rendimiento vs. seguridad), el Agente Coach presenta el dilema y el usuario decide.

### Persistencia
**Archivos en repo git** — `profiles/asma_profile.md` y `profiles/runner_profile.md` viven en el repositorio. Se versionan con git. El usuario puede hacer `git log` para ver la evolución de su perfil.

### Orquestador
**LangGraph** — Elegido como framework de orquestación. El flujo de 4 componentes (Pipeline → Perfil Asmático → Perfil Runner → Coach) se modela como un grafo de estados en LangGraph. Cada nodo es un agente/sub-agente. Las transiciones entre nodos son condicionales (ej: solo actualizar perfiles si hay nueva data, solo invocar coach cuando el usuario lo solicita). LangGraph gestiona la memoria entre ejecuciones y permite depurar el flujo completo.

### Retrieval de Contexto
**RAG on-demand** — No inyección directa en prompt. El Agente Coach tiene instrucciones claras de dónde buscar (`profiles/`, `docs/`, `data/`) y cómo (leer archivos, hacer queries SQL). LangGraph orquesta qué información recuperar según el estado actual del grafo.

### Base de Datos / Schema
**SQLite local** — `data/run_intelligence.db` es la fuente de verdad estructurada. Los markdown profiles son "vistas narrativas" construidas a partir de la BD, no fuentes de verdad. El sub-agente de perfil CONSULTA la BD para emitir conclusiones, y luego las persiste en los .md para que el Coach las lea.

**Tablas propuestas (MVP):**

```sql
-- Carreras procesadas (raw + calculado)
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE,
    date TEXT,
    distance_km REAL,
    duration_sec INTEGER,
    avg_pace_min_km REAL,
    avg_hr INTEGER,
    max_hr INTEGER,
    cadence_spm INTEGER,
    elevation_gain_m INTEGER,
    -- métricas asma-aware calculadas por el pipeline
    hr_pace_drift REAL,          -- desacoplamiento FC/pace en últimos 20%
    hr_variability_sd REAL,      -- variabilidad de FC durante carrera
    time_in_zone1_sec INTEGER,   -- distribución de zonas
    time_in_zone2_sec INTEGER,
    time_in_zone3_sec INTEGER,
    temp_c REAL,                 -- manual o API futura
    humidity_pct REAL,
    -- reporte subjetivo post-carrera (usuario llena después)
    subjective_rpe INTEGER,
    subjective_asthma_symptoms INTEGER,  -- 0-3
    subjective_rescue_used BOOLEAN,
    subjective_notes TEXT,
    created_at TEXT
);

-- Métricas de salud / asma (reportadas por el usuario, no del .fit)
CREATE TABLE health_log (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE,
    morning_peak_flow REAL,      -- FEP matinal
    sleep_quality INTEGER,       -- 1-5
    asthma_control_score REAL,   -- ACQ o similar, manual
    notes TEXT
);

-- Historial de conversaciones con el Coach (para contexto de últimos 5-10 mensajes)
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,                   -- 'user' | 'assistant' | 'system'
    content TEXT,
    timestamp TEXT
);

-- Snapshots de métricas acumuladas (para que el perfil runner no recalcule todo desde cero)
CREATE TABLE runner_metrics_history (
    id INTEGER PRIMARY KEY,
    date TEXT,
    estimated_vo2max REAL,
    vdot REAL,
    acwr REAL,
    weekly_volume_km REAL,
    avg_resting_hr INTEGER
);
```

**¿Qué va en BD vs. qué va en Markdown?**

| Tipo de dato | Dónde vive | Por qué |
|---|---|---|
| Datos crudos de carrera (pace, FC, cadencia) | BD | Estructurado, queryable, fuente de verdad |
| Métricas calculadas (VDOT, ACWR, drift) | BD | Determinísticas, reproducibles, versionables vía git del .db |
| Reportes subjetivos (RPE, síntomas, rescate) | BD | Estructurado, correlacionable con datos objetivos |
| Perfil asmático (triggers, umbrales, hipótesis) | Markdown | Narrativo, escrito por agente, legible por humanos y coach |
| Perfil runner (VO2, economía, lesiones) | Markdown | Narrativo, escrito por agente, legible por humanos y coach |
| Últimos mensajes de conversación | BD | Estructurado, fácil de recuperar para contexto |
| Evidencia cruda (queries SQL, referencias) | Capa 3 del perfil .md | Debugging, transparencia |

### Flujo de Ingesta de Health Logs

Los `health_log` son datos **manuales del usuario**, no del reloj. El flujo de ingesta es:

**1. Input del usuario (3 momentos clave):**

- **Mañana (pre-entreno o al despertar)**: El usuario mide FEP (flujo espiratorio pico) con flujómetro y anota:
  ```
  Fecha: 2026-05-10
  FEP matinal: 520 L/min
  Calidad del sueño: 3/5
  Notas: "Desperté con tos seca"
  ```

- **Post-carrera (inmediatamente después de correr)**: El usuario reporta subjetivos:
  ```
  Carrera: 2026-05-10_5km.fit
  RPE (esfuerzo percibido): 14/20
  Síntomas asmáticos: 1/3 (leve)
  Usé rescate (SABA): Sí
  Notas: "Tos seca minuto 8, se pasó con inhalador"
  ```
  *Estos datos van a la tabla `runs` (campos `subjective_*`), no a `health_log`.*

- **Semanal (opcional)**: El usuario completa un score de control asmático (ACQ simplificado) o anota observaciones generales:
  ```
  Semana: 2026-W19
  Asthma Control Score: 1.2
  Notas: "Esta semana usé rescate 3 veces, todas en intervalos"
  ```

**2. Interfaz de ingesta (MVP):**

Opción A: **CLI interactivo** — `python run.py --log-health` abre un prompt simple:
```bash
$ python run.py --log-health
Fecha [2026-05-10]: 
FEP matinal (L/min): 520
Calidad del sueño (1-5): 3
Notas: Desperté con tos seca
✅ Guardado en health_log
```

Opción B: **Conversación con el Coach** — El usuario le dice al Coach: *"Hoy mi FEP fue 520 y dormí mal"*. El Coach extrae las entidades y confirma antes de guardar:
> "Entiendo: FEP 520 L/min, calidad del sueño 3/5. ¿Guardo esto en tu health log?" → Usuario confirma → Se escribe en BD.

Opción C: **Markdown template** — El usuario edita un archivo `daily_log.md` con formato estructurado y un script lo parsea a la BD.

**Decisión**: Opción A (CLI) para MVP. Opción B (conversacional) como iteración post-MVP.

**3. ¿Quién consume los Health Logs?**

- **Sub-Agente Perfil Asmático**: Al actualizar el perfil post-carrera, consulta `health_log` de esa fecha para ver si el FEP matinal estaba en zona amarilla/roja (contexto de riesgo previo).
- **Sub-Agente Perfil Runner**: Consulta `health_log` para detectar correlaciones (ej: "días con sueño <3/5 correlacionan con FC de reposo +8 bpm").
- **Coach IA**: Al recibir el paquete de contexto, incluye el último `health_log` para tener contexto de estado actual.

**4. Frecuencia esperada:**

| Dato | Frecuencia | Obligatorio |
|---|---|---|
| FEP matinal | Diaria (días con carrera) | Sí — es el mejor predictor de control |
| Calidad del sueño | Diaria | No, pero altamente recomendado |
| RPE post-carrera | Después de cada carrera | Sí — feedback para el perfil runner |
| Síntomas asmáticos post-carrera | Después de cada carrera | Sí — feedback para el perfil asmático |
| Uso de rescate post-carrera | Después de cada carrera | Sí — métrica crítica de control |
| Asthma Control Score | Semanal | No — útil para tendencias |

**5. Relación con el pipeline:**

```
Pipeline procesa .fit → guarda en tabla `runs` (datos objetivos)
                            │
                            ▼
Usuario ingresa health_log → guarda en tabla `health_log` + campos subjective_* en `runs`
                            │
                            ▼
Sub-agente Perfil Asmático consulta: `runs` + `health_log` → actualiza `asma_profile.md`
Sub-agente Perfil Runner consulta: `runs` + `health_log` → actualiza `runner_profile.md`
```

### Evolución Histórica
**Git como time machine** — El agente sabe que puede usar `git diff` o `git log` para ver cómo evolucionó el perfil. El usuario puede auditar qué aprendió el sistema y cuándo.

---

## Phase 2: Pattern Recognition — Mind Mapping

### Cluster Map: Ideas & Decisions Organized

```
RUN-INTELLIGENCE
│
├── 🧠 AGENTES ESPECIALIZADOS (Cerebro del sistema)
│   ├── Sub-Agente Científico Evidence-Based
│   │   └── Consulta docs/ (GINA 2024, ACSM) antes de recomendar
│   ├── Sub-Agente Perfil Asmático
│   │   ├── Escribe asma_profile.md (~500 tokens)
│   │   ├── Detecta triggers, umbrales, protocolos efectivos
│   │   └── Corre después de CADA carrera procesada
│   └── Sub-Agente Perfil Runner
│       ├── Escribe runner_profile.md (~500 tokens)
│       ├── Detecta VO2, VDOT, economía, cadencia
│       └── Contexto limpio, sin ruido asmático
│
├── 🏗️ ARQUITECTURA (Huesos del sistema)
│   ├── LangGraph como orquestador
│   │   ├── Nodo 1: Pipeline (.fit → datos)
│   │   ├── Nodo 2: Perfil Asmático
│   │   ├── Nodo 3: Perfil Runner
│   │   └── Nodo 4: Coach IA (interacción usuario)
│   ├── Base de Datos SQLite (data/run_intelligence.db)
│   │   ├── Tabla `runs`: datos crudos + métricas calculadas del pipeline
│   │   ├── Tabla `health_log`: FEP, sueño, control asmático (input usuario)
│   │   ├── Tabla `conversation_history`: últimos mensajes para contexto
│   │   └── Tabla `runner_metrics_history`: snapshots de VDOT, ACWR, etc.
│   ├── Persistencia en repo git
│   │   ├── profiles/asma_profile.md
│   │   ├── profiles/runner_profile.md
│   │   └── Git como time machine (git log/diff)
│   └── Paquete de contexto preparado
│       └── Orquestador inyecta perfiles + docs relevantes + últimos mensajes al Coach
│
├── 📊 ANÁLISIS DE DATOS (Sangre del sistema)
│   ├── Pipeline .fit (Componente 1 original)
│   └── Métricas Asma-Aware
│       ├── Variabilidad de FC vs sensación de opresión
│       ├── Relación pace/FC (desacoplamiento)
│       ├── Cadencia/zancada (compensaciones biomecánicas)
│       └── Cruce con reportes subjetivos (RPE, síntomas 0-3, rescate)
│
├── 🎯 COACH IA (Cara del sistema)
│   ├── Lee ambos perfiles al inicio de sesión
│   ├── Retrieval on-demand vía LangGraph
│   ├── Resolución de conflictos: Escalación al usuario
│   └── Genera Reporte Mensual (usuario decide si comparte con médico)
│
├── 🔬 BASE CIENTÍFICA (Conocimiento embebido)
│   ├── docs/asma_running_base_teorica.md (719 líneas)
│   │   └── GINA 2024, BIE, fisiopatología, protocolos, farmacología
│   └── docs/base_cientifica_running.md (499 líneas)
│       └── VO2máx, periodización, biomecánica, nutrición, lesiones
│
└── 📦 MVP PRIORITARIO (Qué construir primero)
    ├── ✅ LangGraph con 4 nodos
    ├── ✅ Pipeline .fit + métricas estándar
    ├── ✅ Sub-agente Perfil Asmático
    ├── ✅ Sub-agente Perfil Runner
    ├── ✅ Coach IA con RAG on-demand
    ├── ✅ Reporte mensual
    └── ⏳ FUTURO (no MVP)
        ├── Módulo contexto ambiental (API clima)
        ├── Pipeline automático de planificación semanal
        ├── Sistema bidireccional coach↔pipeline
        └── Dashboard visual
```

### Temas Emergentes

1. **Memoria Persistente**: Todo gira en torno a que el sistema "recuerde" entre sesiones. Perfiles en git son el eje central.

2. **Separación de Dominios**: Asma y running están desacoplados en sub-agentes separados. Se conectan solo en el Coach.

3. **Evidence-Based**: Cada recomendación debe poder rastrearse a docs/. No hay magia negra.

4. **Orquestación Declarativa**: LangGraph define el flujo, no scripts imperativos.

5. **Empoderamiento del Usuario**: El usuario controla el reporte médico, decide en conflictos, y audita perfiles.

---

## Phase 3: Development — SCAMPER Method

### Idea Base: Sub-Agentes Perfil Asmático + Runner

#### 1. SUSTITUIR (Substitute) → **APROBADAS AMBAS**
- **Sistema de hipótesis científicas con ciclo de vida**: El perfil no es estático — es una lista de hipótesis activas con estados (Propuesta → En prueba → Confirmada/Descartada → Arqueada) y niveles de confianza.
- **Actualización post-reporte**: El sub-agente corre después de que el usuario reporta síntomas post-carrera, no solo post-pipeline. Si no hay reporte, anota "sin datos subjetivos".

#### 2. COMBINAR (Combine) → **APROBADAS AMBAS**
- **Síntesis de estado unificado (quinto nodo LangGraph)**: Un nodo "Síntesis" que fusiona ambos perfiles en un resumen de estado unificado para el Coach: "🟡 Fitness mejorando, 🟠 Alerta asmática leve, 🔵 Carga estable".
- **Reporte mensual como checkpoint del perfil**: El mismo sub-agente de perfil, al final de cada mes, resume hipótesis, archiva descartadas, y emite el reporte.

#### 3. ADAPTAR (Adapt) → **APROBADO: Revisión científica interna**
- Cada hipótesis generada por el sub-agente pasa por revisión del Sub-Agente Científico Evidence-Based, que la confronta con docs/. La hipótesis se etiqueta: "Revisada — compatible con literatura" / "Revisada — evidencia insuficiente" / "Revisada — contradictoria (ver fuente)".

#### 4. MODIFICAR (Modify/Magnify/Minify) → **APROBADOS: Amplificar + Modificar. DESCARTADO: Reducir**
- **Amplificar — Perfiles con capas**: Capa 1 (Resumen ~200 tokens), Capa 2 (Detalle ~1000 tokens), Capa 3 (Evidencia cruda / SQL / debugging).
- **Modificar — Perfil corregible por el usuario**: El usuario puede escribir en `asma_profile.md` correcciones o prioridades. El sub-agente respeta estas anotaciones y re-prioriza hipótesis.
- **Descartado — Modo flash (ultra-compacto)**: No se implementa por ahora.

#### 5. PONER EN OTROS USOS (Put to other uses) → **APROBADO: Simulador. DESCARTADAS: Dataset investigación + Backup médico**
- **Simulador de riesgo**: El Coach usa el perfil para simular escenarios: "Según tu perfil, si hacés intervalos mañana a 5°C con SABA, riesgo de BIE ~35%. Sin SABA, ~78%."

#### 6. ELIMINAR (Eliminate) → **APROBADO: Eliminar RAG on-demand. DESCARTADAS: Eliminar Perfil Runner como nodo + Eliminar reporte mensual**
- **Eliminar RAG on-demand**: El orquestador LangGraph prepara TODO el contexto necesario (perfiles, docs relevantes, últimos mensajes) y lo inyecta en el estado antes de invocar al Coach. El Coach recibe un "paquete de contexto" preparado. Más determinismo, menos flexibilidad ad-hoc.
- **Las otras dos eliminaciones se descartan**: Perfil Runner sigue como nodo agente separado. Reporte mensual sigue como feature.

#### 7. REVERTIR (Reverse/Rearrange) → **DESCARTADO TOTALMENTE**
- No se implementan: sistema como tutorial, sistema que inicia diálogo, ni perfiles pre-carrera.

---

### Ideas Descartadas en esta Ronda

- Pipeline Automático de Planificación Semanal: Over-engineering para MVP.
- Módulo de Contexto Ambiental Automático: Interesante pero no core.
- Sistema Bidireccional Coach ↔ Pipeline: Over-engineering para MVP.
- Dashboard visual/HTML: Preferido 100% conversacional.
- Multi-atleta / escalabilidad: Estrictamente personal por ahora.
- Sistema de guardarraíles automático (detener entrenamiento): El usuario prefiere decisión final propia.

---

## Phase 4: Action Planning — Decision Tree Mapping

### Árbol de Implementación: Camino Crítico

```
START
│
├─► [M0] PRE-MILESTONE: Schema de Base de Datos
│   ├─ Definir tablas MVP: `runs`, `health_log`, `conversation_history`, `runner_metrics_history`
│   ├─ Migración inicial `init_db.py`
│   └─ ✅ ENTREGABLE: `data/run_intelligence.db` creado con schema validado
│
├─► [M1] MILESTONE 1: Pipeline .fit funcional
│   ├─ Parser de archivos .fit (Coros)
│   ├─ Extracción de métricas estándar (pace, FC, distancia, tiempo, cadencia, zancada)
│   ├─ Cálculo de métricas derivadas (VDOT estimado, drift FC/pace, distribución de zonas)
│   ├─ Persistencia en SQLite (`data/run_intelligence.db`, tabla `runs`)
│   └─ ✅ ENTREGABLE: Script `pipeline.py` que toma un .fit y genera un registro en la BD
│
│   DECISIÓN 1: ¿El pipeline produce datos válidos y consistentes?
│   ├── NO → Iterar, fix bugs, validar con 5+ archivos .fit
│   └── SÍ → Proceder a Milestone 2
│
├─► [M2] MILESTONE 2: LangGraph scaffold con 2 nodos
│   ├─ Nodo `pipeline_node`: invoca `pipeline.py`
│   ├─ Nodo `coach_basic_node`: agente conversacional simple (sin perfiles todavía)
│   ├─ Estado compartido mínimo (datos de última carrera + últimos mensajes)
│   └─ ✅ ENTREGABLE: Grafo funcional `python run.py --mode coach` que carga un .fit y permite conversar
│
│   DECISIÓN 2: ¿El Coach puede responder preguntas básicas usando los datos de la carrera?
│   ├── NO → Revisar prompts, ajustar contexto, iterar
│   └── SÍ → Proceder a Milestone 3
│
├─► [M3] MILESTONE 3: Sub-agente Perfil Asmático (básico)
│   ├─ Nodo `asma_profile_node`: recibe datos de carrera + reporte subjetivo del usuario
│   ├─ Genera `profiles/asma_profile.md` v1 (estructura narrativa, no sistema de hipótesis todavía)
│   ├─ Detecta triggers básicos: "En carreras con temp <X, síntomas = Y"
│   └─ ✅ ENTREGABLE: Perfil asmático que se actualiza post-carrera con observaciones en lenguaje natural
│
│   DECISIÓN 3: ¿El perfil asmático captura patrones reales de tus carreras?
│   ├── NO → Ajustar prompts del sub-agente, mejorar detección de triggers
│   └── SÍ → Proceder a Milestone 4
│
├─► [M4] MILESTONE 4: Sub-agente Perfil Runner (básico)
│   ├─ Nodo `runner_profile_node`: recibe datos de carrera
│   ├─ Genera `profiles/runner_profile.md` v1 (VO2 estimado, VDOT, zonas de FC, economía)
│   ├─ Métricas calculadas por script determinístico (no agente) donde sea posible
│   └─ ✅ ENTREGABLE: Perfil runner con métricas de rendimiento que evolucionan
│
│   DECISIÓN 4: ¿Ambos perfiles coexisten sin contradecirse constantemente?
│   ├── NO → Revisar separación de dominios, ajustar prompts para evitar overlap
│   └── SÍ → Proceder a Milestone 5
│
├─► [M5] MILESTONE 5: Nodo Síntesis + Coach con paquete de contexto
│   ├─ Nodo `synthesis_node`: fusiona ambos perfiles en resumen unificado (~200 tokens)
│   ├─ Refactor `coach_node`: ya no recibe datos crudos — recibe "paquete de contexto" preparado
│   ├─ Paquete incluye: síntesis de estado + últimos mensajes + docs relevantes (si aplica)
│   ├─ El Coach puede presentar dilemas asmáticos vs. rendimiento y esperar decisión del usuario
│   └─ ✅ ENTREGABLE: Coach que conversa con contexto completo de tu estado asmático + runner
│
│   DECISIÓN 5: ¿El Coach presenta recomendaciones coherentes usando ambos perfiles?
│   ├── NO → Debuggear prompts, ajustar síntesis, revisar inyección de contexto
│   └── SÍ → Proceder a Milestone 6
│
├─► [M6] MILESTONE 6: Reporte mensual + Simulador de riesgo
│   ├─ Nodo `report_node`: genera reporte mensual markdown a demanda
│   ├─ Simulador integrado en Coach: "¿Qué pasaría si...?" con estimaciones de riesgo BIE
│   ├─ Reporte estructurado: sesiones, síntomas, uso de rescate, cumplimiento de protocolos, recomendaciones
│   └─ ✅ ENTREGABLE: `python run.py --mode report` genera informe mensual; Coach simula escenarios
│
│   DECISIÓN 6: ¿El MVP es funcional y útil para entrenar con asma?
│   ├── NO → Iterar, priorizar fixes, ajustar features
│   └── SÍ → 🎉 MVP LISTO → Proceder a Milestone 7+ (features avanzadas)
│
└─► [M7+] MILESTONE 7+: Features Avanzadas (post-MVP)
    ├─ Sistema de hipótesis con estados y confianza (reemplaza perfil narrativo simple)
    ├─ Revisión científica interna de hipótesis (Sub-Agente Científico confronta con docs/)
    ├─ Perfiles con 3 capas (Resumen / Detalle / Evidencia cruda)
    ├─ Perfil corregible por el usuario (el sistema respeta anotaciones manuales)
    ├─ Reporte mensual como checkpoint del perfil (archiva hipótesis descartadas)
    └─ ⏳ Cada feature se implementa como iteración independiente post-MVP
```

### Decisiones Clave en el Camino

| Punto de Decisión | Pregunta | Si es NO, la acción |
|---|---|---|
| D1 | ¿Pipeline genera datos válidos? | Iterar parser, validar con más archivos .fit |
| D2 | ¿Coach responde preguntas básicas? | Revisar system prompt, context window, modelo |
| D3 | ¿Perfil asmático captura patrones reales? | Ajustar prompts de detección, agregar más contexto médico |
| D4 | ¿Perfiles coexisten sin contradicción? | Revisar separación de dominios, ajustar scope de cada nodo |
| D5 | ¿Coach usa ambos perfiles coherentemente? | Debuggear inyección de contexto, ajustar síntesis |
| D6 | ¿MVP es útil para entrenar? | Priorizar fixes, recortar features si es necesario |

### Dependencias Técnicas

```
init_db.py (schema SQLite)
    └─► pipeline.py (depende de que exista la tabla `runs`)
        └─► langgraph scaffold (depende de que pipeline.py funcione)
            ├─► asma_profile_node (depende de pipeline + reporte subjetivo del usuario)
            └─► runner_profile_node (depende de pipeline, paralelizable con asma_profile)
                └─► synthesis_node (depende de ambos perfiles)
                    └─► coach_node refactor (depende de synthesis)
                        └─► report_node + simulador (dependen de coach funcional)
```

### Camino Crítico (lo que NO se puede paralelizar)

**Schema BD → Pipeline → LangGraph scaffold → Perfil Asmático → Síntesis → Coach refactor**

El Perfil Runner puede desarrollarse **en paralelo** con el Perfil Asmático una vez que el scaffold existe. El Reporte y Simulador son las hojas del árbol — dependen de todo lo anterior.

### Estimación de Esfuerzo (orden de magnitud)

| Milestone | Complejidad | Estimación | Bloqueante principal |
|---|---|---|---|
| M0 Schema BD | Baja | 0.5-1 sesión | Diseño de tablas MVP, migración inicial |
| M1 Pipeline .fit | Media | 1-2 sesiones | Parser de .fit, cálculo de métricas derivadas |
| M2 LangGraph scaffold | Media-Alta | 2-3 sesiones | Aprender LangGraph, modelar estado |
| M3 Perfil Asmático | Alta | 3-4 sesiones | Prompt engineering, calidad de detección |
| M4 Perfil Runner | Media | 2 sesiones | Cálculos determinísticos, menos complejo |
| M5 Síntesis + Coach | Alta | 3-4 sesiones | Prompt engineering del Coach, debugging |
| M6 Reporte + Simulador | Media | 2 sesiones | Formateo de reporte, lógica de simulación |
| **MVP Total** | | **~14-18 sesiones** | |

### Criterio de Éxito del MVP

> El usuario puede: (1) procesar un archivo .fit, (2) ver cómo se actualiza su perfil asmático y runner, (3) conversar con el Coach y recibir recomendaciones que integren ambos dominios, (4) generar un reporte mensual, (5) simular un escenario de entrenamiento y ver estimación de riesgo.

---

## Resumen de la Sesión de Brainstorming

### Ideas Aprobadas (14)

1. Sub-Agente Científico Evidence-Based
2. Análisis Cruzado de Métricas Running + Asma
3. Sub-Agente Perfil Asmático
4. Sub-Agente Perfil Runner
5. Reporte Mensual para Médico (controlado por usuario)
6. LangGraph como orquestador
7. Sistema de hipótesis científicas con ciclo de vida
8. Actualización post-reporte del usuario
9. Síntesis de estado unificado (5to nodo LangGraph)
10. Revisión científica interna de hipótesis
11. Perfiles con 3 capas (Resumen/Detalle/Evidencia)
12. Perfil corregible por el usuario
13. Simulador de riesgo BIE
14. Eliminación de RAG on-demand (paquete de contexto preparado)

### Arquitectura Final (5 nodos LangGraph + BD)

```
                    .fit file
                       │
                       ▼
[Pipeline] ──────► [SQLite BD] ◄────── Health log (usuario)
   │                    │
   │                    │ (queries SQL)
   │                    ▼
   │         [Perfil Asmático] + [Perfil Runner]
   │                    │
   │                    ▼
   │              [Síntesis]
   │                    │
   │         (paquete de contexto)
   │                    ▼
   └────────────► [Coach IA] ◄────── docs/ (base científica)
```

**Fuentes de verdad:**
- **BD SQLite**: Datos crudos, métricas calculadas, reportes subjetivos, historial de conversaciones.
- **Markdown profiles**: Interpretaciones narrativas escritas por los sub-agentes (asma_profile.md, runner_profile.md).
- **docs/**: Base científica estática (GINA 2024, ACSM, etc.).

### Decisiones Arquitectónicas Clave

- Perfiles en markdown narrativo, versionados con git
- Sub-agentes (no scripts) generan y actualizan perfiles
- El orquestador prepara paquete de contexto completo antes de invocar Coach
- Conflicto asmático vs. rendimiento → escalación al usuario
- MVP primero, features avanzadas post-MVP

### Próximo Paso Recomendado

**Milestone 1: Construir el Pipeline .fit funcional.** Es la raíz de todo el árbol. Sin datos estructurados, no hay perfiles, no hay coach, no hay nada.

¿Querés que arranquemos con el MVP? 🚀
