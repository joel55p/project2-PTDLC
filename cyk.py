"""
Módulo del Algoritmo CYK (Cocke-Younger-Kasami) con Parse Tree y Programación Dinámica.
Teoría de la Computación - Proyecto 2

Implementa:
1. ParseTreeNode: estructura de datos jerárquica para el árbol de derivación sintáctico.
2. CYKParser:
   - Programación dinámica con tabla triangular.
   - Guardado de nodos para reconstrucción completa del Parse Tree.
   - Medición precisa de tiempo de ejecución (time.perf_counter).
   - Generación de veredicto (SÍ / NO).
   - Impresión tabular y formateo de la matriz dinámica.
"""

import sys
from typing import List, Dict, Set, Tuple, Optional
import time
import re
from grammar import CFG, Rule

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class ParseTreeNode:
    """Nodo del árbol de análisis sintáctico (Parse Tree)."""

    def __init__(self, symbol: str, children: Optional[List['ParseTreeNode']] = None,
                 word: Optional[str] = None, rule: Optional[Rule] = None):
        self.symbol: str = symbol
        self.children: List['ParseTreeNode'] = children or []
        self.word: Optional[str] = word  # Si es hoja, almacena el terminal
        self.rule: Optional[Rule] = rule

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def to_tree_str(self, prefix: str = "", is_last: bool = True) -> str:
        """Devuelve una representación visual en ASCII con conectores jerárquicos."""
        connector = "└── " if is_last else "├── "
        label = self.symbol
        if self.word is not None:
            label += f' ("{self.word}")'

        lines = [prefix + connector + label]

        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(self.children):
            child_is_last = (i == len(self.children) - 1)
            lines.append(child.to_tree_str(prefix=new_prefix, is_last=child_is_last))

        return "\n".join(lines)

    def to_bracketed(self) -> str:
        """Devuelve la notación por corchetes (formato Penn Treebank / LISP)."""
        if self.word is not None:
            return f"[{self.symbol} {self.word}]"
        children_str = " ".join(c.to_bracketed() for c in self.children)
        return f"[{self.symbol} {children_str}]"

    def to_dict(self) -> dict:
        """Serializa a diccionario para exportación JSON y visualización HTML."""
        data = {
            "name": self.symbol,
            "word": self.word,
        }
        if self.children:
            data["children"] = [c.to_dict() for c in self.children]
        return data

    def __repr__(self) -> str:
        if self.word:
            return f"Node({self.symbol} -> '{self.word}')"
        return f"Node({self.symbol}, children={len(self.children)})"


class CYKResult:
    """Resultado detallado de la ejecución de CYK sobre una frase."""

    def __init__(self, sentence: str, tokens: List[str], accepted: bool,
                 execution_time_ms: float, parse_trees: List[ParseTreeNode],
                 table: Dict[Tuple[int, int], Dict[str, List[ParseTreeNode]]]):
        self.sentence: str = sentence
        self.tokens: List[str] = tokens
        self.accepted: bool = accepted
        self.execution_time_ms: float = execution_time_ms
        self.parse_trees: List[ParseTreeNode] = parse_trees
        self.table: Dict[Tuple[int, int], Dict[str, List[ParseTreeNode]]] = table

    @property
    def verdict(self) -> str:
        return "SÍ" if self.accepted else "NO"

    @property
    def num_trees(self) -> int:
        return len(self.parse_trees)

    @property
    def best_tree(self) -> Optional[ParseTreeNode]:
        return self.parse_trees[0] if self.parse_trees else None


class CYKParser:
    """Implementación del analizador CYK basado en programación dinámica."""

    def __init__(self, grammar: CFG):
        # Si la gramática no está en CNF, la convertimos automáticamente
        is_cnf, _ = grammar.is_cnf()
        if not is_cnf:
            self.cnf_grammar, self.cnf_steps = grammar.to_cnf()
            self.original_grammar: Optional[CFG] = grammar
        else:
            self.cnf_grammar = grammar
            self.cnf_steps = []
            self.original_grammar = grammar

        self.start_symbol = self.cnf_grammar.start_symbol
        self._index_rules()

    def _index_rules(self):
        """Indexa las reglas para búsquedas eficientes en tiempo constante O(1)."""
        # terminal -> lista de no-terminales que lo derivan: A -> a
        self.terminal_map: Dict[str, List[Rule]] = {}
        # (B, C) -> lista de no-terminales que derivan el par: A -> B C
        self.binary_map: Dict[Tuple[str, str], List[Rule]] = {}

        for r in self.cnf_grammar.rules:
            if len(r.body) == 1:
                term = r.body[0].lower()
                self.terminal_map.setdefault(term, []).append(r)
            elif len(r.body) == 2:
                pair = (r.body[0], r.body[1])
                self.binary_map.setdefault(pair, []).append(r)

    @staticmethod
    def tokenize(sentence: str) -> List[str]:
        """
        Tokeniza una frase textual en inglés:
        - Remueve signos de puntuación periféricos (. ; , ! ?).
        - Convierte a minúsculas para compatibilidad léxica.
        """
        cleaned = re.sub(r'[;,\.!?]+', ' ', sentence.strip())
        tokens = [word.lower() for word in cleaned.split() if word]
        return tokens

    def parse(self, sentence: str) -> CYKResult:
        """
        Ejecuta el algoritmo CYK con Programación Dinámica y reconstrucción de Parse Tree.
        
        Complejidad: O(n^3 * |R|) donde n es la cantidad de palabras en la frase
        y |R| es el número de reglas de la gramática.
        """
        t0 = time.perf_counter()
        tokens = self.tokenize(sentence)
        n = len(tokens)

        # Si la frase está vacía:
        if n == 0:
            t1 = time.perf_counter()
            # La frase vacía es aceptada sólo si S -> ε existe en la gramática
            empty_rule = any(r.head == self.start_symbol and r.is_epsilon for r in self.cnf_grammar.rules)
            trees = [ParseTreeNode(self.start_symbol, word="ε")] if empty_rule else []
            return CYKResult(
                sentence=sentence,
                tokens=tokens,
                accepted=empty_rule,
                execution_time_ms=(t1 - t0) * 1000.0,
                parse_trees=trees,
                table={}
            )

        # Tabla dinámica: table[(i, l)][A] = lista de ParseTreeNode
        # i: índice de inicio (0 <= i < n)
        # l: longitud de la subcadena (1 <= l <= n - i)
        table: Dict[Tuple[int, int], Dict[str, List[ParseTreeNode]]] = {}

        # ---------------------------------------------------------
        # Caso Base: Subcadenas de longitud l = 1 (palabras individuales)
        # ---------------------------------------------------------
        for i in range(n):
            word = tokens[i]
            cell: Dict[str, List[ParseTreeNode]] = {}
            if word in self.terminal_map:
                for r in self.terminal_map[word]:
                    node = ParseTreeNode(
                        symbol=r.head,
                        children=[],
                        word=word,
                        rule=r
                    )
                    cell.setdefault(r.head, []).append(node)
            table[(i, 1)] = cell

        # ---------------------------------------------------------
        # Paso Inductivo: Subcadenas de longitud l = 2 hasta n
        # ---------------------------------------------------------
        for l in range(2, n + 1):
            for i in range(n - l + 1):
                cell: Dict[str, List[ParseTreeNode]] = {}

                # Partición de la subcadena en longitud k y (l - k)
                for k in range(1, l):
                    left_cell = table.get((i, k), {})
                    right_cell = table.get((i + k, l - k), {})

                    if not left_cell or not right_cell:
                        continue

                    # Para cada par de símbolos (B, C) producidos en las mitades
                    for b_sym, b_nodes in left_cell.items():
                        for c_sym, c_nodes in right_cell.items():
                            pair = (b_sym, c_sym)
                            if pair in self.binary_map:
                                for rule in self.binary_map[pair]:
                                    # Generar combinaciones de árboles de derivación
                                    for b_node in b_nodes:
                                        for c_node in c_nodes:
                                            tree_node = ParseTreeNode(
                                                symbol=rule.head,
                                                children=[b_node, c_node],
                                                rule=rule
                                            )
                                            cell.setdefault(rule.head, []).append(tree_node)

                table[(i, l)] = cell

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        # Verificación del símbolo inicial en la celda superior table[(0, n)]
        top_cell = table.get((0, n), {})
        accepted = self.start_symbol in top_cell
        parse_trees = top_cell.get(self.start_symbol, []) if accepted else []

        return CYKResult(
            sentence=sentence,
            tokens=tokens,
            accepted=accepted,
            execution_time_ms=elapsed_ms,
            parse_trees=parse_trees,
            table=table
        )

    @staticmethod
    def format_table_summary(result: CYKResult) -> str:
        """
        Formatea la tabla triangular de programación dinámica para la consola.
        Muestra la progresión de longitudes y los no-terminales deducidos en cada celda.
        """
        tokens = result.tokens
        n = len(tokens)
        if n == 0:
            return "Tabla vacía."

        lines = []
        lines.append(f"Palabras ({n}): " + " | ".join(f"[{i}] {w}" for i, w in enumerate(tokens)))
        lines.append("-" * 75)
        lines.append(f"{'Long':<5} {'Rango':<10} {'Subcadena':<28} {'Variables derivadas'}")
        lines.append("-" * 75)

        for l in range(1, n + 1):
            for i in range(n - l + 1):
                j = i + l - 1
                substr = " ".join(tokens[i:i + l])
                if len(substr) > 26:
                    substr = substr[:23] + "..."
                cell = result.table.get((i, l), {})
                vars_found = sorted(cell.keys())
                vars_str = "{" + ", ".join(vars_found) + "}" if vars_found else "∅"
                lines.append(f"{l:<5} [{i}..{j}]    {substr:<28} {vars_str}")
            if l < n:
                lines.append("." * 75)

        return "\n".join(lines)

    @staticmethod
    def format_triangle_matrix(result: CYKResult) -> str:
        """
        Imprime la clásica matriz triangular CYK donde:
        - Las filas representan la longitud l (de n hacia 1 o de 1 a n).
        - Las columnas representan el índice inicial i.
        """
        tokens = result.tokens
        n = len(tokens)
        if n == 0:
            return ""

        # Ancho por celda
        col_w = max(12, max((len(w) for w in tokens), default=5) + 4)

        header = f"{'l \\ i':<6}" + "".join(f"{f'i={i} ({tokens[i][:6]})':^{col_w}}" for i in range(n))
        separator = "=" * len(header)
        matrix_lines = [header, separator]

        for l in range(n, 0, -1):
            row = [f"l={l:<3}"]
            for i in range(n):
                if i + l <= n:
                    cell = result.table.get((i, l), {})
                    vars_found = sorted(cell.keys())
                    content = "{" + ",".join(vars_found) + "}" if vars_found else "∅"
                else:
                    content = ""
                row.append(f"{content:^{col_w}}")
            matrix_lines.append("".join(row))

        return "\n".join(matrix_lines)
