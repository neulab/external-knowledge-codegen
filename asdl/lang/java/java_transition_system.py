# coding=utf-8

import ast

from asdl.lang.java import jastor
from asdl.lang.java.java_asdl_helper import (asdl_ast_to_java_ast,
                                             java_ast_to_asdl_ast)
from asdl.lang.java.java_utils import tokenize_code
from asdl.transition_system import TransitionSystem, GenTokenAction

from common.registerable import Registrable


@Registrable.register('java')
class JavaTransitionSystem(TransitionSystem):
    def tokenize_code(self, code, mode=None):
        return tokenize_code(code, mode)

    def surface_code_to_ast(self, code):
        java_ast = ast.parse(code)
        return java_ast_to_asdl_ast(java_ast, self.grammar)

    def ast_to_surface_code(self, asdl_ast):
        java_ast = asdl_ast_to_java_ast(asdl_ast, self.grammar)
        code = jastor.to_source(java_ast).strip()

        return code

    def compare_ast(self, hyp_ast, ref_ast):
        hyp_code = self.ast_to_surface_code(hyp_ast)
        ref_reformatted_code = self.ast_to_surface_code(ref_ast)

        ref_code_tokens = tokenize_code(ref_reformatted_code)
        hyp_code_tokens = tokenize_code(hyp_code)

        return ref_code_tokens == hyp_code_tokens

    def get_primitive_field_actions(self, realized_field):
        actions = []
        if realized_field.value is not None:
            # expr -> Global(identifier* names)
            if realized_field.cardinality == 'multiple':
                field_values = realized_field.value
            else:
                field_values = [realized_field.value]

            tokens = []
            if realized_field.type.name == 'string':
                for field_val in field_values:
                    tokens.extend(field_val.split(' ') + ['</primitive>'])
            else:
                for field_val in field_values:
                    tokens.append(field_val)

            for tok in tokens:
                actions.append(GenTokenAction(tok))
        elif (realized_field.type.name == 'singleton'
              and realized_field.value is None):
            # singleton can be None
            actions.append(GenTokenAction('None'))

        return actions

    def is_valid_hypothesis(self, hyp, **kwargs):
        try:
            hyp_code = self.ast_to_surface_code(hyp.tree)
            ast.parse(hyp_code)
            self.tokenize_code(hyp_code)
        except Exception:
            return False
        return True
