import json
import six
import subprocess
import sys
from typing import (List, Set, Tuple)

from . import util
from . import tree
from .tokenizer import (
    EndOfInput, Keyword, Modifier, BasicType, Identifier,
    Annotation, Literal, Operator, CppToken,
    )

ENABLE_DEBUG_SUPPORT = False

def parse_debug(method):
    global ENABLE_DEBUG_SUPPORT

    if ENABLE_DEBUG_SUPPORT:
        def _method(self):
            if not hasattr(self, 'recursion_depth'):
                self.recursion_depth = 0

            if self.debug:
                depth = "%02d" % (self.recursion_depth,)
                token = six.text_type(self.tokens.look())
                start_value = self.tokens.look().value
                name = method.__name__
                sep = ("-" * self.recursion_depth)
                e_message = ""

                print("%s %s> %s(%s)" % (depth, sep, name, token))

                self.recursion_depth += 1

                try:
                    r = method(self)

                except CppSyntaxError as e:
                    e_message = e.description
                    raise

                except Exception as e:
                    e_message = six.text_type(e)
                    raise

                finally:
                    token = six.text_type(self.tokens.last())
                    print("%s <%s %s(%s, %s) %s" %
                        (depth, sep, name, start_value, token, e_message))
                    self.recursion_depth -= 1
            else:
                self.recursion_depth += 1
                try:
                    r = method(self)
                finally:
                    self.recursion_depth -= 1

            return r

        return _method

    else:
        return method

# ------------------------------------------------------------------------------
# ---- Parsing exception ----

class CppParserBaseException(Exception):
    def __init__(self, message=''):
        super(CppParserBaseException, self).__init__(message)

class CppSyntaxError(CppParserBaseException):
    def __init__(self, description, at=None):
        super(CppSyntaxError, self).__init__()

        self.description = description
        self.at = at

class CppParserError(CppParserBaseException):
    pass

# ------------------------------------------------------------------------------
# ---- Parser class ----

class Parser(object):
    operator_precedence = [ set(('||',)),
                            set(('&&',)),
                            set(('|',)),
                            set(('^',)),
                            set(('&',)),
                            set(('==', '!=')),
                            set(('<', '>', '>=', '<=', 'instanceof')),
                            set(('<<', '>>', '>>>')),
                            set(('+', '-')),
                            set(('*', '/', '%'))]

    def __init__(self, cpp_code):
        preprocess = subprocess.Popen(
            ["clang", "-x", "c++", "-std=c++17", "-fPIC",
             "-I/usr/include/x86_64-linux-gnu/qt5",
             "-I/usr/include/x86_64-linux-gnu/qt5/QtCore",
             "-I/home/gael/Projets/Lima/lima/lima_common/src/",
             "-I/home/gael/Projets/Lima/lima/lima_common/src/common/XMLConfigurationFiles",
             "-E", "-"],

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        preprocess_stdout_data, preprocess_stderr_data = preprocess.communicate(
            input=cpp_code.encode())
        p = subprocess.Popen(
            ["clang", "-x", "c++", "-std=c++17", "-fPIC",
             "-I/usr/include/x86_64-linux-gnu/qt5",
             "-I/usr/include/x86_64-linux-gnu/qt5/QtCore",
             "-I/home/gael/Projets/Lima/lima/lima_common/src/",
             "-I/home/gael/Projets/Lima/lima/lima_common/src/common/XMLConfigurationFiles",
             "-Xclang", "-ast-dump=json",
             "-fsyntax-only", "-"],

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout_data, stderr_data = p.communicate(input=preprocess_stdout_data)
        self.tu = json.loads(stdout_data.decode())
        self.stack = []
        self.debug = False
        self.source_code = preprocess_stdout_data.decode()

# ------------------------------------------------------------------------------
# ---- Debug control ----

    def set_debug(self, debug=True):
        self.debug = debug

# ------------------------------------------------------------------------------
# ---- Parsing entry point ----

    def parse(self):
        return self.parse_TranslationUnit(self.tu)

# ------------------------------------------------------------------------------
# ---- Helper methods ----

    #def illegal(self, description, at=None):
        #if not at:
            #at = self.tokens.look()

        #raise CppSyntaxError(description, at)

    #def accept(self, *accepts):
        #last = None

        #if len(accepts) == 0:
            #raise CppParserError("Missing acceptable values")

        #for accept in accepts:
            #token = next(self.tokens)
            #if isinstance(accept, six.string_types) and (
                    #not token.value == accept):
                #self.illegal("Expected '%s'" % (accept,))
            #elif isinstance(accept, type) and not isinstance(token, accept):
                #self.illegal("Expected %s" % (accept.__name__,))

            #last = token

        #return last.value

    #def would_accept(self, *accepts):
        #if len(accepts) == 0:
            #raise CppParserError("Missing acceptable values")

        #for i, accept in enumerate(accepts):
            #token = self.tokens.look(i)

            #if isinstance(accept, six.string_types) and (
                    #not token.value == accept):
                #return False
            #elif isinstance(accept, type) and not isinstance(token, accept):
                #return False

        #return True

    #def try_accept(self, *accepts):
        #if len(accepts) == 0:
            #raise CppParserError("Missing acceptable values")

        #for i, accept in enumerate(accepts):
            #token = self.tokens.look(i)

            #if isinstance(accept, six.string_types) and (
                    #not token.value == accept):
                #return False
            #elif isinstance(accept, type) and not isinstance(token, accept):
                #return False

        #for i in range(0, len(accepts)):
            #next(self.tokens)

        #return True

    #def build_binary_operation(self, parts, start_level=0) -> tree.BinaryOperation:
        #if len(parts) == 1:
            #return parts[0]

        #operands = list()
        #operators = list()

        #i = 0

        #for level in range(start_level, len(self.operator_precedence)):
            #for j in range(1, len(parts) - 1, 2):
                #if parts[j].operator in self.operator_precedence[level]:
                    #operand = self.build_binary_operation(parts[i:j], level + 1)
                    #operator = parts[j]
                    #i = j + 1

                    #operands.append(operand)
                    #operators.append(operator)

            #if operands:
                #break

        #operand = self.build_binary_operation(parts[i:], level + 1)
        #operands.append(operand)

        #operation = operands[0]

        #for operator, operandr in zip(operators, operands[1:]):
            #operation = tree.BinaryOperation(operandl=operation)
            #operation.operator = operator
            #operation.operandr = operandr

        #return operation

    #def is_annotation(self, i=0):
        #""" Returns true if the position is the start of an annotation application
        #(as opposed to an annotation declaration)

        #"""

        #return (isinstance(self.tokens.look(i), Annotation)
                #and not self.tokens.look(i + 1).value == 'interface')

    #def is_annotation_declaration(self, i=0):
        #""" Returns true if the position is the start of an annotation application
        #(as opposed to an annotation declaration)

        #"""

        #return (isinstance(self.tokens.look(i), Annotation)
                #and self.tokens.look(i + 1).value == 'interface')

    def parse_subnodes(self, node):
        if 'inner' in node:
            assert len(node['inner']) > 0
            result = [self.parse_node(c) for c in node['inner']]
            return [c for c in result if c is not None]
        else:
            return []

    def collect_comment(self, node) -> str:
        if node['kind'] == 'TextComment':
            return node['text']
        return " ".join([self.collect_comment(subnode) for subnode in node['inner']])

    def get_node_source_code(self, node) -> str:
        return self.source_code[
            node['range']['begin']['offset']:node['range']['end']['offset']].strip()
# ------------------------------------------------------------------------------
# ---- Parsing methods ----

# ------------------------------------------------------------------------------
# -- Identifiers --

    #@parse_debug
    #def parse_identifier(self):
        #return self.accept(Identifier)

    #@parse_debug
    #def parse_qualified_identifier(self):
        #qualified_identifier = list()

        #while True:
            #identifier = self.parse_identifier()
            #qualified_identifier.append(identifier)

            #if not self.try_accept('.'):
                #break

        #return '.'.join(qualified_identifier)

    #@parse_debug
    #def parse_qualified_identifier_list(self):
        #qualified_identifiers = list()

        #while True:
            #qualified_identifier = self.parse_qualified_identifier()
            #qualified_identifiers.append(qualified_identifier)

            #if not self.try_accept(','):
                #break

        #return qualified_identifiers

    def abort_visit(node):  # XXX: self?
        msg = (f"No defined parse handler for clang node of type `{node['kind']}`.\n"
               f"please define `parse_{node['kind']}` in cpplang/parser.py.")
        raise AttributeError(msg)

    @parse_debug
    def parse_node(self, node, abort=abort_visit) -> tree.Node:
        if node is None or 'kind' not in node:
            return None
        print(f"parse_node {node['kind']}", file=sys.stderr)
        if (('isImplicit' in node and node['isImplicit'])
            or ('loc' in node and 'includedFrom' in node['loc'])
            or ('range' in node and 'includedFrom' in node['range']['begin'])
            or ('loc' in node and 'range' in node['loc']
                and 'includedFrom' in node['loc']['range']['begin'])
            or ('loc' in node and 'spellingLoc' in node['loc'] and 'includedFrom' in node['loc']['spellingLoc'])
            or ('range' in node and 'spellingLoc' in node['range']['begin'] and 'includedFrom' in node['range']['begin']['spellingLoc'])
            ):
            return None
        elif ((len(self.stack) == 0 and node['loc'] and 'file' in node['loc']
             and node['loc']['file'] == "<stdin>")
                or len(self.stack) > 0):
            self.stack.append(node)
            parse_method = getattr(self, "parse_"+node['kind'], abort)
            result = parse_method(node)
            self.stack.pop()
            return result
        elif ((len(self.stack) == 0 and 'loc' in node
               and 'file' not in node['loc']
               and 'includedFrom' not in node['loc']
               and ('range' not in node['loc']
                    or 'includedFrom' not in node['loc']['range']['begin'])
               and ('spellingLoc' not in node['loc']
                    or 'includedFrom' not in node['loc']['spellingLoc']))
                or len(self.stack) > 0):
            self.stack.append(node)
            parse_method = getattr(self, "parse_"+node['kind'], abort)
            result = parse_method(node)
            self.stack.pop()
            return result
        else:
            return None

# ------------------------------------------------------------------------------
# -- Top level units --

    @parse_debug
    def parse_TranslationUnit(self, node) -> tree.TranslationUnit:
        assert node['kind'] == "TranslationUnitDecl"
        #print(f"parse_TranslationUnit {node}", file=sys.stderr)
        subnodes = self.parse_subnodes(node)
        return tree.TranslationUnit(subnodes=subnodes)

    @parse_debug
    def parse_CXXRecordDecl(self, node) -> tree.CXXRecordDecl:
        assert node['kind'] == "CXXRecordDecl"
        if 'isImplicit' in node and node['isImplicit']:
            return None
        name = node['name']
        kind = node['tagUsed']
        bases = []
        if "bases" in node:
            for base in node['bases']:
                if base['writtenAccess'] != 'none':
                    bases.append(f"{base['writtenAccess']} {base['type']['qualType']}")
                else:
                    bases.append(f"{base['type']['qualType']}")
        subnodes = self.parse_subnodes(node)
        return tree.CXXRecordDecl(name=name, kind=kind, bases=", ".join(bases),
                                  subnodes=subnodes)

    @parse_debug
    def parse_CXXConstructorDecl(self, node) -> tree.CXXConstructorDecl:
        assert node['kind'] == "CXXConstructorDecl"
        if 'isImplicit' in node and node['isImplicit']:
            return None
        name = self.get_node_source_code(node).split("(")[0]
        subnodes = self.parse_subnodes(node)
        return tree.CXXConstructorDecl(name=name, subnodes=subnodes)

    @parse_debug
    def parse_CXXCtorInitializer(self, node) -> tree.CXXCtorInitializer:
        assert node['kind'] == "CXXCtorInitializer"
        if (len(self.get_node_source_code(node['inner'][0])) == 0
                and node['inner'][0]['kind'] == 'CXXConstructExpr'):
            return None
        if 'anyInit' in node:
            name = node['anyInit']['name']
        elif 'baseInit' in node:
            name = node['baseInit']['qualType']
        else:
            name = None
        subnodes = self.parse_subnodes(node)
        return tree.CXXCtorInitializer(name=name, subnodes=subnodes)

    @parse_debug
    def parse_CXXDestructorDecl(self, node) -> tree.CXXDestructorDecl:
        assert node['kind'] == "CXXDestructorDecl"
        if 'isImplicit' in node and node['isImplicit']:
            return None
        virtual = 'virtual' if 'virtual' in node and node['virtual'] else ''
        name = self.get_node_source_code(node).split("(")[0]
        subnodes = self.parse_subnodes(node)
        return tree.CXXDestructorDecl(name=name, virtual=virtual, subnodes=subnodes)

    @parse_debug
    def parse_AccessSpecDecl(self, node) -> tree.AccessSpecDecl:
        assert node['kind'] == "AccessSpecDecl"
        access_spec = node['access']
        subnodes = self.parse_subnodes(node)

        return tree.AccessSpecDecl(access_spec=access_spec, subnodes=subnodes)

    @parse_debug
    def parse_CXXMethodDecl(self, node) -> tree.CXXMethodDecl:
        assert node['kind'] == "CXXMethodDecl"
        if 'isImplicit' in node and node['isImplicit']:
            return None
        name = self.get_node_source_code(node).split("(")[0].split(" ")[-1]
        return_type = node['type']['qualType'].split("(")[0]
        subnodes = self.parse_subnodes(node)
        return tree.CXXMethodDecl(name=name, return_type=return_type, subnodes=subnodes)

    @parse_debug
    def parse_FunctionDecl(self, node) -> tree.FunctionDecl:
        assert node['kind'] == "FunctionDecl"
        name = node['name']
        return_type = node['type']['qualType'].split("(")[0]
        subnodes = self.parse_subnodes(node)
        return tree.FunctionDecl(name=name, return_type=return_type, subnodes=subnodes)

    @parse_debug
    def parse_ParmVarDecl(self, node) -> tree.ParmVarDecl:
        assert node['kind'] == "ParmVarDecl"
        name = node['name'] if 'name' in node else ''
        if name == '':
            #breakpoint()
            var_type = self.source_code[
                node['range']['begin']['offset']:
                    (node['range']['end']['offset']
                     + node['range']['end']['tokLen'])].strip()
        else:
            var_type = self.source_code[
                node['range']['begin']['offset']:node['range']['end']['offset']].strip()
        subnodes = self.parse_subnodes(node)
        return tree.ParmVarDecl(name=name, type=var_type, subnodes=subnodes)

    @parse_debug
    def parse_CompoundStmt(self, node) -> tree.CompoundStmt:
        assert node['kind'] == "CompoundStmt"
        subnodes = self.parse_subnodes(node)
        return tree.CompoundStmt(subnodes=subnodes)

    @parse_debug
    def parse_IfStmt(self, node) -> tree.IfStmt:
        assert node['kind'] == "IfStmt"
        subnodes = self.parse_subnodes(node)
        return tree.IfStmt(subnodes=subnodes)

    @parse_debug
    def parse_ForStmt(self, node) -> tree.ForStmt:
        assert node['kind'] == "ForStmt"
        subnodes = self.parse_subnodes(node)
        return tree.ForStmt(subnodes=subnodes)

    @parse_debug
    def parse_ContinueStmt(self, node) -> tree.ContinueStmt:
        assert node['kind'] == "ContinueStmt"
        subnodes = self.parse_subnodes(node)
        return tree.ContinueStmt(subnodes=subnodes)

    @parse_debug
    def parse_ReturnStmt(self, node) -> tree.ReturnStmt:
        assert node['kind'] == "ReturnStmt"
        subnodes = self.parse_subnodes(node)
        assert len(subnodes) <= 1
        if len(subnodes) == 0:
            return tree.ReturnStmt()
        else:
            return tree.ReturnStmt(subnodes=subnodes)

    def parse_SwitchStmt(self, node) -> tree.SwitchStmt:
        assert node['kind'] == "SwitchStmt"
        subnodes = self.parse_subnodes(node)
        return tree.SwitchStmt(subnodes=subnodes)

    def parse_CaseStmt(self, node) -> tree.CaseStmt:
        assert node['kind'] == "CaseStmt"
        subnodes = self.parse_subnodes(node)
        return tree.CaseStmt(subnodes=subnodes)

    def parse_BreakStmt(self, node) -> tree.BreakStmt:
        assert node['kind'] == "BreakStmt"
        subnodes = []
        return tree.BreakStmt(subnodes=subnodes)

    def parse_DefaultStmt(self, node) -> tree.DefaultStmt:
        assert node['kind'] == "DefaultStmt"
        subnodes = self.parse_subnodes(node)
        return tree.DefaultStmt(subnodes=subnodes)

    def parse_CXXThisExpr(self, node) -> tree.CXXThisExpr:
        assert node['kind'] == "CXXThisExpr"
        subnodes = self.parse_subnodes(node)
        return tree.CXXThisExpr(subnodes=subnodes)

    def parse_MemberExpr(self, node) -> tree.MemberExpr:
        assert node['kind'] == "MemberExpr"
        name = node['name']
        subnodes = self.parse_subnodes(node)
        return tree.MemberExpr(name=name, subnodes=subnodes)

    def parse_ConstantExpr(self, node) -> tree.ConstantExpr:
        assert node['kind'] == "ConstantExpr"
        value = node['value']
        subnodes = self.parse_subnodes(node)
        return tree.ConstantExpr(value=value, subnodes=subnodes)

    @parse_debug
    def parse_DeclRefExpr(self, node) -> tree.DeclRefExpr:
        assert node['kind'] == "DeclRefExpr"
        name = self.get_node_source_code(node)+node['referencedDecl']['name']
        kind = node['referencedDecl']['kind']
        subnodes = self.parse_subnodes(node)
        return tree.DeclRefExpr(name=name, kind=kind, subnodes=subnodes)

    @parse_debug
    def parse_IntegerLiteral(self, node) -> tree.IntegerLiteral:
        assert node['kind'] == "IntegerLiteral"
        value = node['value']
        subnodes = self.parse_subnodes(node)
        return tree.IntegerLiteral(value=value, subnodes=subnodes)

    @parse_debug
    def parse_FloatingLiteral(self, node) -> tree.FloatingLiteral:
        assert node['kind'] == "FloatingLiteral"
        value = node['value']
        subnodes = self.parse_subnodes(node)
        return tree.FloatingLiteral(value=value, subnodes=subnodes)

    @parse_debug
    def parse_CharacterLiteral(self, node) -> tree.CharacterLiteral:
        assert node['kind'] == "CharacterLiteral"
        value = chr(node['value'])
        subnodes = self.parse_subnodes(node)
        return tree.CharacterLiteral(value=value, subnodes=subnodes)

    @parse_debug
    def parse_StringLiteral(self, node) -> tree.StringLiteral:
        assert node['kind'] == "StringLiteral"
        value = node['value']
        subnodes = self.parse_subnodes(node)
        return tree.StringLiteral(value=value, subnodes=subnodes)

    @parse_debug
    def parse_NamespaceDecl(self, node) -> tree.NamespaceDecl:
        assert node['kind'] == "NamespaceDecl"
        name = node['name']
        subnodes = self.parse_subnodes(node)
        return tree.NamespaceDecl(name=name, subnodes=subnodes)

    #@parse_debug
    #def parse_Namespace(self, node) -> tree.Namespace:
        #assert node['kind'] == "Namespace"
        #name = node['name']
        #subnodes = self.parse_subnodes(node)
        #return tree.Namespace(name=name, subnodes=subnodes)

    @parse_debug
    def parse_UsingDirectiveDecl(self, node) -> tree.UsingDirectiveDecl:
        assert node['kind'] == "UsingDirectiveDecl"
        name = node['nominatedNamespace']['name']
        return tree.UsingDirectiveDecl(name=name)

    @parse_debug
    def parse_DeclStmt(self, node) -> tree.DeclStmt:
        assert node['kind'] == "DeclStmt"
        subnodes = self.parse_subnodes(node)
        return tree.DeclStmt(subnodes=subnodes)

    @parse_debug
    def parse_VarDecl(self, node) -> tree.VarDecl:
        assert node['kind'] == "VarDecl"
        name = node['name']
        init = node['init']
        storage_class = node['storageClass'] if "storageClass" in node else ""
        splitted_type = self.source_code[
            node['range']['begin']['offset']:
                node['range']['end']['offset']].strip().split(" ")
        if len(storage_class) > 0:
            splitted_type.pop(0)
        splitted_type.pop()
        var_type, array_decl = (splitted_type if len(splitted_type) == 2
                                else (splitted_type[0], ""))
        if 'init' in node:
            subnodes = self.parse_subnodes(node)
        else:
            subnodes = []
        return tree.VarDecl(name=name, storage_class=storage_class, type=var_type,
                            array=array_decl, init=init, subnodes=subnodes)

    @parse_debug
    def parse_InitListExpr(self, node) -> tree.InitListExpr:
        assert node['kind'] == "InitListExpr"
        subnodes = self.parse_subnodes(node)
        return tree.InitListExpr(subnodes=subnodes)

    @parse_debug
    def parse_TypeRef(self, node) -> tree.TypeRef:
        assert node['kind'] == "TypeRef"
        name = node['name']
        subnodes = self.parse_subnodes(node)
        return tree.TypeRef(name=name, subnodes=subnodes)

    #@parse_debug
    #def parse_NamespaceRef(self, node) -> tree.NamespaceRef:
        #assert node['kind'] == "NamespaceRef"
        #name = node['name']
        #subnodes = self.parse_subnodes(node)
        #return tree.NamespaceRef(name=name, subnodes=subnodes)

    @parse_debug
    def parse_ExprWithCleanups(self, node) -> tree.ExprWithCleanups:
        assert node['kind'] == "ExprWithCleanups"
        subnodes = self.parse_subnodes(node)
        return tree.ExprWithCleanups(subnodes=subnodes)

    @parse_debug
    def parse_CXXConstructExpr(self, node) -> tree.CXXConstructExpr:
        assert node['kind'] == "CXXConstructExpr"
        #if len(self.get_node_source_code(node)) == 0:
            #breakpoint()
            #return None

        the_type = node['type']['qualType']
        subnodes = self.parse_subnodes(node)
        return tree.CXXConstructExpr(type=the_type, subnodes=subnodes)

    @parse_debug
    def parse_MaterializeTemporaryExpr(self, node) -> tree.MaterializeTemporaryExpr:
        assert node['kind'] == "MaterializeTemporaryExpr"
        subnodes = self.parse_subnodes(node)
        return tree.MaterializeTemporaryExpr(subnodes=subnodes)

    @parse_debug
    def parse_CXXBindTemporaryExpr(self, node) -> tree.CXXBindTemporaryExpr:
        assert node['kind'] == "CXXBindTemporaryExpr"
        subnodes = self.parse_subnodes(node)
        assert len(subnodes) > 0
        return tree.CXXBindTemporaryExpr(subnodes=subnodes)

    @parse_debug
    def parse_ImplicitCastExpr(self, node) -> tree.ImplicitCastExpr:
        assert node['kind'] == "ImplicitCastExpr"
        subnodes = self.parse_subnodes(node)
        return tree.ImplicitCastExpr(subnodes=subnodes)

    @parse_debug
    def parse_CXXDefaultArgExpr(self, node) -> None:
        assert node['kind'] == "CXXDefaultArgExpr"
        return None

    @parse_debug
    def parse_FieldDecl(self, node) -> tree.FieldDecl:
        assert node['kind'] == "FieldDecl"
        name = node['name']
        splitted_type = self.source_code[node['range']['begin']['offset']:node['range']['end']['offset']].strip().split(" ")
        var_type, array_decl = splitted_type if len(splitted_type) == 2 else (splitted_type[0], "")
        #var_type = node['type']['qualType']
        if 'hasInClassInitializer' in node:
            subnodes = self.parse_subnodes(node)
        else:
            subnodes = []
        return tree.FieldDecl(name=name, type=var_type, subnodes=subnodes)

    @parse_debug
    def parse_BinaryOperator(self, node) -> tree.BinaryOperator:
        assert node['kind'] == "BinaryOperator"
        opcode = node['opcode']
        subnodes = self.parse_subnodes(node)
        return tree.BinaryOperator(opcode=opcode, subnodes=subnodes)

    @parse_debug
    def parse_UnaryOperator(self, node) -> tree.UnaryOperator:
        assert node['kind'] == "UnaryOperator"
        opcode = node['opcode']
        subnodes = self.parse_subnodes(node)
        postfix = str(node['isPostfix'])
        return tree.UnaryOperator(opcode=opcode, postfix=postfix, subnodes=subnodes)

    @parse_debug
    def parse_ParenExpr(self, node) -> tree.ParenExpr:
        assert node['kind'] == "ParenExpr"
        subnodes = self.parse_subnodes(node)
        return tree.ParenExpr(subnodes=subnodes)

    @parse_debug
    def parse_ClassTemplateDecl(self, node) -> tree.ClassTemplateDecl:
        assert node['kind'] == "ClassTemplateDecl"
        subnodes = self.parse_subnodes(node)
        return tree.ClassTemplateDecl(subnodes=subnodes)

    @parse_debug
    def parse_FunctionTemplateDecl(self, node) -> tree.FunctionTemplateDecl:
        assert node['kind'] == "FunctionTemplateDecl"
        subnodes = self.parse_subnodes(node)
        return tree.FunctionTemplateDecl(subnodes=subnodes)

    @parse_debug
    def parse_TemplateTypeParmDecl(self, node) -> tree.TemplateTypeParmDecl:
        assert node['kind'] == "TemplateTypeParmDecl"
        name = node['name']
        subnodes = self.parse_subnodes(node)
        return tree.TemplateTypeParmDecl(name=name, subnodes=subnodes)

    @parse_debug
    def parse_NonTypeTemplateParmDecl(self, node) -> tree.NonTypeTemplateParmDecl:
        assert node['kind'] == "NonTypeTemplateParmDecl"
        name = node['name']
        the_type = node['type']['qualType']
        subnodes = self.parse_subnodes(node)
        return tree.NonTypeTemplateParmDecl(name=name, type=the_type, subnodes=subnodes)

    @parse_debug
    def parse_FullComment(self, node) -> tree.FullComment:
        assert node['kind'] == "FullComment"
        comment = self.collect_comment(node)
        return tree.FullComment(comment=comment)

    @parse_debug
    def parse_OverrideAttr(self, node) -> tree.OverrideAttr:
        assert node['kind'] == "OverrideAttr"
        return tree.OverrideAttr()

    @parse_debug
    def parse_CXXMemberCallExpr(self, node) -> tree.CXXMemberCallExpr:
        assert node['kind'] == "CXXMemberCallExpr"
        subnodes = self.parse_subnodes(node)
        return tree.CXXMemberCallExpr(subnodes=subnodes)

    @parse_debug
    def parse_CallExpr(self, node) -> tree.CallExpr:
        assert node['kind'] == "CallExpr"
        subnodes = self.parse_subnodes(node)
        return tree.CallExpr(subnodes=subnodes)

    @parse_debug
    def parse_CXXOperatorCallExpr(self, node) -> tree.CXXOperatorCallExpr:
        assert node['kind'] == "CXXOperatorCallExpr"
        subnodes = self.parse_subnodes(node)
        assert len(subnodes) == 3
        op = subnodes[0]
        left = subnodes[1]
        right = subnodes[2]
        return tree.CXXOperatorCallExpr(left=left, op=op, right=right)

    @parse_debug
    def parse_CXXBoolLiteralExpr(self, node) -> tree.CXXBoolLiteralExpr:
        assert node['kind'] == "CXXBoolLiteralExpr"
        subnodes = self.parse_subnodes(node)
        return tree.CXXBoolLiteralExpr(value=str(node['value']))

    @parse_debug
    def parse_CXXTemporaryObjectExpr(self, node) -> tree.CXXTemporaryObjectExpr:
        assert node['kind'] == "CXXTemporaryObjectExpr"
        the_type = node['type']['qualType']
        subnodes = self.parse_subnodes(node)
        assert len(subnodes) > 0
        return tree.CXXTemporaryObjectExpr(type=the_type, subnodes=subnodes)

    @parse_debug
    def parse_CXXFunctionalCastExpr(self, node) -> tree.CXXFunctionalCastExpr:
        assert node['kind'] == "CXXFunctionalCastExpr"
        the_type = self.get_node_source_code(node).split("(")[0]
        #the_type = node['type']['qualType']
        #the_type = node['conversionFunc']['name']
        if the_type == 'Lima::Common::XMLConfigurationFiles::ModuleConfigurationStructure':
            breakpoint()
        elif the_type == 'basic_string':
            breakpoint()
        subnodes = self.parse_subnodes(node)
        return tree.CXXFunctionalCastExpr(type=the_type, subnodes=subnodes)

    @parse_debug
    def parse_NullStmt(self, node) -> tree.NullStmt:
        assert node['kind'] == "NullStmt"
        subnodes = self.parse_subnodes(node)
        return tree.NullStmt(subnodes=subnodes)


def parse(tokens, debug=False):
    parser = Parser(tokens)
    parser.set_debug(debug)
    return parser.parse()
