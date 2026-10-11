"""
Aplicación Principal e Interfaz de Consola: Algoritmo CYK y Simplificación a CNF.
Teoría de la Computación - Proyecto 2

Diseñado con el mismo patrón de menús interactivos, lectura de archivos
y trazas tabulares de shuntingyard.py y Balanceo.py.
"""

import os
import sys

# Asegurar codificación UTF-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from typing import Optional
from grammar import CFG
from cyk import CYKParser, CYKResult
from visualizer import generate_html_report


DEFAULT_GRAMMAR_FILE = "gramatica_ingles.txt"
DEFAULT_PHRASES_FILE = "frases.txt"


def pedir_archivo(prompt: str, default: str) -> str:
    """Solicita el nombre del archivo al usuario con valor por defecto y autoextensión .txt."""
    entrada = input(f"{prompt} [por defecto '{default}']: ").strip()
    if not entrada:
        filename = default
    else:
        filename = entrada

    if not filename.lower().endswith('.txt'):
        filename += '.txt'
    return filename


def mostrar_pasos_cnf(grammar_file: str):
    """Muestra el proceso paso a paso de conversión de una CFG a Forma Normal de Chomsky."""
    try:
        cfg = CFG.from_file(grammar_file)
    except FileNotFoundError:
        print(f"\n[Error 404] El archivo '{grammar_file}' no existe.")
        return

    print("\n" + "=" * 70)
    print("  SIMPLIFICACIÓN Y CONVERSIÓN A FORMA NORMAL DE CHOMSKY (CNF)")
    print("=" * 70)
    print(f"Gramática leída desde: {grammar_file}")
    print(f"Símbolo inicial: {cfg.start_symbol}")
    print(f"Variables iniciales ({len(cfg.variables)}): {', '.join(sorted(cfg.variables))}")
    print(f"Terminales iniciales ({len(cfg.terminals)}): {', '.join(sorted(cfg.terminals))}")
    print("\n--- Reglas Originales ---")
    print(cfg.pretty_rules())

    is_already_cnf, invalid_rules = cfg.is_cnf()
    print("\n--- Evaluación de CNF previa ---")
    if is_already_cnf:
        print(">> La gramática YA cumple con la Forma Normal de Chomsky.")
    else:
        print(f">> La gramática NO está en CNF. Reglas a transformar ({len(invalid_rules)}):")
        for r in invalid_rules:
            print(f"   * {r}")

    print("\n--- Ejecutando algoritmo de transformación paso a paso ---")
    cnf_final, steps = cfg.to_cnf()

    for idx, (step_name, step_cfg, exp) in enumerate(steps, 1):
        print(f"\n[{step_name}]")
        print(exp)
        print("Reglas resultantes:")
        for line in step_cfg.pretty_rules().splitlines():
            print(f"  {line}")

    print("\n" + "=" * 70)
    print("  GRAMÁTICA FINAL EN FORMA NORMAL DE CHOMSKY (CNF)")
    print("=" * 70)
    print(cnf_final.pretty_rules())
    is_valid, _ = cnf_final.is_cnf()
    print(f"\n>> Verificación de conformidad CNF: {'EXITOSA (100% CNF)' if is_valid else 'FALLIDA'}")
    print("=" * 70 + "\n")


def procesar_archivo_resumen(parser: CYKParser, phrases_file: str):
    """Valida un lote de frases desde un archivo de texto en modo resumen con tabla de tiempos."""
    try:
        with open(phrases_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        print(f"\n[Error 404] El archivo '{phrases_file}' no existe.")
        return

    if not lines:
        print(f"\nEl archivo '{phrases_file}' no contiene frases para procesar.")
        return

    print("\n" + "=" * 80)
    print(f"  VALIDACIÓN DE FRASES: {phrases_file} (Modo Resumen)")
    print("=" * 80)
    print(f"{'#':>3}  {'Veredicto':<10} {'Tiempo':<14} {'Palabras':<10} Frase")
    print("-" * 80)

    total_time = 0.0
    accepted_count = 0

    for idx, line in enumerate(lines, 1):
        result = parser.parse(line)
        total_time += result.execution_time_ms
        if result.accepted:
            accepted_count += 1

        tiempo_str = f"{result.execution_time_ms:.4f} ms"
        veredicto_str = f"SÍ [ACEPT]" if result.accepted else f"NO  [RECH]"
        print(f"{idx:>3}  {veredicto_str:<10} {tiempo_str:<14} {len(result.tokens):<10} \"{line}\"")

    print("-" * 80)
    promedio_ms = total_time / len(lines) if lines else 0.0
    print(f">> Total procesadas: {len(lines)} | Aceptadas (SÍ): {accepted_count} | Rechazadas (NO): {len(lines) - accepted_count}")
    print(f">> Tiempo total: {total_time:.4f} ms | Tiempo promedio por frase: {promedio_ms:.4f} ms")
    print("=" * 80 + "\n")


def procesar_archivo_paso_a_paso(parser: CYKParser, phrases_file: str):
    """Valida frases mostrando para cada una la tabla triangular CYK completa y el Parse Tree."""
    try:
        with open(phrases_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        print(f"\n[Error 404] El archivo '{phrases_file}' no existe.")
        return

    if not lines:
        print(f"\nEl archivo '{phrases_file}' no contiene frases para procesar.")
        return

    print("\n" + "=" * 80)
    print(f"  VALIDACIÓN PASO A PASO CON TABLA DINÁMICA CYK Y PARSE TREE")
    print("=" * 80)

    for idx, line in enumerate(lines, 1):
        print(f"\n[{idx}/{len(lines)}] Procesando: \"{line}\"")
        result = parser.parse(line)

        print("\n--- Tabla de Programación Dinámica (CYK) ---")
        print(CYKParser.format_table_summary(result))

        print("\n--- Matriz Triangular Visual ---")
        print(CYKParser.format_triangle_matrix(result))

        print("\n--- Resultado de Validación ---")
        print(f">> Pertenece al lenguaje: {result.verdict}")
        print(f">> Tiempo de ejecución:   {result.execution_time_ms:.4f} ms ({result.execution_time_ms * 1000:.2f} µs)")

        if result.accepted:
            print(f">> Árboles sintácticos encontrados: {result.num_trees}")
            print("\n--- Parse Tree (Árbol Sintáctico Jerárquico) ---")
            print(result.best_tree.to_tree_str())
            print(f"\n--- Notación de Corchetes ---")
            print(result.best_tree.to_bracketed())
        else:
            print(">> No se puede construir el Parse Tree porque la frase NO es generada por la gramática.")

        print("=" * 80)


def procesar_frase_individual(parser: CYKParser, sentence: str):
    """Procesa una única frase ingresada interactivamente."""
    result = parser.parse(sentence)

    print("\n" + "=" * 75)
    print(f"  ANÁLISIS DE LA FRASE: \"{sentence}\"")
    print("=" * 75)
    print(f">> Tokens identificados ({len(result.tokens)}): {result.tokens}")
    print(f">> ¿Pertenece al lenguaje?: {result.verdict}")
    print(f">> Tiempo empleado:         {result.execution_time_ms:.4f} ms ({result.execution_time_ms * 1000:.2f} µs)")

    print("\n--- Matriz Triangular CYK ---")
    print(CYKParser.format_triangle_matrix(result))

    if result.accepted:
        print(f"\n--- Parse Tree ({result.num_trees} derivación/es válida/s) ---")
        print(result.best_tree.to_tree_str())
        print(f"\nNotación de corchetes: {result.best_tree.to_bracketed()}")
    else:
        print("\n>> La frase NO es válida sintácticamente según la gramática.")
    print("=" * 75 + "\n")
    return result


def main():
    print("""
========================================================================
     TEORÍA DE LA COMPUTACIÓN 2024 — PROYECTO 2
     ALGORITMO COCK-YOUNGER-KASAMI (CYK) Y FORMA NORMAL DE CHOMSKY
========================================================================
    """)

    # Cargar gramática por defecto del Proyecto 2
    grammar_file = DEFAULT_GRAMMAR_FILE
    if not os.path.exists(grammar_file):
        # Intentar buscar en la carpeta actual
        print(f"Aviso: '{grammar_file}' no encontrado en el directorio de ejecución actual.")

    try:
        cfg = CFG.from_file(grammar_file)
        parser = CYKParser(cfg)
        print(f"✓ Gramática cargada exitosamente: '{grammar_file}' (Símbolo inicial: {parser.start_symbol})")
    except Exception as e:
        print(f"Error al cargar '{grammar_file}': {e}")
        cfg = None
        parser = None

    last_result: Optional[CYKResult] = None

    while True:
        print("\n" + "=" * 55)
        print("                  MENÚ PRINCIPAL")
        print("=" * 55)
        print("1. Cargar y simplificar gramática a CNF (Paso a paso)")
        print("2. Validar frases desde archivo (Modo Resumen)")
        print("3. Validar frases desde archivo paso a paso (Tabla CYK + Árbol)")
        print("4. Ingresar frase manualmente por teclado")
        print("5. Generar reporte HTML/SVG interactivo de una frase")
        print("6. Cambiar archivo de gramática activa")
        print("7. Salir")
        print("=" * 55)

        opcion = input("Seleccione una opción (1-7): ").strip()

        if opcion == '1':
            g_file = pedir_archivo("Ingrese nombre de archivo de la gramática", grammar_file)
            mostrar_pasos_cnf(g_file)

        elif opcion == '2':
            if parser is None:
                print("Por favor cargue una gramática válida primero.")
                continue
            p_file = pedir_archivo("Ingrese nombre de archivo de frases", DEFAULT_PHRASES_FILE)
            procesar_archivo_resumen(parser, p_file)

        elif opcion == '3':
            if parser is None:
                print("Por favor cargue una gramática válida primero.")
                continue
            p_file = pedir_archivo("Ingrese nombre de archivo de frases", DEFAULT_PHRASES_FILE)
            procesar_archivo_paso_a_paso(parser, p_file)

        elif opcion == '4':
            if parser is None:
                print("Por favor cargue una gramática válida primero.")
                continue
            frase = input("\nIngrese la expresión/frase en inglés (ej: She eats a cake with a fork): ").strip()
            if frase:
                last_result = procesar_frase_individual(parser, frase)
            else:
                print("Frase vacía no ingresada.")

        elif opcion == '5':
            if parser is None:
                print("Por favor cargue una gramática válida primero.")
                continue
            if last_result is None:
                frase = input("Ingrese la frase para generar el reporte HTML: ").strip()
                if not frase:
                    frase = "She eats a cake with a fork"
                last_result = parser.parse(frase)

            out_html = "reporte_cyk.html"
            generate_html_report(last_result, parser.cnf_grammar, out_html)
            abs_path = os.path.abspath(out_html)
            print(f"\n✓ Reporte visual generado exitosamente en:")
            print(f"  {abs_path}")
            print(f"  (Puede abrirlo directamente en cualquier navegador web)")

        elif opcion == '6':
            g_file = pedir_archivo("Ingrese nombre de archivo de la nueva gramática", grammar_file)
            try:
                new_cfg = CFG.from_file(g_file)
                parser = CYKParser(new_cfg)
                grammar_file = g_file
                cfg = new_cfg
                print(f"✓ Gramática cambiada a '{grammar_file}' exitosamente.")
            except Exception as e:
                print(f"Error al cargar gramática: {e}")

        elif opcion == '7':
            print("\nSaliendo del programa CYK. ¡Hasta luego!\n")
            break

        else:
            print("Opción inválida. Por favor, seleccione un número entre 1 y 7.")


if __name__ == "__main__":
    main()
