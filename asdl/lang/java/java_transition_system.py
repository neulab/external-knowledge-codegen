# coding=utf-8

import javalang.parse
from javalang.parser import JavaSyntaxError
from javalang import tree

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
        try:
            java_ast = javalang.parse.parse(code)
        except JavaSyntaxError as e:
            java_ast = javalang.parse.parse_member_declaration(code)
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
                assert(type(tok)!=tree.FieldReference)
                actions.append(GenTokenAction(tok))
        else:
            pass
        return actions

    def is_valid_hypothesis(self, hyp, **kwargs):
        try:
            hyp_code = self.ast_to_surface_code(hyp.tree)
            try:
                java_ast = javalang.parse.parse(hyp_code)
            except JavaSyntaxError as e:
                java_ast = javalang.parse.parse_member_declaration(hyp_code)
            self.tokenize_code(hyp_code)
        except Exception:
            return False
        return True
