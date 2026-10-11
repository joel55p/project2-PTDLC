# CYK Parser & Simplificación de Gramáticas a CNF — Proyecto 2

Implementación completa en Python 3 del algoritmo **Cocke-Younger-Kasami (CYK)** para parsing de Gramáticas Libres de Contexto (CFG) y el algoritmo de simplificación y transformación a **Forma Normal de Chomsky (CNF)**.

Desarrollado para el curso de **Teoría de la Computación 2024**.

---

## Características Principales

- **Simplificación y conversión a CNF paso a paso:**
  - Paso 0: Normalización del símbolo inicial.
  - Paso 1: Eliminación de producciones épsilon ($\epsilon$ / variables anulables).
  - Paso 2: Eliminación de producciones unitarias ($A \to B$).
  - Paso 3: Eliminación de símbolos inútiles (no generadores e inalcanzables).
  - Paso 4: Binarización de reglas largas y aislamiento de terminales mixtos.
- **Algoritmo CYK con Programación Dinámica:**
  - Tabla triangular y matriz de búsqueda eficiente $O(1)$ por regla.
  - Veredicto determinista: **SÍ** si la frase pertenece al lenguaje, **NO** en caso contrario.
  - Medición precisa de tiempo de ejecución en milisegundos y microsegundos.
- **Construcción y renderizado del Parse Tree:**
  - Representación visual jerárquica en ASCII (árbol conectivo).
  - Notación de corchetes estilo Penn Treebank / LISP.
  - Generación de reportes gráficos interactivos autónomos en **HTML / SVG**.
- **Menú interactivo en consola:** Mismo patrón de interfaz limpia y robusta utilizado en `shuntingyard.py` y `Balanceo.py`.
- **Suite de pruebas unitarias (`unittest`)** automatizada con cobertura de gramática y algoritmos.

---

## Requisitos

- **Python 3.8+**
- **Sin dependencias externas requeridas** (opera 100% con la biblioteca estándar de Python: `typing`, `time`, `re`, `sys`, `unittest`).

---

## Cómo Ejecutar el Programa

El repositorio incluye la gramática de prueba del proyecto (`gramatica_ingles.txt`) y una batería de 26 frases de prueba (`frases.txt`).

Para iniciar la aplicación interactiva:

```bash
python main.py
```

Aparecerá el menú principal:

```
=======================================================
                  MENÚ PRINCIPAL
=======================================================
1. Cargar y simplificar gramática a CNF (Paso a paso)
2. Validar frases desde archivo (Modo Resumen)
3. Validar frases desde archivo paso a paso (Tabla CYK + Árbol)
4. Ingresar frase manualmente por teclado
5. Generar reporte HTML/SVG interactivo de una frase
6. Cambiar archivo de gramática activa
7. Salir
=======================================================
Seleccione una opción (1-7):
```

### Opciones del Menú

- **Opción 1:** Carga una gramática (por defecto `gramatica_ingles.txt` o una personalizada como `gramatica_simplificacion_demo.txt`), valida si ya cumple CNF y ejecuta los 5 pasos del algoritmo de simplificación mostrando el estado intermedio de las reglas.
- **Opción 2:** Lee un archivo de frases línea por línea (por defecto `frases.txt`), procesa cada frase e imprime una tabla resumen con el veredicto (**SÍ / NO**), tiempo de ejecución individual en milisegundos, conteo de palabras y métricas globales.
- **Opción 3:** Lee el archivo de frases pero muestra el desglose completo de cada una: la progresión de la tabla dinámica CYK por longitudes, la matriz triangular en 2D, el veredicto, el tiempo y el **Parse Tree** completo en formato árbol ASCII y corchetes.
- **Opción 4:** Permite al usuario escribir interactivamente cualquier frase en inglés (por ejemplo: `She eats a cake with a fork` o `The cat drinks the beer`) y ver los resultados inmediatos.
- **Opción 5:** Genera un archivo `reporte_cyk.html` interactivo y autocontenido con la matriz triangular estilizada y el diagrama vectorial SVG del árbol de derivación para abrir en cualquier navegador web.
- **Opción 6:** Cambia la gramática activa en memoria por otra ruta o archivo.
- **Opción 7:** Finaliza la ejecución del programa.

> **Nota de entrada:** Al solicitar nombres de archivo, si se presiona `Enter` se usará el archivo por defecto. Si se omite la extensión `.txt`, el programa la agregará automáticamente.

---

## Salida Esperada

### Modo Resumen (Opción 2)
```
================================================================================
  VALIDACIÓN DE FRASES: frases.txt (Modo Resumen)
================================================================================
  #  Veredicto  Tiempo         Palabras   Frase
--------------------------------------------------------------------------------
  1  SÍ [ACEPT] 0.1539 ms      7          "She eats a cake with a fork"
  2  SÍ [ACEPT] 0.0383 ms      5          "The cat drinks the beer"
  3  SÍ [ACEPT] 0.0334 ms      7          "He cuts the meat with a knife"
 ...
 14  NO  [RECH] 0.0160 ms      6          "He cuts meat with a knife"
 15  NO  [RECH] 0.0092 ms      4          "Cat drinks the beer"
--------------------------------------------------------------------------------
>> Total procesadas: 26 | Aceptadas (SÍ): 13 | Rechazadas (NO): 13
>> Tiempo total: 0.5478 ms | Tiempo promedio por frase: 0.0211 ms
================================================================================
```

### Modo Detallado / Frase Individual (Opciones 3 y 4)
```
===========================================================================
  ANÁLISIS DE LA FRASE: "The cat drinks the beer"
===========================================================================
>> Tokens identificados (5): ['the', 'cat', 'drinks', 'the', 'beer']
>> ¿Pertenece al lenguaje?: SÍ
>> Tiempo empleado:         0.0383 ms (38.30 µs)

--- Matriz Triangular CYK ---
l \ i  i=0 (the)   i=1 (cat)  i=2 (drinks) i=3 (the)   i=4 (beer) 
==================================================================
l=5      {S}                                                     
l=4       ∅           ∅                                          
l=3      {S}          ∅          {VP}                            
l=2      {NP}         ∅           ∅          {NP}                
l=1     {Det}        {N}        {V,VP}      {Det}        {N}     

--- Parse Tree (1 derivación/es válida/s) ---
└── S
    ├── NP
    │   ├── Det ("the")
    │   └── N ("cat")
    └── VP
        ├── V ("drinks")
        └── NP
            ├── Det ("the")
            └── N ("beer")

Notación de corchetes: [S [NP [Det the] [N cat]] [VP [V drinks] [NP [Det the] [N beer]]]]
===========================================================================
```

---

## Formato de Archivos de Gramática

Las reglas se escriben en líneas individuales con formato:
```text
S -> NP VP
VP -> VP PP | V NP | cooks | drinks | eats | cuts
PP -> P NP
NP -> Det N | he | she
V -> cooks | drinks | eats | cuts
P -> in | with
N -> cat | dog | beer | cake | juice | meat | soup | fork | knife | oven | spoon
Det -> a | the
```

- Las alternativas se separan por `|`.
- El símbolo inicial por defecto es la cabeza de la primera regla (o puede especificarse).
- Las líneas vacías o iniciadas por `#` son comentarios.
- Símbolo épsilon soportado como: `ε`, `epsilon`, o `eps`.

---

## Ejecución de Pruebas Unitarias

Para correr la suite automatizada de pruebas:

```bash
python -m unittest test_cyk.py
```

Salida esperada:
```
..........
----------------------------------------------------------------------
Ran 10 tests in 0.001s

OK
```

---

## Estructura del Repositorio

- **`main.py`** — Aplicación de consola interactiva con menús y trazas.
- **`grammar.py`** — Representación de CFG y algoritmo completo de simplificación a Forma Normal de Chomsky (CNF).
- **`cyk.py`** — Algoritmo de Cocke-Younger-Kasami con programación dinámica, temporizador de alta precisión y reconstrucción de Parse Tree.
- **`visualizer.py`** — Generador de reportes visuales en HTML/SVG interactivo.
- **`test_cyk.py`** — Batería de pruebas unitarias automatizadas (`unittest`).
- **`gramatica_ingles.txt`** — Gramática de frases en inglés del Proyecto 2.
- **`frases.txt`** — Conjunto de pruebas con frases válidas y contraejemplos inválidos.
- **`gramatica_simplificacion_demo.txt`** — Gramática con épsilon, unitarias y símbolos inútiles para demostrar la transformación a CNF.
- **`doc/`** — Carpeta de documentación formal:
  - `DOCUMENTACION.md` — Reporte académico completo (Diseño y modelado, Discusión teórica de obstáculos y recomendaciones, Ejemplos y pruebas empíricas).
  - `Proyecto No 2.pdf` — Documento de especificación del proyecto.

---

## Compatibilidad de Codificación en Windows

El programa incorpora reconfiguración automática de `stdout` a UTF-8 (`sys.stdout.reconfigure(encoding='utf-8', errors='replace')`) para asegurar que caracteres tipográficos, símbolos griegos ($\epsilon$) y caracteres de caja ASCII/Unicode se visualicen correctamente en PowerShell y CMD sin arrojar errores de tipo `charmap`.
