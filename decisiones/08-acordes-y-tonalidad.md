# 08 - Detección de acordes y tonalidad

Este archivo es el más importante de la carpeta: contiene el algoritmo completo, con sus reglas, desempates y ejemplos resueltos. Está aprobado por el autor (revisión 2026-10-17 en `archivos/autonomo_automatico.md`; casos aprobados el 2026-10-18 en `tests_md/deteccion_acordes_tonalidad.md`).

## 1. Autoría (debe destacarse en el README del proyecto)

- **El diseño es del autor.** Su idea central: nombrar cada acorde según la tonalidad en que se toca, y hacer que la detección entregue **todas las tonalidades candidatas** para que el usuario elija la que representa su canción, en lugar de imponer una. El registro de la sesión resume la idea del autor como «nombrar los acordes según la tonalidad, con caso base y paso inductivo».
- **Refinamientos propuestos por el harness de IA y aprobados por el autor:** puntaje sobre las 24 tonalidades, uso de la menor armónica, orden de sugerencia de las candidatas y nombre de respaldo para acordes sin nombre estándar.
- Motivo del cambio de diseño: la tonalidad depende de cómo resuelve la canción, algo que no se deduce solo del conjunto de acordes; por eso el sistema propone candidatas y el usuario elige. Reemplazó una versión anterior que elegía **una sola** tonalidad mediante cadenas de desempates (descartada: dejaba casos sin resolver).

Origen: `archivos/autonomo_automatico.md` (sección «Autoría»); `AGENTS.md` (README, «Mi rol»); Engram 263, 260, 269.

## 2. Propiedades generales

| Propiedad | Regla |
| --- | --- |
| Determinista | A las mismas notas y acordes corresponde siempre el mismo resultado (DET-023 y DET-122 ejecutan 100 veces los casos y exigen resultado idéntico). |
| Independiente del orden | El orden en que aparecen los acordes en la canción no influye en las candidatas (DET-121). |
| Nunca «desconocido» | Ningún acorde ni tonalidad queda como «desconocido». Si ningún nombre estándar calza, el acorde se nombra con un nombre de respaldo (fundamental + intervalos). Es una restricción de calidad (`archivos/restricciones.md`) que se aplica por igual al detector de acordes y al de tonalidad. Sin acordes, la tonalidad no es «desconocida»: las candidatas son un arreglo vacío y `key = null`. |
| Módulo propio | `restricciones.md` indica que «es posible que se deba crear un módulo específico» para el detector. |
| Recalcula en cada cambio | Se recalcula al agregar, editar o borrar un acorde. |
| Tablaturas no cuentan | Las tablaturas no se usan para detectar la tonalidad. |

### Interfaz bajo prueba (ilustrativa, no vinculante)

Las firmas las decide la arquitectura; los casos aprobados usan estos nombres:

- `name_chord(notes, key) -> str`: nombre de un acorde (lista de notas MIDI) en una tonalidad.
- `candidate_keys(chords) -> list[str]`: arreglo ordenado de tonalidades candidatas.
- `analyze(chords, key_mode, selected_key) -> {candidates, key, names}` (con `key_reset`): combina ambas. `selected_key` es la elección del usuario o `null`.

Origen: `autonomo_automatico.md`; `tests_md/deteccion_acordes_tonalidad.md` (interfaz propuesta).

## 3. Datos de entrada

- Cada acorde llega como una lista de **notas MIDI** (`notes`). Referencia: `C4 = 60`.
- **El bajo es la nota MIDI más grave**, no la primera del arreglo (DET-009).
- Las octavas duplicadas no cambian el resultado (DET-010).
- Se trabaja con **clases de altura** (pitch classes) para decidir qué acorde forman las notas.
- Un acorde necesita **al menos 2 clases de altura distintas**; si no, error de validación (`422 validation_error` en la API). Ejemplos: `[60]` y `[48,60]` son inválidos (DET-022).

Tríadas usadas como entradas en los casos (nombre → notas MIDI): `C [48,52,55]`, `Cm [48,51,55]`, `C+ [48,52,56]`, `Db [49,53,56]`, `D [50,54,57]`, `Dm [50,53,57]`, `E [40,44,47]`, `Em [52,55,59]`, `F [41,45,48]`, `Fm [41,44,48]`, `F# [42,46,49]`, `G [43,47,50]`, `G#dim [44,47,50]`, `Ab [44,48,51]`, `A [45,49,52]`, `Am [45,48,52]`, `Bb [46,50,53]`, `Bbm [46,49,53]`.

## 4. Nombre de un acorde

### 4.1 Identificación (revisión 2026-10-17, aprobada; reemplaza «la nota más grave es la fundamental»)

1. Se busca qué acorde conocido forman las notas, **probando cada una como fundamental**.
2. Si hay varias lecturas válidas (por ejemplo `C6` = `Am7` en notas), **gana la que tiene el bajo (nota más grave) como fundamental**.
3. Si aún empatan, **gana la lectura diatónica a la tonalidad seleccionada**.
4. Si el bajo no es la fundamental, se escribe **con barra** (ejemplo `C/E`).

Consecuencias comprobadas por casos:

- Mismas clases de altura con distinto bajo dan distinto nombre: `[45,48,52,55]` (bajo A) = `Am7`; `[48,52,55,57]` (bajo C) = `C6` (DET-007, DET-008).
- El bajo como fundamental gana sobre la coherencia con la tonalidad: `name_chord([48,52,55,57], "Am")` = `C6` (DET-021).
- Tríada aumentada (simétrica): en `Fm`, `[48,52,56]` tiene lecturas válidas `C+`, `E+` y `Ab+`; gana la que tiene el bajo como fundamental: `C+` (DET-020).

### 4.2 Notación (revisión 2026-10-17, aprobada): solo ASCII

- **Calidades:** `m`, `dim`, `+`, `7`, `maj7`, `m7`, `6`, `m7b5`, `dim7`, `sus2`, `sus4`, `add9`, `9`, `maj9`, `m9`, `11`, `m11`, `13`.
- **Tensiones alteradas entre paréntesis:** `G7(b9)`, `C7(#11)`.
- **Tonalidades como cadena:** `"C"`, `"Am"`, `"F#m"`, `"Bb"`.
- Notas de los ejemplos aprobados, para fijar el significado de cada calidad: `C` = C E G; `Cm` = C Eb G; `C+` = C E G#; `Bdim` = B D F; `G7` = G B D F; `Cmaj7` = C E G B; `Am7` = A C E G; `C6` = C E G A; `G7(b9)` = G B D F Ab; `Cmaj9` = C E G B D; `C9` = C E G Bb D. (Las fuentes no incluyen una tabla completa de intervalos por calidad; ver archivo 15.)

### 4.3 Grafía enarmónica

- **Acordes diatónicos a la tonalidad seleccionada:** el nombre y la grafía (F# frente a Gb) se eligen coherentes con la tonalidad. Ejemplos: `[42,46,49]` en `B` = `F#`; en `Db` = `Gb`; `[49,53,56]` en `F#` = `C#`; en `Ab` = `Db` (DET-015 a DET-018). `[42,45,48]` en `G` = `F#dim` (DET-014).
- **Acordes no diatónicos** (revisión 2026-10-17, aprobada): se elige la grafía enarmónica que da **menos alteraciones** al escribir las notas del acorde (`Ab` y no `G#` en C; `F#dim` y no `Gbdim`). Ejemplo: `[44,48,51]` en `C` = `Ab`, porque `Ab C Eb` tiene 2 alteraciones frente a `G# B# D#` con 3 (DET-019).
- **Empate** en número de alteraciones: bemoles en tonalidades con bemoles y en C/Am; sostenidos en tonalidades con sostenidos.

### 4.4 Acordes de pocas notas (revisión 2026-10-17, aprobada)

| Notas | Nombre | Caso |
| --- | --- | --- |
| 1 clase de altura | No es un acorde: error de validación (`422`) | DET-022, CHD-017 |
| Quinta justa (C G) | `C5` | DET-024, CHD-018 |
| Tercera mayor (C E) | `C(no5)` | DET-025 |
| Tercera menor (C Eb) | `Cm(no5)` | DET-026 |
| Otro intervalo (C F#) | Nombre de respaldo `C(#11)` | DET-027 |

Las díadas puntúan como cualquier acorde (todas sus notas deben caber en la tonalidad).

### 4.5 Nombre de respaldo

Si ningún nombre estándar calza, el acorde se nombra como **fundamental + intervalos**, tomando el **bajo como fundamental**. Ejemplo literal de la fuente: `[48,49,54]` (C Db F#) = `C(b9,#11)` (DET-012). DET-013 exige un barrido: todo conjunto de 2 a 12 clases de altura, con cada nota posible como bajo, en las 24 tonalidades, produce siempre un nombre no vacío y distinto de `unknown`/`desconocido`.

Origen: `archivos/autonomo_automatico.md` (revisión 2026-10-17); `tests_md/deteccion_acordes_tonalidad.md` (A, DET-001 a DET-027); Engram 271.

### 4.6 Quinta omitida (revisión 2026-10-31, aprobada por el autor)

Un acorde que conserva la tercera y al menos otra nota además de la fundamental puede omitir la **quinta justa**. Se nombra igual que el acorde completo, sin marcarlo: `E G G# D` = `E7(#9)`, `C E Bb` = `C7`, `C E B` = `Cmaj7`, `C E Bb D` = `C9`, `C Eb Bb` = `Cm7`. Un acorde completo siempre tiene prioridad sobre una lectura sin quinta (`C E A` sigue siendo `Am/C`). Las díadas siguen la sección 4.4 y el nombre de respaldo queda para lo que no calce.

## 5. Tonalidades candidatas

### 5.1 Puntaje

En cada cambio se puntúan **las 24 tonalidades** (12 mayores y 12 menores) según cuántos acordes de la canción son diatónicos en cada una.

- **En menor puntúan solo los acordes de la menor natural.**
- **Un acorde suma en una tonalidad solo si todas sus notas pertenecen a ella** (`Cmaj7` suma en C; `C7` no).
- **Tensiones alteradas** (`b9`, `#9`, `#11`, `b13`): solo se evalúa la **tríada principal** del acorde.
- **Tensiones naturales** (`9`, `11`, `13`): se evalúan **todas** sus notas.
- Los acordes con **nombre de respaldo** siguen la misma regla.
- **Acordes duplicados** (mismas clases de altura) cuentan una sola vez (S4).
- **Pertenencia por clases de altura** (S2): un acorde «es» un acorde diatónico si tiene el mismo conjunto de clases de altura. Importa en la tríada aumentada, simétrica: `C+` = `E+` = `G#+` = `Ab+`.
- La función devuelve un **arreglo** con **todas las tonalidades empatadas en el puntaje máximo**.

### 5.2 Orden del arreglo (orden de sugerencia; nunca descarta opciones)

1. **Menores con más acordes de la menor armónica presentes** (V mayor, vii°, III aumentado, incluidas sus séptimas: V7, vii°7). Se cuentan acordes armónicos **distintos** presentes; una tonalidad mayor cuenta 0 (S1). Si dos menores empatan en este criterio, se sigue con los siguientes. Ejemplo: en Am, `E7` y `G#dim7` cuentan como armónicos.
2. **Tonalidades cuyo acorde I aparece** en la canción.
3. **Mayores antes que menores.**
4. **Orden del círculo de quintas desde C** (S5):
   - Mayores: `C, G, D, A, E, B, F#, Db, Ab, Eb, Bb, F`.
   - Menores, en la posición de su relativa mayor: `Am, Em, Bm, F#m, C#m, G#m, Ebm, Bbm, Fm, Cm, Gm, Dm`.

Ejemplos de la fuente: `[C, F, G, E]` → `[Am, C]`; `[C, G, D]` → `[G, Em]`.

### 5.3 Casos límite

- **Puntaje máximo 0** (ningún acorde calza en ninguna tonalidad, por ejemplo `[C+]`): se devuelve un **arreglo vacío**, igual que sin acordes. En `auto`, `key = null` (DET-124).
- **Sin acordes:** arreglo vacío. En `auto`, la tonalidad queda vacía (`null`) y la interfaz invita a agregar acordes; al agregar el primero se selecciona la **primera candidata sin aviso** (`key_reset = false`), porque no había elección previa (DET-212).

Origen: `autonomo_automatico.md`; `tests_md/deteccion_acordes_tonalidad.md` (S1 a S5, B); Engram 269, 270.

## 6. Tonalidad vigente y nombres de los acordes

Los nombres de los acordes se calculan con la **tonalidad seleccionada**, eligiendo la interpretación y la grafía enarmónica coherentes con ella. Mientras el usuario no elija, se usa **siempre la primera tonalidad del arreglo**, aunque otras empaten en puntaje (DET-207).

| Modo (`key_mode`) | Comportamiento |
| --- | --- |
| `auto` | La tonalidad se elige del arreglo de candidatas (por defecto, la primera). Si tras un cambio la tonalidad elegida **sigue** en el arreglo, se conserva aunque el orden cambie (`key_reset = false`, DET-213). Si un cambio en los acordes la deja **fuera** del arreglo, se vuelve a la primera candidata y se **avisa al usuario con una notificación breve (tipo snackbar)** de que su tonalidad cambió (`key_reset = true`, DET-214). En `auto` el usuario solo puede elegir entre las candidatas; elegir otra tonalidad responde `422 validation_error` (para otra tonalidad hay que pasar a `manual`, KEY-004). |
| `manual` | El usuario fija **cualquier** tonalidad (aunque no esté entre las candidatas, DET-208) y los nombres se adaptan a ella. Las candidatas **se siguen calculando** y se muestran solo como sugerencia, sin afectar la tonalidad fijada ni los nombres (DET-211). Cambiar la tonalidad manual recalcula los nombres de todos los acordes (KEY-003). |
| Paso `manual` → `auto` | Misma regla: si la tonalidad fijada está entre las candidatas se conserva (`key_reset = false`); si no, se toma la primera y se avisa (`key_reset = true`) (DET-215, KEY-005). |

Otras reglas del modelo: `key_mode` por defecto `auto` en canciones nuevas; las canciones migradas del modelo antiguo quedan en `manual`. Con `key_mode = manual`, agregar acordes de otra tonalidad no cambia `key` (KEY-002).

Nota: el componente snackbar **no existe aún** en el design system; Engram 275 registra que debe proponerse antes del trabajo de frontend correspondiente (archivo 15).

## 7. Ejemplos resueltos (casos aprobados)

Los arreglos de la sección B se calcularon con un script de puntuación que aplica las reglas y los supuestos S1 a S5. «Máx.» es el puntaje máximo.

### 7.1 Nombre de cada acorde

| ID | Entrada | Esperado |
| --- | --- | --- |
| DET-001 | `name_chord([48,52,55], "C")` | `"C"` |
| DET-002 | `name_chord([45,48,52], "C")` | `"Am"` |
| DET-003 | `name_chord([47,50,53], "C")` (B D F) | `"Bdim"` |
| DET-004 | `name_chord([48,52,56], "Am")` (C E G#) | `"C+"` (III+ de la menor armónica) |
| DET-005 | `name_chord([43,47,50,53], "C")` (G B D F) | `"G7"` |
| DET-006 | `name_chord([48,52,55,59], "C")` (C E G B) | `"Cmaj7"` |
| DET-007 | `name_chord([45,48,52,55], "C")` (A C E G, bajo A) | `"Am7"` |
| DET-008 | `name_chord([48,52,55,57], "C")` (C E G A, bajo C) | `"C6"`: mismas clases de altura que DET-007, distinto bajo, distinto nombre |
| DET-009 | `name_chord([55,48,52], "C")` | `"C"`: el bajo es la nota MIDI más grave, no la primera del arreglo |
| DET-010 | `name_chord([48,52,55,60,64], "C")` (octavas duplicadas) | `"C"` |
| DET-011 | `name_chord([52,55,60], "C")` (E G C, bajo E) | `"C/E"`: las notas forman C mayor; el bajo no es la fundamental, se escribe con barra |
| DET-012 | `name_chord([48,49,54], "C")` (C Db F#) | `"C(b9,#11)"` (ejemplo literal de la fuente; fundamental = bajo) |
| DET-013 | Barrido: todo conjunto de 2 a 12 clases de altura, cada nota posible como bajo, en las 24 tonalidades | Siempre un nombre no vacío, distinto de `"unknown"` / `"desconocido"` |
| DET-014 | `name_chord([42,45,48], "G")` (F# A C) | `"F#dim"` (vii° de G; grafía con sostenido) |
| DET-015 | `name_chord([42,46,49], "B")` | `"F#"` (V de B) |
| DET-016 | `name_chord([42,46,49], "Db")` | `"Gb"` (IV de Db): mismas notas que DET-015, otra grafía |
| DET-017 | `name_chord([49,53,56], "F#")` | `"C#"` (V de F#) |
| DET-018 | `name_chord([49,53,56], "Ab")` | `"Db"` (IV de Ab) |
| DET-019 | `name_chord([44,48,51], "C")` (acorde no diatónico en C) | `"Ab"`: Ab C Eb (2 alteraciones) frente a G# B# D# (3) |
| DET-020 | `name_chord([48,52,56], "Fm")` | `"C+"`: lecturas válidas C+, E+ y Ab+; gana la que tiene el bajo como fundamental |
| DET-021 | `name_chord([48,52,55,57], "Am")` | `"C6"`: el bajo como fundamental gana sobre la coherencia con la tonalidad |
| DET-022 | `name_chord([60], "C")` y `name_chord([48,60], "C")` (una sola clase de altura) | Error de validación (en la API, `422 validation_error`) |
| DET-024 | `name_chord([48,55], "C")` (C G) | `"C5"` |
| DET-025 | `name_chord([48,52], "C")` (C E) | `"C(no5)"` |
| DET-026 | `name_chord([48,51], "Cm")` (C Eb) | `"Cm(no5)"` |
| DET-027 | `name_chord([48,54], "C")` (C F#) | `"C(#11)"` (nombre de respaldo) |
| DET-028 | `name_chord([40,55,56,62], "C")` (E G G# D) | `"E7(#9)"`: quinta omitida (sección 4.6) |
| DET-029 | `name_chord([48,64,70], "C")` (C E Bb) | `"C7"` |
| DET-030 | `name_chord([48,64,71], "C")` (C E B) | `"Cmaj7"` |
| DET-031 | `name_chord([48,63,70], "C")` (C Eb Bb) | `"Cm7"` |
| DET-032 | `name_chord([48,64,70,74], "C")` (C E Bb D) | `"C9"` |
| DET-033 | `name_chord([52,60,70], "C")` (E C Bb) | `"C7/E"`: la barra sigue aplicando |
| DET-034 | `name_chord([48,64,69], "C")` (C E A) | `"Am/C"`: el acorde completo gana sobre la lectura sin quinta |
| DET-035 | `name_chord([48,67,71], "C")` (C G B) | `"C(5,7)"`: sin tercera no hay lectura sin quinta |
| DET-036 | `candidate_keys` de C, F y G B F | `["C", "Am"]`: el acorde sin quinta puntúa con todas sus notas |
| DET-023 | DET-001 a DET-018 ejecutados 100 veces | Resultado idéntico en todas |

### 7.2 Arreglo de tonalidades candidatas

| ID | Entrada `candidate_keys(...)` | Esperado | Máx. | Por qué ese orden |
| --- | --- | --- | --- | --- |
| DET-101 | `[]` | `[]` | - | Sin acordes. |
| DET-102 | `[C]` | `[C, G, F, Am, Em, Dm]` | 1 | Ninguna menor tiene un acorde armónico presente; el I de C aparece (criterio 2); luego mayores G, F por círculo de quintas (criterio 4); menores por círculo (S5). |
| DET-103 | `[Am]` | `[Am, C, G, F, Em, Dm]` | 1 | El I de Am aparece (criterio 2); el resto por criterios 3 y 4. |
| DET-104 | `[C, F, G]` | `[C, Am]` | 3 | Relativas empatadas; el I de C aparece y el de Am no (criterio 2). |
| DET-105 | `[Am, F, G]` | `[Am, C]` | 3 | Relativas empatadas; el I de Am aparece (criterio 2) aunque C sea mayor. |
| DET-106 | `[C, F, G, E]` | `[Am, C]` | 3 | Ejemplo de la fuente. E no puntúa (no es menor natural) pero es V armónico de Am (criterio 1), que pasa delante de C aunque el I de C aparezca. |
| DET-107 | `[C, G, D]` | `[G, Em]` | 3 | Ejemplo de la fuente. Em no tiene acordes armónicos (B, D#dim, G+); el I de G aparece (criterio 2). |
| DET-108 | `[Dm, Em]` | `[C, Am]` | 2 | Ningún I aparece; mayor antes que menor (criterio 3). |
| DET-109 | `[Am, E]` | `[Am, E, C, G, A, B, F, Em, F#m, C#m, G#m, Dm]` | 1 | E no suma a Am (máx. 1, 12 empatadas), pero ordena: Am tiene 1 armónico (criterio 1); el I de E aparece (criterio 2); resto por criterios 3 y 4. |
| DET-110 | `[C, Cm, G, Ab]` | `[Cm, Fm, C, G, Ab, Eb, Am, Em]` | 2 | Cm (V = G) y Fm (V = C) tienen 1 armónico (criterio 1); entre ellas, el I de Cm aparece (criterio 2). Luego mayores con I presente C, G, Ab (criterio 4); Eb; menores Am, Em. |
| DET-111 | `[C, Cm, C+, G, Db]` | `[Fm, Am, C, G, Ab, Em]` | 2 | Fm tiene 2 armónicos (C, y C+ = Ab+ por S2); Am tiene 1 (C+). |
| DET-112 | `[C, F]` | `[C, F, Am, Dm]` | 2 | C y F tienen I presente; C antes que F por círculo de quintas. |
| DET-113 | `[F#]` | `[F#, B, Db, G#m, Ebm, Bbm]` | 1 | I de F# presente; B y Db por círculo; menores por círculo (S5). Grafías según S5. |
| DET-114 | `[C, F, G, Ab]` (Ab prestado) | `[C, Am]` | 3 | Ab no es diatónico en C ni en Am; ninguna tonalidad con Ab llega a 3. Mismo resultado que DET-104. |
| DET-115 | `[C, F, G, Am, D]` (D = V/V) | `[C, G, Am, Em]` | 4 | I presentes: C, G, Am (criterio 2); mayores antes (criterio 3): C, G; luego Am; Em al final. |
| DET-116 | `[C, F, G]` (= DET-104); se borra G → `[C, F]` | `[C, F, Am, Dm]` | 2 | Se recalcula al borrar; ver DET-112. |
| DET-117 | `[C, F, G]`; se edita G a E → `[C, F, E]` | `[Am, C, F, Dm]` | 2 | Se recalcula al editar; E es V armónico de Am. |
| DET-118 | `[F#]` (= DET-113); se agrega Ab → `[F#, Ab]` | `[Db, Bbm]` | 2 | Se recalcula al agregar; ningún I presente; mayor antes (criterio 3). |
| DET-119 | `[Fm, Bbm, C+]` | `[Fm, Bbm, Db, Ab]` | 2 | Con S2, C+ es III+ de Fm. |
| DET-120 | `[Am, C+]` | `[Am, C, G, F, Em, Dm]` | 1 | C+ no puntúa (no hay tríada aumentada diatónica en mayor ni en menor natural); ordena a Am primero (criterio 1). |
| DET-121 | `[G, C, F]` (DET-104 en otro orden) | `[C, Am]` | 3 | El orden de los acordes en la canción no influye. |
| DET-122 | DET-101 a DET-121 ejecutados 100 veces | Resultado idéntico en todas | - | Determinismo. |
| DET-123 | `[Bb, Bb, A, E]` (dos versiones de Bb con las mismas notas) | `[A, E, F#m, C#m]` | 2 | S4: los dos Bb cuentan una vez. |
| DET-124 | `[C+]` (ningún acorde diatónico en ninguna tonalidad) | `[]` | 0 | Puntaje máximo 0: se trata como una canción sin acordes (en `auto`, `key = null`). |
| DET-125 | `[[43,47,50,53], C]` (G7 y C) | `[C, Am]` | 2 | G7 (G B D F) solo cabe completo en C / Am natural. |
| DET-126 | `[G7(b9), C]` (G7(b9) = G B D F Ab) | `[C, G, Am, Em]` | 2 | Tensión alterada `b9`: G7(b9) puntúa solo como su tríada G (S3); resultado igual a `[G, C]`. C y G tienen su I presente; mayores antes que menores. |
| DET-127 | `[Cmaj9]` (C E G B D) | `[C, G, Am, Em]` | 1 | Tensión natural: se evalúan todas sus notas, que caben en C, G, Am y Em (S3). C tiene su I presente. |
| DET-128 | `[C9]` (C E G Bb D) | `[F, Dm]` | 1 | Todas sus notas caben solo en F y Dm; contrasta con DET-127 (Bb excluye C y G). |

### 7.3 Tonalidad seleccionada y nombres

| ID | Precondiciones / Acción | Esperado |
| --- | --- | --- |
| DET-201 | `analyze([C, F, G, E], auto, null)` | `candidates = [Am, C]`, `key = "Am"` (la primera), `names = ["C","F","G","E"]` |
| DET-202 | `analyze([[42,46,49]], auto, null)` | `candidates = [F#, B, Db, G#m, Ebm, Bbm]`, `key = "F#"`, `names = ["F#"]` |
| DET-203 | Como DET-202, el usuario elige `Db` (`selected_key = "Db"`) | `key = "Db"`, `names = ["Gb"]`; `candidates` sin cambio |
| DET-204 | Como DET-202, el usuario elige `Ebm` | `key = "Ebm"`, `names = ["Gb"]` |
| DET-205 | Como DET-202, el usuario elige `G#m` | `key = "G#m"`, `names = ["F#"]` |
| DET-206 | Como DET-202 sin elección del usuario; se agrega Ab `[44,48,51]` | `candidates = [Db, Bbm]`, `key = "Db"`; `names = ["Gb","Ab"]`: el primer acorde se vuelve a nombrar con la nueva primera candidata |
| DET-207 | `analyze([C, F, G], auto, null)`: hay empate (`[C, Am]`) | `key = "C"`: se usa la primera aunque Am empate |
| DET-208 | `analyze([C, F, G], manual, "D")` | `key = "D"` aunque no esté entre las candidatas; `names = ["C","F","G"]` |
| DET-209 | `analyze([[42,46,49],[49,53,56]], manual, "F#")` | `key = "F#"`, `names = ["F#","C#"]` |
| DET-210 | Como DET-209, el usuario cambia la tonalidad manual a `"Db"` | `key = "Db"`, `names = ["Gb","Db"]` |
| DET-211 | `analyze([], manual, "D")` (se borraron todos los acordes) | `key = "D"` (fijada por el usuario), `names = []`, `candidates = []`. En `manual` las candidatas se calculan siempre y se devuelven como sugerencia, sin afectar `key` ni `names` |
| DET-212 | `analyze([], auto, null)` | `candidates = []`, `names = []`, `key = null`. Al agregar el primer acorde se selecciona la primera candidata con `key_reset = false` |
| DET-213 | `[C, F, G]`, `auto`, el usuario eligió `C`; se agrega E → candidatas `[Am, C]` | `C` sigue en el arreglo: se mantiene `key = "C"`, nombres con C, `key_reset = false` |
| DET-214 | `[C, F, G]`, `auto`, el usuario eligió `Am`; se edita F a D → candidatas `[G, Em]` | Am ya no está: `key = "G"` (la primera), nombres recalculados con G, `key_reset = true` para que el frontend avise al usuario |
| DET-215 | Canción en `manual` con `key = "D"`; pasa a `auto` | Si `D` está en el arreglo, se conserva (`key_reset = false`); si no, `key` = primera candidata y `key_reset = true` |

## 8. Supuestos aprobados de la propuesta (S1 a S6)

| Supuesto | Detalle |
| --- | --- |
| S1. Criterio 1 | Se cuentan acordes armónicos **distintos** presentes; una mayor cuenta 0. Si dos menores empatan, se sigue con los criterios 2 a 4. |
| S2. Pertenencia por clases de altura | Un acorde es diatónico si tiene el mismo conjunto de clases de altura (importa en la tríada aumentada). |
| S3. Puntaje con todas las notas | Un acorde suma solo si todas sus notas pertenecen a la tonalidad; con tensiones alteradas (`b9`, `#9`, `#11`, `b13`) solo se evalúa la tríada; con naturales (`9`, `11`, `13`), todas las notas; nombres de respaldo, igual. Los acordes de la menor armónica incluyen sus séptimas (`E7`, `G#dim7` en Am). |
| S4. Duplicados | Acordes con las mismas clases de altura cuentan una vez. |
| S5. Círculo de quintas | Mayores: `C, G, D, A, E, B, F#, Db, Ab, Eb, Bb, F`. Menores en la posición de su relativa mayor: `Am, Em, Bm, F#m, C#m, G#m, Ebm, Bbm, Fm, Cm, Gm, Dm`. Fija también la grafía de las tonalidades devueltas. |
| S6. Notación | Tonalidad: `"C"`, `"Am"`, `"F#m"`, `"Bb"`. Calidades de acorde: ver 4.2. |

Todas las preguntas abiertas de la propuesta de detección quedaron resueltas (13 de 13): séptimas y tensiones, acordes repetidos, puntaje máximo 0, círculo de quintas para menores, grafía de tonalidades, tríada aumentada, bajo frente a interpretación, grafía no diatónica, notación, conjuntos de 1 o 2 notas, elección previa del usuario, sin acordes/manual, paso manual a auto.

## 9. Descartado (solo por el motivo)

- **Una sola tonalidad elegida por cadena de desempates** (versión anterior): descartada porque dejaba casos sin resolver (`[C, G, D]`: G y Em empatan en 3, la actual C tiene 2, el primer acorde no es el I de ninguna). La reemplaza el arreglo de candidatas.
- **La menor armónica dentro del puntaje** (aprobado el 2026-10-17 y luego reemplazado): hoy la armónica **solo ordena** (criterio 1); el puntaje usa la menor natural.
- **«La nota más grave es la fundamental»**: reemplazada por la regla de 4.1 (prueba cada nota como fundamental).

Origen: `archivos/autonomo_automatico.md`; `tests_md/deteccion_acordes_tonalidad.md`; `archivos/restricciones.md`; Engram 260, 263, 269, 270, 271; `odd/tasks/tests-proposal.md` (hallazgo de 2026-10-17).
