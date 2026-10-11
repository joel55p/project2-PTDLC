"""
Módulo de Gramáticas Libres de Contexto (CFG) y Simplificación a Forma Normal de Chomsky (CNF).
Teoría de la Computación - Proyecto 2
Cocke-Younger-Kasami (CYK) Parser

Implementa:
1. Representación de Reglas y Gramática Libre de Contexto (CFG).
2. Algoritmo de Simplificación y Conversión a CNF:
   - Paso 0: Normalización del símbolo inicial.
   - Paso 1: Eliminación de producciones épsilon (ε / nullable).
   - Paso 2: Eliminación de producciones unitarias (A -> B).
   - Paso 3: Eliminación de símbolos inútiles (no generadores e inalcanzables).
   - Paso 4: Binarización de reglas largas y aislamiento de terminales.
"""

import sys
from typing import List, Tuple, Set, Dict, Optional
import copy

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


EPSILON_SYMBOLS = {'ε', 'epsilon', 'eps', 'EPS', "''", '""'}


class Rule:
    """Representa una regla de producción A -> X1 X2 ... Xn."""
    def __init__(self, head: str, body: Tuple[str, ...]):
        self.head: str = head
        # Si el cuerpo es una tupla vacía o contiene un símbolo épsilon, se normaliza
        if len(body) == 1 and body[0] in EPSILON_SYMBOLS:
            self.body: Tuple[str, ...] = ()
        else:
            self.body: Tuple[str, ...] = tuple(body)

    @property
    def is_epsilon(self) -> bool:
        return len(self.body) == 0

    def is_unit(self, variables: Set[str]) -> bool:
        return len(self.body) == 1 and self.body[0] in variables

    def __repr__(self) -> str:
        if self.is_epsilon:
            return f"{self.head} -> ε"
        return f"{self.head} -> {' '.join(self.body)}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Rule):
            return False
        return self.head == other.head and self.body == other.body

    def __hash__(self) -> int:
        return hash((self.head, self.body))


class CFG:
    """Representa una Gramática Libre de Contexto (V, Sigma, R, S)."""

    def __init__(self, variables: Set[str], terminals: Set[str],
                 rules: List[Rule], start_symbol: str):
        self.variables: Set[str] = set(variables)
        self.terminals: Set[str] = set(terminals)
        self.rules: List[Rule] = list(rules)
        self.start_symbol: str = start_symbol

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_rules = []
        for r in self.rules:
            if r not in seen:
                seen.add(r)
                unique_rules.append(r)
        self.rules = unique_rules

    @classmethod
    def from_string(cls, text: str, default_start: Optional[str] = None) -> 'CFG':
        """
        Crea una CFG a partir de una cadena multilínea con formato:
        A -> B C | d
        """
        raw_rules: List[Rule] = []
        lhs_set: Set[str] = set()
        first_lhs: Optional[str] = None

        lines = text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '->' in line:
                sep = '->'
            elif '::=' in line:
                sep = '::='
            elif '→' in line:
                sep = '→'
            else:
                continue

            head_part, body_part = line.split(sep, 1)
            head = head_part.strip()
            if not head:
                continue

            if first_lhs is None:
                first_lhs = head
            lhs_set.add(head)

            # Las alternativas se separan por '|'
            alternatives = body_part.split('|')
            for alt in alternatives:
                tokens = tuple(alt.strip().split())
                raw_rules.append(Rule(head, tokens))

        start_symbol = default_start if default_start else (first_lhs if first_lhs else 'S')

        # Variables: todos los símbolos en el lado izquierdo (LHS)
        variables = set(lhs_set)

        # Terminales: todos los símbolos en el lado derecho que no están en LHS y no son épsilon
        terminals = set()
        for r in raw_rules:
            for symbol in r.body:
                if symbol not in variables and symbol not in EPSILON_SYMBOLS:
                    terminals.add(symbol)

        return cls(variables, terminals, raw_rules, start_symbol)

    @classmethod
    def from_file(cls, filepath: str, default_start: Optional[str] = None) -> 'CFG':
        """Lee una CFG desde un archivo de texto con codificación UTF-8."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls.from_string(content, default_start=default_start)

    def is_cnf(self) -> Tuple[bool, List[Rule]]:
        """
        Verifica si la gramática está en Forma Normal de Chomsky (CNF).
        Una regla está en CNF si:
        - A -> B C  donde B, C pertenecen a Variables
        - A -> a    donde a pertenece a Terminales
        - S -> ε    (sólo si S es el símbolo inicial y no aparece a la derecha)
        """
        non_cnf_rules: List[Rule] = []
        for r in self.rules:
            if r.is_epsilon:
                if r.head == self.start_symbol:
                    # Verificar si el símbolo inicial aparece a la derecha de alguna regla
                    if any(self.start_symbol in other.body for other in self.rules):
                        non_cnf_rules.append(r)
                else:
                    non_cnf_rules.append(r)
            elif len(r.body) == 1:
                # Debe ser un único terminal
                symbol = r.body[0]
                if symbol in self.variables:
                    non_cnf_rules.append(r)  # Regla unitaria
            elif len(r.body) == 2:
                # Deben ser dos variables
                b, c = r.body[0], r.body[1]
                if b not in self.variables or c not in self.variables:
                    non_cnf_rules.append(r)
            else:
                # Longitud > 2
                non_cnf_rules.append(r)

        return len(non_cnf_rules) == 0, non_cnf_rules

    # -------------------------------------------------------------
    # Algoritmo de Simplificación y Conversión a CNF
    # -------------------------------------------------------------

    def _step_0_start_symbol(self) -> Tuple['CFG', str]:
        """
        Paso 0: Si el símbolo inicial aparece en el lado derecho de alguna regla,
        se introduce un nuevo símbolo inicial S0 -> S.
        """
        appears_on_rhs = any(self.start_symbol in r.body for r in self.rules)
        if not appears_on_rhs:
            return self.copy(), "El símbolo inicial no aparece en el lado derecho; no es necesario agregar S0."

        new_start = f"{self.start_symbol}_0"
        # Asegurar que el nombre sea único
        idx = 0
        while new_start in self.variables:
            idx += 1
            new_start = f"{self.start_symbol}_{idx}"

        new_variables = set(self.variables)
        new_variables.add(new_start)

        new_rules = [Rule(new_start, (self.start_symbol,))] + list(self.rules)
        explanation = f"Se introdujo un nuevo símbolo inicial '{new_start}' con la regla: {new_start} -> {self.start_symbol}"

        return CFG(new_variables, self.terminals, new_rules, new_start), explanation

    def _step_1_eliminate_epsilon(self) -> Tuple['CFG', str]:
        """
        Paso 1: Eliminación de producciones épsilon (A -> ε).
        1. Hallar variables anulables (nullable).
        2. Para cada regla, generar combinaciones omitiendo variables anulables.
        3. Remover reglas A -> ε (excepto posiblemente Start -> ε).
        """
        # 1. Variables anulables
        nullable: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for r in self.rules:
                if r.head in nullable:
                    continue
                if r.is_epsilon:
                    nullable.add(r.head)
                    changed = True
                elif all(sym in nullable for sym in r.body):
                    nullable.add(r.head)
                    changed = True

        if not nullable:
            return self.copy(), "No existen producciones épsilon ni variables anulables."

        # 2. Generar nuevas reglas expandiendo las combinaciones de anulables
        new_rules_set: Set[Rule] = set()

        def expand_rule(head: str, body: Tuple[str, ...], idx: int, current: List[str]):
            if idx == len(body):
                if current:  # No agregar regla vacía aquí
                    new_rules_set.add(Rule(head, tuple(current)))
                return

            sym = body[idx]
            # Opción 1: incluir el símbolo
            expand_rule(head, body, idx + 1, current + [sym])

            # Opción 2: si es anulable, podemos omitirlo
            if sym in nullable:
                expand_rule(head, body, idx + 1, current)

        for r in self.rules:
            if not r.is_epsilon:
                expand_rule(r.head, r.body, 0, [])

        # Si el símbolo inicial es anulable, la palabra vacía pertenece al lenguaje
        if self.start_symbol in nullable:
            new_rules_set.add(Rule(self.start_symbol, ()))

        new_rules = list(new_rules_set)
        explanation = (f"Variables anulables encontradas: {', '.join(sorted(nullable)) or 'ninguna'}.\n"
                       f"Se expandieron las reglas omitiendo variables anulables y se eliminaron las reglas ε.")

        return CFG(self.variables, self.terminals, new_rules, self.start_symbol), explanation

    def _step_2_eliminate_unit_rules(self) -> Tuple['CFG', str]:
        """
        Paso 2: Eliminación de producciones unitarias (A -> B donde B es no-terminal).
        Calcula la clausura de pares unitarios (A =>* B) y transfiere las producciones no unitarias.
        """
        # 1. Hallar clausura unitaria para cada variable
        unit_closure: Dict[str, Set[str]] = {v: {v} for v in self.variables}
        changed = True
        while changed:
            changed = False
            for r in self.rules:
                if r.is_unit(self.variables):
                    a, b = r.head, r.body[0]
                    # Si b está en unit_closure de alguna variable o a puede alcanzar lo que b alcanza
                    before_size = len(unit_closure[a])
                    unit_closure[a].update(unit_closure.get(b, set()))
                    if len(unit_closure[a]) > before_size:
                        changed = True

        # Reglas no unitarias agrupadas por cabeza
        non_unit_rules: Dict[str, List[Rule]] = {v: [] for v in self.variables}
        has_units = False
        for r in self.rules:
            if r.is_unit(self.variables):
                has_units = True
            else:
                non_unit_rules.setdefault(r.head, []).append(r)

        if not has_units:
            return self.copy(), "No existen producciones unitarias (A -> B)."

        new_rules_set: Set[Rule] = set()
        for a in self.variables:
            for b in unit_closure.get(a, {a}):
                for r in non_unit_rules.get(b, []):
                    new_rules_set.add(Rule(a, r.body))

        new_rules = list(new_rules_set)
        explanation = "Se eliminaron todas las producciones unitarias sustituyendo sus clausuras de derivación."
        return CFG(self.variables, self.terminals, new_rules, self.start_symbol), explanation

    def _step_3_eliminate_useless_symbols(self) -> Tuple['CFG', str]:
        """
        Paso 3: Eliminación de símbolos inútiles.
        Subpaso 3a: Eliminar símbolos no generadores (que no derivan cadenas de terminales).
        Subpaso 3b: Eliminar símbolos inalcanzables (que no se pueden derivar desde el símbolo inicial).
        """
        # --- 3a: Símbolos generadores ---
        generating: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for r in self.rules:
                if r.head in generating:
                    continue
                # Si todos los símbolos del cuerpo son terminales o variables ya generadoras
                if all(sym in self.terminals or sym in generating for sym in r.body):
                    generating.add(r.head)
                    changed = True

        # Filtrar reglas que sólo contengan símbolos generadores
        gen_rules = [
            r for r in self.rules
            if r.head in generating and all(sym in self.terminals or sym in generating for sym in r.body)
        ]
        gen_vars = self.variables.intersection(generating)

        # Si el símbolo inicial no es generador, el lenguaje es vacío
        if self.start_symbol not in gen_vars:
            gen_vars = {self.start_symbol}
            gen_rules = []

        # --- 3b: Símbolos alcanzables ---
        reachable_vars: Set[str] = {self.start_symbol}
        reachable_terms: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for r in gen_rules:
                if r.head in reachable_vars:
                    for sym in r.body:
                        if sym in gen_vars:
                            if sym not in reachable_vars:
                                reachable_vars.add(sym)
                                changed = True
                        elif sym in self.terminals:
                            if sym not in reachable_terms:
                                reachable_terms.add(sym)
                                changed = True

        final_rules = [
            r for r in gen_rules
            if r.head in reachable_vars and all(sym in reachable_vars or sym in reachable_terms for sym in r.body)
        ]

        removed_vars = self.variables - reachable_vars
        explanation = (f"Eliminación de símbolos inútiles:\n"
                       f"- Símbolos generadores conservados: {len(gen_vars)} de {len(self.variables)}\n"
                       f"- Símbolos alcanzables conservados: {len(reachable_vars)} variables y {len(reachable_terms)} terminales.\n"
                       f"- Variables eliminadas: {', '.join(sorted(removed_vars)) or 'ninguna'}.")

        return CFG(reachable_vars, reachable_terms, final_rules, self.start_symbol), explanation

    def _step_4_cnf_binarize_and_terminals(self) -> Tuple['CFG', str]:
        """
        Paso 4: Conversión a Forma Normal de Chomsky.
        1. Para cuerpos de longitud >= 2, reemplazar cada terminal 'a' por una nueva variable T_a y regla T_a -> a.
        2. Para cuerpos de longitud > 2, descomponer en pares binarios con variables auxiliares.
        """
        current_vars = set(self.variables)
        current_terms = set(self.terminals)
        new_rules: List[Rule] = []

        # Mapa de terminal -> variable sustituta
        terminal_vars: Dict[str, str] = {}

        # 1. Identificar terminales en cuerpos de longitud >= 2
        for r in self.rules:
            if len(r.body) >= 2:
                for sym in r.body:
                    if sym in current_terms and sym not in terminal_vars:
                        # Generar un nombre único de variable
                        var_name = f"T_{sym.upper()}"
                        counter = 1
                        while var_name in current_vars:
                            var_name = f"T_{sym.upper()}_{counter}"
                            counter += 1
                        terminal_vars[sym] = var_name
                        current_vars.add(var_name)
                        new_rules.append(Rule(var_name, (sym,)))

        # 2. Reemplazar terminales en cuerpos de longitud >= 2
        intermediate_rules: List[Rule] = []
        for r in self.rules:
            if len(r.body) >= 2:
                new_body = tuple(terminal_vars.get(sym, sym) for sym in r.body)
                intermediate_rules.append(Rule(r.head, new_body))
            else:
                intermediate_rules.append(r)

        # 3. Binarizar cuerpos de longitud > 2
        binarized_rules: List[Rule] = list(new_rules)  # Incluye las reglas T_a -> a
        bin_counter = 1

        for r in intermediate_rules:
            if len(r.body) <= 2:
                binarized_rules.append(r)
            else:
                # Regla de longitud k > 2: A -> B1 B2 ... Bk
                # A -> B1 X1
                # X1 -> B2 X2 ...
                k = len(r.body)
                prev_head = r.head
                for i in range(k - 2):
                    aux_var = f"BIN_{prev_head}_{bin_counter}"
                    while aux_var in current_vars:
                        bin_counter += 1
                        aux_var = f"BIN_{prev_head}_{bin_counter}"
                    bin_counter += 1
                    current_vars.add(aux_var)

                    binarized_rules.append(Rule(prev_head, (r.body[i], aux_var)))
                    prev_head = aux_var

                # Última regla binaria: X_{k-2} -> B_{k-1} B_k
                binarized_rules.append(Rule(prev_head, (r.body[k - 2], r.body[k - 1])))

        explanation = (f"Binarización y reemplazo de terminales:\n"
                       f"- Se crearon {len(terminal_vars)} variables auxiliares para terminales en cuerpos mixtos.\n"
                       f"- Se descompusieron reglas de longitud > 2 en cascadas binarias.")

        return CFG(current_vars, current_terms, binarized_rules, self.start_symbol), explanation

    def to_cnf(self) -> Tuple['CFG', List[Tuple[str, 'CFG', str]]]:
        """
        Ejecuta la secuencia completa de simplificación y conversión a CNF.
        Devuelve:
            (gramática_en_cnf, lista_de_pasos)
            donde cada paso es una tupla: (nombre_del_paso, gramática_resultante, descripción)
        """
        steps: List[Tuple[str, 'CFG', str]] = []

        # Paso 0: Símbolo inicial
        g0, exp0 = self._step_0_start_symbol()
        steps.append(("Paso 0: Normalización del símbolo inicial", g0, exp0))

        # Paso 1: Eliminar épsilon
        g1, exp1 = g0._step_1_eliminate_epsilon()
        steps.append(("Paso 1: Eliminación de producciones épsilon (ε)", g1, exp1))

        # Paso 2: Eliminar producciones unitarias
        g2, exp2 = g1._step_2_eliminate_unit_rules()
        steps.append(("Paso 2: Eliminación de producciones unitarias", g2, exp2))

        # Paso 3: Eliminar símbolos inútiles
        g3, exp3 = g2._step_3_eliminate_useless_symbols()
        steps.append(("Paso 3: Eliminación de símbolos inútiles", g3, exp3))

        # Paso 4: Binarizar y aislar terminales
        g4, exp4 = g3._step_4_cnf_binarize_and_terminals()
        steps.append(("Paso 4: Conversión final a Forma Normal de Chomsky", g4, exp4))

        return g4, steps

    def copy(self) -> 'CFG':
        return CFG(set(self.variables), set(self.terminals), list(self.rules), self.start_symbol)

    def pretty_rules(self) -> str:
        """Agrupa las reglas por cabeza para una lectura limpia y agradable."""
        grouped: Dict[str, List[str]] = {}
        for r in self.rules:
            body_str = 'ε' if r.is_epsilon else ' '.join(r.body)
            grouped.setdefault(r.head, []).append(body_str)

        lines = []
        # Mostrar primero el símbolo inicial
        if self.start_symbol in grouped:
            bodies = ' | '.join(grouped[self.start_symbol])
            lines.append(f"{self.start_symbol} -> {bodies}")

        for head in sorted(grouped.keys()):
            if head == self.start_symbol:
                continue
            bodies = ' | '.join(grouped[head])
            lines.append(f"{head} -> {bodies}")

        return '\n'.join(lines)

    def __str__(self) -> str:
        return self.pretty_rules()
