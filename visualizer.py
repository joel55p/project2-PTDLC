"""
Módulo de Visualización Gráfica para el Algoritmo CYK y Parse Tree.
Genera reportes HTML interactivos y autónomos (sin dependencias externas).
Teoría de la Computación - Proyecto 2
"""

import json
from typing import Optional
from cyk import CYKResult, ParseTreeNode
from grammar import CFG


def _build_svg_tree(node: ParseTreeNode) -> str:
    """Genera un diagrama de árbol sintáctico en SVG jerárquico."""
    # Asignar coordenadas (x, y) a cada nodo
    levels = []

    def layout(curr: ParseTreeNode, depth: int):
        while len(levels) <= depth:
            levels.append([])
        curr_info = {
            "node": curr,
            "depth": depth,
            "children": [],
            "x": 0,
            "y": depth * 80 + 50
        }
        levels[depth].append(curr_info)
        for child in curr.children:
            child_info = layout(child, depth + 1)
            curr_info["children"].append(child_info)
        return curr_info

    root_info = layout(node, 0)

    # Calcular posiciones horizontales (hojas equidistantes)
    leaf_counter = [0]
    leaf_gap = 100

    def assign_leaf_x(curr_info):
        if not curr_info["children"]:
            curr_info["x"] = leaf_counter[0] * leaf_gap + 70
            leaf_counter[0] += 1
        else:
            for child in curr_info["children"]:
                assign_leaf_x(child)
            # El padre se centra sobre sus hijos
            curr_info["x"] = sum(c["x"] for c in curr_info["children"]) / len(curr_info["children"])

    assign_leaf_x(root_info)

    total_width = max(800, leaf_counter[0] * leaf_gap + 140)
    total_height = len(levels) * 80 + 90

    # Dibujar líneas y nodos
    svg_elements = []

    def draw_elements(curr_info):
        x, y = curr_info["x"], curr_info["y"]
        for child in curr_info["children"]:
            cx, cy = child["x"], child["y"]
            svg_elements.append(
                f'<path d="M {x} {y+15} C {x} {y+45}, {cx} {cy-45}, {cx} {cy-15}" '
                f'stroke="#4f46e5" stroke-width="2" fill="none" opacity="0.6"/>'
            )
            draw_elements(child)

        # Dibujar nodo
        curr_node: ParseTreeNode = curr_info["node"]
        if curr_node.is_leaf:
            # Nodo terminal
            svg_elements.append(
                f'<rect x="{x-40}" y="{y-18}" width="80" height="36" rx="6" '
                f'fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>'
            )
            svg_elements.append(
                f'<text x="{x}" y="{y+4}" font-family="system-ui, sans-serif" font-size="13" '
                f'font-weight="bold" fill="#065f46" text-anchor="middle">{curr_node.symbol}</text>'
            )
            if curr_node.word:
                svg_elements.append(
                    f'<text x="{x}" y="{y+32}" font-family="system-ui, sans-serif" font-size="12" '
                    f'font-style="italic" fill="#047857" text-anchor="middle">"{curr_node.word}"</text>'
                )
        else:
            # Nodo no terminal
            svg_elements.append(
                f'<rect x="{x-35}" y="{y-18}" width="70" height="36" rx="6" '
                f'fill="#eef2ff" stroke="#6366f1" stroke-width="2"/>'
            )
            svg_elements.append(
                f'<text x="{x}" y="{y+5}" font-family="system-ui, sans-serif" font-size="14" '
                f'font-weight="bold" fill="#3730a3" text-anchor="middle">{curr_node.symbol}</text>'
            )

    draw_elements(root_info)

    svg_content = "\n".join(svg_elements)
    return (
        f'<svg viewBox="0 0 {total_width} {total_height}" width="100%" '
        f'style="min-width: 600px; max-height: 600px; background: #ffffff; border-radius: 8px;">\n'
        f'{svg_content}\n'
        f'</svg>'
    )


def generate_html_report(result: CYKResult, grammar: CFG, output_path: str):
    """Genera un archivo HTML visualmente atractivo con la matriz CYK y el Parse Tree."""
    tokens = result.tokens
    n = len(tokens)

    # Veredicto visual
    verdict_badge = (
        '<span style="background: #10b981; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 1.1rem;">SÍ (Aceptada)</span>'
        if result.accepted else
        '<span style="background: #ef4444; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 1.1rem;">NO (Rechazada)</span>'
    )

    # Parse tree SVG
    tree_html = ""
    if result.best_tree:
        tree_svg = _build_svg_tree(result.best_tree)
        bracketed = result.best_tree.to_bracketed()
        ascii_tree = result.best_tree.to_tree_str()
        tree_html = f"""
        <div class="card">
            <h2>🌳 Árbol Sintáctico (Parse Tree)</h2>
            <p>Se encontraron <strong>{result.num_trees}</strong> árbol(es) de derivación sintáctica válidos.</p>
            <div style="overflow-x: auto; padding: 15px 0; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px;">
                {tree_svg}
            </div>
            <h3>Notación Penn Treebank / Corchetes:</h3>
            <pre class="code-box">{bracketed}</pre>
            <details style="margin-top: 15px;">
                <summary style="cursor: pointer; color: #4f46e5; font-weight: 600;">Ver Árbol en formato ASCII Textual</summary>
                <pre class="code-box" style="margin-top: 10px;">{ascii_tree}</pre>
            </details>
        </div>
        """
    else:
        tree_html = """
        <div class="card">
            <h2>🌳 Árbol Sintáctico</h2>
            <p style="color: #64748b; font-style: italic;">No se generó árbol de análisis sintáctico debido a que la frase no pertenece al lenguaje.</p>
        </div>
        """

    # Construir tabla triangular en HTML
    matrix_rows = []
    for l in range(n, 0, -1):
        cells_html = [f"<td style='background:#f1f5f9; font-weight:bold; text-align:center;'>l = {l}</td>"]
        for i in range(n):
            if i + l <= n:
                cell = result.table.get((i, l), {})
                vars_found = sorted(cell.keys())
                is_start = grammar.start_symbol in vars_found and l == n and i == 0
                cell_bg = "#ecfdf5" if is_start else ("#f8fafc" if vars_found else "#ffffff")
                border_color = "#10b981" if is_start else "#cbd5e1"
                text_color = "#047857" if is_start else "#1e293b"
                content = "{" + ", ".join(vars_found) + "}" if vars_found else "∅"
                cells_html.append(
                    f"<td style='background:{cell_bg}; border: 1px solid {border_color}; color: {text_color}; text-align:center; padding: 10px; font-weight: 600;'>"
                    f"{content}</td>"
                )
            else:
                cells_html.append("<td style='background:#f8fafc; border:none;'></td>")
        matrix_rows.append("<tr>" + "".join(cells_html) + "</tr>")

    header_cols = ["<th style='background:#0f172a; color:white; padding:10px;'>l \\ i</th>"]
    for i, w in enumerate(tokens):
        header_cols.append(f"<th style='background:#1e293b; color:white; padding:10px;'>i={i}<br><small style='color:#94a3b8;'>\"{w}\"</small></th>")
    matrix_header = "<tr>" + "".join(header_cols) + "</tr>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYK Parser — Reporte de Validación</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 30px 20px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }}
        h1 {{
            margin-top: 0;
            color: #1e1b4b;
            font-size: 1.8rem;
        }}
        h2 {{
            color: #312e81;
            margin-top: 0;
            border-bottom: 2px solid #e0e7ff;
            padding-bottom: 8px;
            font-size: 1.3rem;
        }}
        .badge-bar {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}
        .metric-pill {{
            background: #f1f5f9;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.95rem;
            color: #334155;
            font-weight: 500;
        }}
        .table-responsive {{
            overflow-x: auto;
            margin: 15px 0;
        }}
        table.matrix {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}
        table.matrix th, table.matrix td {{
            min-width: 80px;
            height: 40px;
        }}
        .code-box {{
            background: #0f172a;
            color: #f8fafc;
            padding: 16px;
            border-radius: 8px;
            font-family: Consolas, Monaco, "Courier New", monospace;
            font-size: 0.9rem;
            overflow-x: auto;
        }}
        footer {{
            text-align: center;
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Cocke-Younger-Kasami (CYK) — Reporte de Análisis Sintáctico</h1>
            <p style="font-size: 1.15rem; color: #475569; margin-bottom: 10px;">
                Expresión: <strong style="color: #0f172a;">"{result.sentence}"</strong>
            </p>
            <div class="badge-bar">
                {verdict_badge}
                <div class="metric-pill">⏱️ Tiempo de validación: <strong>{result.execution_time_ms:.4f} ms</strong> ({result.execution_time_ms * 1000:.1f} µs)</div>
                <div class="metric-pill">🔤 Longitud: <strong>{n} palabras</strong></div>
                <div class="metric-pill">🎯 Símbolo inicial: <strong>{grammar.start_symbol}</strong></div>
            </div>
        </div>

        {tree_html}

        <div class="card">
            <h2>📐 Matriz Triangular de Programación Dinámica (CYK Table)</h2>
            <p>Eje vertical: longitud de subcadena (<strong>l</strong>). Eje horizontal: índice de inicio (<strong>i</strong>). La celda superior (l={n}, i=0) determina la aceptación con el símbolo <strong>{grammar.start_symbol}</strong>.</p>
            <div class="table-responsive">
                <table class="matrix">
                    <thead>
                        {matrix_header}
                    </thead>
                    <tbody>
                        {"".join(matrix_rows)}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>📋 Gramática Utilizada (Forma Normal de Chomsky)</h2>
            <pre class="code-box">{grammar.pretty_rules()}</pre>
        </div>

        <footer>
            Teoría de la Computación — Proyecto 2 — Algoritmo CYK y Simplificación de Gramáticas
        </footer>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
