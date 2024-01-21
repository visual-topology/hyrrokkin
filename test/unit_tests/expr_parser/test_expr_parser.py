
from hyrrokkin.utils.expr_parser import ExpressionParser
import unittest
import os.path
import json

class TestExprParser(unittest.TestCase):


    def setUp(self):
        folder = os.path.split(__file__)[0]
        with open(os.path.join(folder,"test_expr_parser_binary_operators.json")) as f:
            binary_ops = json.loads(f.read())["binary_operators"]
        with open(os.path.join(folder, "test_expr_parser_unary_operators.json")) as f:
            unary_ops = json.loads(f.read())["unary_operators"]

        self.ep = ExpressionParser()
        for op in unary_ops:
            self.ep.add_unary_operator(op)
        for op in binary_ops:
            precedence = binary_ops[op]
            self.ep.add_binary_operator(op,precedence)

    def run_tests(self,test_file_name, key="test_cases"):
        folder = os.path.split(__file__)[0]
        with open(os.path.join(folder,test_file_name)) as f:
            tests = json.loads(f.read())[key]
        for test_name in tests:
            print(test_name)
            self.assertEqual(tests[test_name],self.ep.parse(test_name))

    def test_basic(self):
        self.run_tests("test_expr_parser_basic.json")

    def test_listerals(self):
        self.run_tests("test_expr_parser_literals.json")

if __name__ == '__main__':
    unittest.main()