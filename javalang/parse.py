import sys

from .parser import Parser
from .tokenizer import tokenize


def parse_expression(exp):
    if not exp.endswith(';'):
        exp = exp + ';'

    tokens = tokenize(exp)
    parser = Parser(tokens)

    return parser.parse_expression()


def parse_member_signature(sig):
    if not sig.endswith(';'):
        sig = sig + ';'

    tokens = tokenize(sig)
    parser = Parser(tokens)

    return parser.parse_member_declaration()


def parse_constructor_signature(sig):
    # Add an empty body to the signature, replacing a ; if necessary
    if sig.endswith(';'):
        sig = sig[:-1]
    sig = sig + '{ }'

    tokens = tokenize(sig)
    parser = Parser(tokens)

    return parser.parse_member_declaration()


def parse_type(s):
    tokens = tokenize(s)
    parser = Parser(tokens)

    return parser.parse_type()


def parse_type_signature(sig):
    if sig.endswith(';'):
        sig = sig[:-1]
    sig = sig + '{ }'

    tokens = tokenize(sig)
    parser = Parser(tokens)

    return parser.parse_class_or_interface_declaration()


def parse(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse()


def parse_method_or_field_declaraction(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_method_or_field_declaraction()


def parse_member_declaration(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_member_declaration()


def parse_array_dimension(s):
    tokens = tokenize(s)
    parser = Parser(tokens)
    return parser.parse_array_dimension()


def parse_any(code):
    tokens = tokenize(code)
    parser = Parser(tokens)
    #functions = [
      #parser.parse_identifier,
      #parser.parse_qualified_identifier,
      #parser.parse_qualified_identifier_list,
      #parser.parse_compilation_unit,
      #parser.parse_import_declaration,
      #parser.parse_type_declaration,
      #parser.parse_class_or_interface_declaration,
      #parser.parse_normal_class_declaration,
      #parser.parse_enum_declaration,
      #parser.parse_normal_interface_declaration,
      #parser.parse_annotation_type_declaration,
      #parser.parse_type,
      #parser.parse_basic_type,
      #parser.parse_reference_type,
      #parser.parse_type_arguments,
      #parser.parse_type_argument,
      #parser.parse_nonwildcard_type_arguments,
      #parser.parse_type_list,
      #parser.parse_type_arguments_or_diamond,
      #parser.parse_nonwildcard_type_arguments_or_diamond,
      #parser.parse_type_parameters,
      #parser.parse_type_parameter,
      #parser.parse_array_dimension,
      #parser.parse_modifiers,
      #parser.parse_annotations,
      #parser.parse_annotation,
      #parser.parse_annotation_element,
      #parser.parse_element_value_pairs,
      #parser.parse_element_value_pair,
      #parser.parse_element_value,
      #parser.parse_element_values,
      #parser.parse_class_body,
      #parser.parse_class_body_declaration,
      #parser.parse_member_declaration,
      #parser.parse_method_or_field_declaraction,
      #parser.parse_method_or_field_rest,
      #parser.parse_field_declarators_rest,
      #parser.parse_method_declarator_rest,
      #parser.parse_void_method_declarator_rest,
      #parser.parse_constructor_declarator_rest,
      #parser.parse_generic_method_or_constructor_declaration,
      #parser.parse_interface_body,
      #parser.parse_interface_body_declaration,
      #parser.parse_interface_member_declaration,
      #parser.parse_interface_method_or_field_declaration,
      #parser.parse_interface_method_or_field_rest,
      #parser.parse_constant_declarators_rest,
      #parser.parse_constant_declarator_rest,
      #parser.parse_constant_declarator,
      #parser.parse_interface_method_declarator_rest,
      #parser.parse_void_interface_method_declarator_rest,
      #parser.parse_interface_generic_method_declarator,
      #parser.parse_formal_parameters,
      #parser.parse_variable_modifiers,
      #parser.parse_variable_declarators,
      #parser.parse_variable_declarator,
      #parser.parse_variable_declarator_rest,
      #parser.parse_variable_initializer,
      #parser.parse_array_initializer,
      #parser.parse_block,
      #parser.parse_block_statement,
      #parser.parse_local_variable_declaration_statement,
      #parser.parse_statement,
      #parser.parse_catches,
      #parser.parse_catch_clause,
      #parser.parse_resource_specification,
      #parser.parse_resource,
      #parser.parse_switch_block_statement_groups,
      #parser.parse_switch_block_statement_group,
      #parser.parse_for_control,
      #parser.parse_for_var_control,
      #parser.parse_for_var_control_rest,
      #parser.parse_for_variable_declarator_rest,
      #parser.parse_for_init_or_update,
      #parser.parse_expression,
      #parser.parse_method_reference_expression,
      #parser.parse_method_reference,
      #parser.parse_lambda_expression,
      #parser.parse_lambda_method_body,
      #parser.parse_infix_operator,
      #parser.parse_primary,
      #parser.parse_literal,
      #parser.parse_par_expression,
      #parser.parse_arguments,
      #parser.parse_super_suffix,
      #parser.parse_explicit_generic_invocation_suffix,
      #parser.parse_creator,
      #parser.parse_created_name,
      #parser.parse_class_creator_rest,
      #parser.parse_array_creator_rest,
      #parser.parse_identifier_suffix,
      #parser.parse_explicit_generic_invocation,
      #parser.parse_inner_creator,
      #parser.parse_selector,
      #parser.parse_enum_body,
      #parser.parse_enum_constant,
      #parser.parse_annotation_type_body,
      #parser.parse_annotation_type_element_declarations,
      #parser.parse_annotation_type_element_declaration,
      #parser.parse_annotation_method_or_constant_rest,
      #]

    #for f in functions:
    for attr, value in Parser.__dict__.items():
        if callable(value) and attr.startswith('parse_'):
            try:
                parser.tokens.push_marker()
                ast = value(parser)
                print(f"parsing '{code}' with {attr} SUCCEEDED", file=sys.stderr)
                return ast
            except Exception:
                parser.tokens.pop_marker(True)
                #print(f"parsing '{code}' with {attr} failed", file=sys.stderr)
                pass
    print(f"NOTHING was able to parse '{code}' ", file=sys.stderr)
