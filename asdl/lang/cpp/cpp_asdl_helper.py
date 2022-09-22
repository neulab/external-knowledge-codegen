# coding=utf-8

import sys

from asdl.asdl_ast import RealizedField, AbstractSyntaxTree

ENABLE_DEBUG_SUPPORT = True

# from https://stackoverflow.com/questions/15357422/python-determine-if-a-string-should-be-converted-into-int-or-float
def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def cpp_ast_to_asdl_ast(cpp_ast_node, grammar):
    global ENABLE_DEBUG_SUPPORT
    # node should be composite
    cpp_node_name = type(cpp_ast_node).__name__
    # assert py_node_name.startswith('_ast.')

    production = grammar.get_prod_by_ctr_name(cpp_node_name)
    # print(production, file=sys.stderr)

    fields = []
    for field in production.fields:
        if ENABLE_DEBUG_SUPPORT:
            print(f"cpp_ast_to_asdl_ast {cpp_node_name}, field: {field.name}")
        #try:
            #field_value = next(c for c in cpp_ast_node.get_children() if c.kind.name == field.name)
        #except StopIteration as e:
            #field_value = None
        #print(f"cpp_ast_to_asdl_ast {cpp_node_name}, field_value: {field_value}")
        field_value = getattr(cpp_ast_node, field.name)
        asdl_field = RealizedField(field)
        if field.cardinality == 'single' or field.cardinality == 'optional':
            if field_value is not None:  # sometimes it could be 0
                if grammar.is_composite_type(field.type):
                    child_node = cpp_ast_to_asdl_ast(field_value, grammar)
                    asdl_field.add_value(child_node)
                else:
                    asdl_field.add_value(field_value)
        # field with multiple cardinality
        #elif field_value is not None:
        else:
            if grammar.is_composite_type(field.type):
                has_value = False
                for val in cpp_ast_node.subnodes:
                    child_node = cpp_ast_to_asdl_ast(val, grammar)
                    asdl_field.add_value(child_node)
                    has_value = True
                if not has_value:
                    asdl_field.init_empty()
            else:
                for val in cpp_ast_node.subnodes:
                    asdl_field.add_value(str(val))
        #else:
            #pass

        fields.append(asdl_field)

    asdl_node = AbstractSyntaxTree(production, realized_fields=fields)

    return asdl_node


def asdl_ast_to_cpp_ast(asdl_ast_node, grammar):
    cpp_node_type = getattr(sys.modules['cpplang.tree'],
                             asdl_ast_node.production.constructor.name)
    cpp_ast_node = cpp_node_type()

    for field in asdl_ast_node.fields:
        # for composite node
        field_value = None
        #if field.name == 'arguments':
            #print(f'arguments {field.value} {field.cardinality}', file=sys.stderr)
        if grammar.is_composite_type(field.type):
            if (field.value is not None) and (field.cardinality == 'multiple'):
                field_value = []
                for val in field.value:
                    node = asdl_ast_to_cpp_ast(val, grammar)
                    field_value.append(node)
            elif field.value and field.cardinality in ('single', 'optional'):
                field_value = asdl_ast_to_cpp_ast(field.value, grammar)
        else:
            # for primitive node, note that primitive field may have `None`
            # value
            if field.value is not None:
                if field.type.name == 'object':
                    if '.' in field.value or 'e' in field.value:
                        field_value = float(field.value)
                    elif isint(field.value):
                        field_value = int(field.value)
                    else:
                        raise ValueError(
                          f'cannot convert [{field.value}] to float or int')
                elif field.type.name == 'int':
                    if type(field.value) == list:
                        field_value = [None] * len(field.value)
                    else:
                        field_value = int(field.value)
                else:
                    field_value = field.value

            # FIXME: hack! if int? is missing value in ImportFrom(identifier?
            # module, alias* names, int? level), fill with 0
            elif field.name == 'level':
                field_value = 0

        # # must set unused fields to default value...
        # if field_value is None and field.cardinality == 'multiple':
        # field_value = list()

        setattr(cpp_ast_node, field.name, field_value)

    return cpp_ast_node
