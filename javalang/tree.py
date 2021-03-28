
from .ast import Node

# ------------------------------------------------------------------------------

class CompilationUnit(Node):
    attrs = ("package", "imports", "types")

class Import(Node):
    attrs = ("path", "static", "wildcard")

class Documented(Node):
    attrs = ("documentation",)

class EmptyDeclaration(Documented):
    attrs = ()

class Declaration(Node):
    attrs = ("modifiers", "annotations")

class TypeDeclaration(Declaration, Documented):
    attrs = ("name", "body")

    @property
    def fields(self):
        return [decl for decl in self.body if isinstance(decl, FieldDeclaration)]

    @property
    def methods(self):
        return [decl for decl in self.body if isinstance(decl, MethodDeclaration)]

    @property
    def constructors(self):
        return [decl for decl in self.body if isinstance(decl, ConstructorDeclaration)]

class PackageDeclaration(Declaration, Documented):
    attrs = ("name",)

class ClassDeclaration(TypeDeclaration):
    attrs = ("type_parameters", "extends", "implements")

class EnumDeclaration(TypeDeclaration):
    attrs = ("implements",)

    @property
    def fields(self):
        return [decl for decl in self.body.declarations if isinstance(decl, FieldDeclaration)]

    @property
    def methods(self):
        return [decl for decl in self.body.declarations if isinstance(decl, MethodDeclaration)]

class InterfaceDeclaration(TypeDeclaration):
    attrs = ("type_parameters", "extends",)

class AnnotationDeclaration(TypeDeclaration):
    attrs = ()


class StaticInitializer(Node):
    attrs = ("block",)


class InstanceInitializer(Node):
    attrs = ("block",)

# ------------------------------------------------------------------------------


class Modifier(Node):
    attrs = ("value",)


class Void(Node):
    attrs = ("void",)


class Operator(Node):
    attrs = ("operator",)

# ------------------------------------------------------------------------------

class Type(Node):
    attrs = ("name", "dimensions",)

class BasicType(Type):
    attrs = ()

class ReferenceType(Type):
    attrs = ("arguments", "sub_type")

class TypeArgument(Node):
    attrs = ("type", "pattern_type")

# ------------------------------------------------------------------------------

class TypeParameter(Node):
    attrs = ("name", "extends")

# ------------------------------------------------------------------------------


class Annotation(Node):
    attrs = ("name", "element")

#Annotation:
  #NormalAnnotation
  #MarkerAnnotation
  #SingleElementAnnotation

class NormalAnnotation(Annotation):
    attrs = ()

class MarkerAnnotation(Annotation):
    attrs = ()

class SingleElementAnnotation(Annotation):
    attrs = ()

class ElementValuePair(Node):
    attrs = ("name", "value")

class ElementArrayValue(Node):
    attrs = ("values",)

# ------------------------------------------------------------------------------

class Member(Documented):
    attrs = ()

class MethodDeclaration(Member, Declaration):
    attrs = ("type_parameters", "return_type", "name", "dimensions", "parameters", "throws", "body")

class FieldDeclaration(Member, Declaration):
    attrs = ("type", "declarators")

class ConstructorDeclaration(Declaration, Documented):
    attrs = ("type_parameters", "name", "parameters", "throws", "body")

# ------------------------------------------------------------------------------

class ConstantDeclaration(FieldDeclaration):
    attrs = ()

class ArrayInitializer(Node):
    attrs = ("initializers", "comma")

class VariableDeclaration(Declaration):
    attrs = ("type", "declarators")

class LocalVariableDeclaration(VariableDeclaration):
    attrs = ()

class VariableDeclarator(Node):
    attrs = ("name", "dimensions", "initializer")

class FormalParameter(Declaration):
    attrs = ("type", "name", "dimensions", "varargs")

class InferredFormalParameter(Node):
    attrs = ('name',)

# ------------------------------------------------------------------------------

class Statement(Node):
    attrs = ("label",)

class IfStatement(Statement):
    attrs = ("condition", "then_statement", "else_statement")

class WhileStatement(Statement):
    attrs = ("condition", "body")

class DoStatement(Statement):
    attrs = ("condition", "body")

class ForStatement(Statement):
    attrs = ("control", "body")

class AssertStatement(Statement):
    attrs = ("condition", "value")

class BreakStatement(Statement):
    attrs = ("goto",)

class ContinueStatement(Statement):
    attrs = ("goto",)

class ReturnStatement(Statement):
    attrs = ("expression",)

class ThrowStatement(Statement):
    attrs = ("expression",)

class SynchronizedStatement(Statement):
    attrs = ("lock", "block")

class TryStatement(Statement):
    attrs = ("resources", "block", "catches", "finally_block")

class SwitchStatement(Statement):
    attrs = ("expression", "cases")

class BlockStatement(Statement):
    attrs = ("statements",)

class StatementExpression(Statement):
    attrs = ("expression",)

# ------------------------------------------------------------------------------

class TryResource(Declaration):
    attrs = ("type", "name", "value")

class CatchClause(Statement):
    attrs = ("parameter", "block")

class CatchClauseParameter(Declaration):
    attrs = ("types", "name")

# ------------------------------------------------------------------------------

class SwitchStatementCase(Node):
    attrs = ("case", "statements")

class ForControl(Node):
    attrs = ("init", "condition", "update")

class EnhancedForControl(Node):
    attrs = ("var", "iterable")

# ------------------------------------------------------------------------------

class Expression(Node):
    attrs = ()

class NoExpression(Node):
    attrs = ("null",)

class Identifier(Node):
    attrs = ("id",)

class Primary(Expression):
    attrs = ("prefix_operators", "postfix_operators", "qualifier", "selectors")

class Assignment(Primary):
    attrs = ("expressionl", "value", "type")

class TernaryExpression(Primary):
    attrs = ("condition", "if_true", "if_false")

class BinaryOperation(Primary):
    attrs = ("operator", "operandl", "operandr")

class MethodReference(Primary):
    attrs = ("expression", "method", "type_arguments")


class LambdaExpression(Primary):
    attrs = ('parameters', 'body')

# ------------------------------------------------------------------------------

class Literal(Primary):
    attrs = ("value",)

class This(Primary):
    attrs = ()

class Cast(Primary):
    attrs = ("type", "expression")

class MemberReference(Primary):
    attrs = ("member",)

class Invocation(Primary):
    attrs = ("type_arguments", "arguments")

class ExplicitConstructorInvocation(Invocation):
    attrs = ()

class SuperConstructorInvocation(Invocation):
    attrs = ()

class MethodInvocation(Invocation):
    attrs = ("member",)

class SuperMethodInvocation(Invocation):
    attrs = ("member",)

class SuperMemberReference(Primary):
    attrs = ("member",)

class ArraySelector(Expression):
    attrs = ("index",)

class ClassReference(Primary):
    attrs = ("type",)

class VoidClassReference(ClassReference):
    attrs = ()

# ------------------------------------------------------------------------------

class Creator(Primary):
    attrs = ("type",)

class ArrayCreator(Creator):
    attrs = ("dimensions", "initializer")

class ClassCreator(Creator):
    attrs = ("constructor_type_arguments", "arguments", "body")

class InnerClassCreator(Creator):
    attrs = ("constructor_type_arguments", "arguments", "body")

# ------------------------------------------------------------------------------

class EnumBody(Node):
    attrs = ("constants", "separator", "declarations", "comma")

class EnumConstantDeclaration(Declaration, Documented):
    attrs = ("name", "arguments", "body")

class AnnotationMethod(Declaration):
    attrs = ("name", "return_type", "dimensions", "default")

