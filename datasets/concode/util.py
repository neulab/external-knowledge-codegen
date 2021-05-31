# coding=utf-8

from __future__ import print_function

import itertools
import re
import sys

import javalang
from javalang import ast
from asdl.lang.java import jastor
# from aymara import lima
import nltk

# Used in Conala to mark python code items (variable names…) present in
# rewritten_intent between quotes
QUOTED_TOKEN_RE = re.compile(r"(?P<quote>''|[`'\"])(?P<string>.*?)(?P=quote)")


def compare_ast(node1, node2):
    if not isinstance(node1, str):
        if type(node1) is not type(node2):
            return False
    if isinstance(node1, javalang.ast.Node):
        for k, v1 in list(vars(node1).items()):
            if k in ('lineno', 'col_offset', 'ctx', '_position'):
                continue
            v2 = getattr(node2, k)
            if not compare_ast(v1, v2):
                return False
        return True
    elif isinstance(node1, list):
        return all(itertools.starmap(compare_ast, zip(node1, node2)))
    else:
        return node1 == node2


def tokenize_intent(intent):
    lower_intent = intent.lower()
    # tokens = lima.word_tokenize(lower_intent)
    tokens = nltk.word_tokenize(lower_intent)

    return tokens


def infer_slot_type(quote, value):
    if quote == '`' and value.isidentifier():
        return 'var'
    return 'str'


def canonicalize_intent(intent):
    # handle the following special case: quote is `''`
    marked_token_matches = QUOTED_TOKEN_RE.findall(intent)

    slot_map = dict()
    var_id = 0
    str_id = 0
    for match in marked_token_matches:
        quote = match[0]
        value = match[1]
        quoted_value = quote + value + quote

        slot_type = infer_slot_type(quote, value)

        if slot_type == 'var':
            slot_name = 'var_%d' % var_id
            var_id += 1
            slot_type = 'var'
        else:
            slot_name = 'str_%d' % str_id
            str_id += 1
            slot_type = 'str'

        intent = intent.replace(quoted_value, slot_name)
        slot_map[slot_name] = {
            'value': value.strip().encode().decode('unicode_escape', 'ignore'),
            'quote': quote,
            'type': slot_type}

    # Now handle Concode data: fields and methods.
    # "intent": "Check if details are parsed . concode_field_sep Container
    # concode_elem_sep parent … concode_func_sep Container concode_elem_sep
    # getParent _

    # Each field is announced by the string "concode_field_sep" and each method
    # by "concode_func_sep". Both are composed of a Java type and an identifier
    # separated by "concode_elem_sep"

    # 1. split at first concode_func_sep. Everything after is methods. Split
    # this methods string on concode_func_sep, and each element on
    # concode_elem_sep. Add these methods data to slot_map
    method_id = 0
    if "concode_func_sep" in intent:
        intent, methods = intent.split("concode_func_sep", 1)
        methods = methods.strip().split("concode_func_sep")
        for method in methods:
            return_type, method_name = method.strip().split("concode_elem_sep")
            return_type = return_type.strip()
            method_name = method_name.strip()
            slot_name = 'method_%d' % method_id
            method_id += 1
            slot_type = 'method'

            slot_map[slot_name] = {
                'value': method_name.strip().encode().decode('unicode_escape',
                                                            'ignore'),
                'quote': return_type,
                'type': slot_type}
            #print(f"slot_map[{slot_name}] = {slot_map[slot_name]}",
                  #file=sys.stderr)

    # 2. split the substring before concode_func_sep at first concode_field_sep
    # Everything after is fields. Split this fields string on
    # concode_field_sep, and each element on concode_elem_sep. Add these fields
    # data to slot_map
    if "concode_field_sep" in intent:
        field_id = 0
        intent, fields = intent.split("concode_field_sep", 1)
        fields = fields.strip().split("concode_field_sep")
        for field in fields:
            field_type, field_name = field.strip().split("concode_elem_sep")
            field_type = field_type.strip()
            field_name = field_name.strip()
            slot_name = 'field_%d' % field_id
            field_id += 1
            slot_type = 'field'

            slot_map[slot_name] = {
                'value': field_name.strip().encode().decode('unicode_escape',
                                                            'ignore'),
                'quote': field_type,
                'type': slot_type}
            #print(f"slot_map[{slot_name}] = {slot_map[slot_name]}",
                  #file=sys.stderr)

    #print(f"canonicalized intent = {intent}", file=sys.stderr)
    return intent, slot_map


def replace_identifiers_in_ast(java_ast, identifier2slot):
    for _, node in ast.walk_tree(java_ast):
        if isinstance(node, ast.Node):
            for k, v in list(vars(node).items()):
                if k in ('lineno', 'col_offset', 'ctx'):
                    continue
                # Python 3
                # if isinstance(v, str) or isinstance(v, unicode):
                if isinstance(v, str):
                    if v in identifier2slot:
                        slot_name = identifier2slot[v]
                        # Python 3
                        # if isinstance(slot_name, unicode):
                        #     try: slot_name = slot_name.encode('ascii')
                        #     except: pass

                        setattr(node, k, slot_name)


def is_enumerable_str(identifier_value):
    """
    Test if the quoted identifier value is a list
    """

    return (len(identifier_value) > 2
            and identifier_value[0] in ('{', '(', '[')
            and identifier_value[-1] in ('}', ']', ')'))


def canonicalize_code(code, slot_map):
    string2slot = {x['value']: slot_name
                   for slot_name, x in list(slot_map.items())}

    java_ast = javalang.parse.parse_member_declaration(code)

    replace_identifiers_in_ast(java_ast, string2slot)
    canonical_code = jastor.to_source(java_ast).strip()

    entries_that_are_lists = [slot_name for slot_name, val in slot_map.items()
                              if is_enumerable_str(val['value'])]
    if entries_that_are_lists:
        for slot_name in entries_that_are_lists:
            list_repr = slot_map[slot_name]['value']
            # if list_repr[0] == '[' and list_repr[-1] == ']':
            first_token = list_repr[0]  # e.g. `[`
            last_token = list_repr[-1]  # e.g., `]`
            fake_list = first_token + slot_name + last_token
            slot_map[fake_list] = slot_map[slot_name]
            # else:
            #     fake_list = slot_name

            canonical_code = canonical_code.replace(list_repr, fake_list)

    return canonical_code


def decanonicalize_code(code, slot_map):
    for slot_name, slot_val in slot_map.items():
        if is_enumerable_str(slot_name):
            code = code.replace(slot_name, slot_val['value'])

    slot2string = {x[0]: x[1]['value'] for x in list(slot_map.items())}
    java_ast = javalang.parse.parse_one_of(code)
    replace_identifiers_in_ast(java_ast, slot2string)
    raw_code = jastor.to_source(java_ast).strip()
    # for slot_name, slot_info in slot_map.items():
    #     raw_code = raw_code.replace(slot_name, slot_info['value'])

    return raw_code
