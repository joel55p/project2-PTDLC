"""
Suite de Pruebas Unitarias Automatizadas para CYK y Simplificación de Gramáticas.
Teoría de la Computación - Proyecto 2
"""

import unittest
from grammar import CFG, Rule
from cyk import CYKParser, ParseTreeNode


class TestGrammarAndCNF(unittest.TestCase):
    """Pruebas para la manipulación de CFG y conversión a Forma Normal de Chomsky."""

    def test_english_grammar_already_cnf(self):
        cfg = CFG.from_file("gramatica_ingles.txt")
        is_cnf, invalid_rules = cfg.is_cnf()
        self.assertTrue(is_cnf, f"La gramática del Proyecto 2 debe cumplir CNF. Inválidas: {invalid_rules}")

    def test_epsilon_elimination(self):
        text = """
        S -> A b
        A -> a A | epsilon
        """
        cfg = CFG.from_string(text)
        cnf, steps = cfg.to_cnf()
        is_cnf, _ = cnf.is_cnf()
        self.assertTrue(is_cnf)
        self.assertFalse(any(r.head == 'A' and r.is_epsilon for r in cnf.rules))

    def test_unit_rules_elimination(self):
        text = """
        S -> A
        A -> B
        B -> b
        """
        cfg = CFG.from_string(text)
        cnf, steps = cfg.to_cnf()
        is_cnf, _ = cnf.is_cnf()
        self.assertTrue(is_cnf)
        self.assertTrue(any(r.head == cnf.start_symbol and r.body == ('b',) for r in cnf.rules))

    def test_useless_symbols_elimination(self):
        text = """
        S -> a | U
        U -> U a
        Z -> b
        """
        cfg = CFG.from_string(text)
        cnf, steps = cfg.to_cnf()
        self.assertNotIn('U', cnf.variables)
        self.assertNotIn('Z', cnf.variables)

    def test_long_body_binarization(self):
        text = """
        S -> a b c d
        """
        cfg = CFG.from_string(text)
        cnf, steps = cfg.to_cnf()
        is_cnf, _ = cnf.is_cnf()
        self.assertTrue(is_cnf)
        for r in cnf.rules:
            self.assertLessEqual(len(r.body), 2)


class TestCYKAlgorithm(unittest.TestCase):
    """Pruebas para el algoritmo CYK con la gramática en inglés del Proyecto 2."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = CFG.from_file("gramatica_ingles.txt")
        cls.parser = CYKParser(cls.cfg)

    def test_pdf_phrase_1_she_eats_a_cake_with_a_fork(self):
        sentence = "She eats a cake with a fork"
        result = self.parser.parse(sentence)
        self.assertTrue(result.accepted, f"La frase '{sentence}' debe ser aceptada (SÍ)")
        self.assertGreater(result.num_trees, 0)
        self.assertEqual(result.best_tree.symbol, 'S')
        self.assertGreater(result.execution_time_ms, 0)

    def test_pdf_phrase_2_the_cat_drinks_the_beer(self):
        sentence = "The cat drinks the beer"
        result = self.parser.parse(sentence)
        self.assertTrue(result.accepted, f"La frase '{sentence}' debe ser aceptada (SÍ)")
        self.assertGreater(result.num_trees, 0)
        self.assertEqual(result.best_tree.symbol, 'S')

    def test_valid_variations(self):
        valid_sentences = [
            "He cuts the meat with a knife",
            "A dog drinks the beer",
            "She cooks the soup in the oven",
            "He drinks the juice with a spoon",
            "The dog eats a cake",
            "She eats the meat with a fork",
            "The cat drinks a juice",
            "He drinks in the oven",
            "She eats with a fork",
            "She eats",
            "He cooks",
        ]
        for s in valid_sentences:
            res = self.parser.parse(s)
            self.assertTrue(res.accepted, f"'{s}' debería ser aceptada (SÍ)")

    def test_invalid_sentences_rejected(self):
        invalid_sentences = [
            "He cuts meat with a knife",  # falta determinante 'the' o 'a'
            "Cat drinks the beer",        # falta determinante antes de Cat
            "She eats beer the fork",     # orden inválido
            "The drinks cake cat",        # orden inválido
            "He cuts with in fork",       # preposiciones sin sustantivo
            "The dog sleeps in the oven", # palabra no perteneciente a la gramática
            "A banana drinks the tea",    # palabras fuera de la gramática
            "Cake eats a dog",            # sustantivo sin determinante
            "drinks the beer",            # falta sujeto
            "She with a fork eats cake",  # orden inválido
        ]
        for s in invalid_sentences:
            res = self.parser.parse(s)
            self.assertFalse(res.accepted, f"'{s}' debería ser rechazada (NO)")

    def test_parse_tree_structure(self):
        res = self.parser.parse("The cat drinks the beer")
        tree = res.best_tree
        self.assertIsNotNone(tree)
        self.assertEqual(tree.symbol, 'S')
        self.assertEqual(len(tree.children), 2)
        left, right = tree.children[0], tree.children[1]
        self.assertEqual(left.symbol, 'NP')
        self.assertEqual(right.symbol, 'VP')

        bracketed = tree.to_bracketed()
        self.assertTrue(bracketed.startswith("[S [NP"))


if __name__ == "__main__":
    unittest.main()
