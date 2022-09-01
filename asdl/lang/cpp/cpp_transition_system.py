# coding=utf-8

import cpplang.parse
from cpplang.parser import CppSyntaxError
from cpplang import tree

from asdl.lang.cpp import cppastor
from asdl.lang.cpp.cpp_asdl_helper import (asdl_ast_to_cpp_ast,
                                             cpp_ast_to_asdl_ast)
from asdl.lang.cpp.cpp_utils import tokenize_code
from asdl.transition_system import TransitionSystem, GenTokenAction

from common.registerable import Registrable


@Registrable.register('cpp')
class CppTransitionSystem(TransitionSystem):
    def tokenize_code(self, code, mode=None):
        return tokenize_code(code, mode)

    def surface_code_to_ast(self, code):
        try:
            cpp_ast = cpplang.parse.parse(code)
        except CppSyntaxError as e:
            cpp_ast = cpplang.parse.parse_member_declaration(code)
        return cpp_ast_to_asdl_ast(cpp_ast, self.grammar)

    def ast_to_surface_code(self, asdl_ast):
        cpp_ast = asdl_ast_to_cpp_ast(asdl_ast, self.grammar)
        code = jastor.to_source(cpp_ast).strip()

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
                if isinstance(realized_field.value, tree.Node):
                    print()
                field_values = realized_field.value
            else:
                field_values = [realized_field.value]

            tokens = []
            if realized_field.type.name == 'string':
                for field_val in field_values:
                    tokens.extend(field_val.split(' ') + ['</primitive>'])
            else:
                for field_val in field_values:
                    #if type(field_val) == bool:
                        #field_val = str(field_val).lower()
                    tokens.append(field_val)

            for tok in tokens:
                assert(not isinstance(tok, tree.Node))
                assert(type(tok) == str)
                actions.append(GenTokenAction(tok))
        else:
            pass
        return actions

    def is_valid_hypothesis(self, hyp, **kwargs):
        try:
            hyp_code = self.ast_to_surface_code(hyp.tree)
            try:
                cpp_ast = cpplang.parse.parse(hyp_code)
            except CppSyntaxError as e:
                cpp_ast = cpplang.parse.parse_member_declaration(hyp_code)
            self.tokenize_code(hyp_code)
        except Exception:
            return False
        return True
