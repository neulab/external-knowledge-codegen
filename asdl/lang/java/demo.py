# coding=utf-8

import colorama
import os
import re
import sys

import jastor
import javalang
from javalang.parser import JavaSyntaxError
from asdl.lang.java.java_transition_system import *
from asdl.hypothesis import *


# read in the grammar specification of Python 2.7, defined in ASDL
asdl_text = open('java_asdl.simplified.txt').read()
grammar = ASDLGrammar.from_text(asdl_text)
# print(grammar, file=sys.stderr)
# initialize the Java transition parser
parser = JavaTransitionSystem(grammar)


class bcolors:
    BLACK = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DEFAULT = '\033[99m'

def cprint(color, string: str, **kwargs):
    print(f"{color}{string}{bcolors.ENDC}", **kwargs)

def removeComments(string):
    # remove all occurance streamed comments (/*COMMENT */) from string
    string = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", string)
    # remove all occurance singleline comments (//COMMENT\n ) from string
    string = re.sub(re.compile("//.*?\n"), "", string)
    return string


def code_from_hyp(asdl_ast):
    # get the sequence of gold-standard actions to construct the ASDL AST
    actions = parser.get_actions(asdl_ast)
    # a hypothesis is a(n) (partial) ASDL AST generated using a sequence of
    # tree-construction actions
    hypothesis = Hypothesis()
    for t, action in enumerate(actions, 1):
        # the type of the action should belong to one of the valid continuing
        # types of the transition system
        valid_cont_types = parser.get_valid_continuation_types(hypothesis)
        if action.__class__ not in valid_cont_types:
            print(f"Error: Valid continuation types are {valid_cont_types} "
                  f"but current action class is {action.__class__}",
                  file=sys.stderr)
            raise Exception(f"{action.__class__} is not in {valid_cont_types}")

        # if it's an ApplyRule action, the production rule should belong to the
        # set of rules with the same LHS type as the current rule
        if isinstance(action, ApplyRuleAction) and hypothesis.frontier_node:
            assert action.production in grammar[hypothesis.frontier_field.type]

        p_t = (hypothesis.frontier_node.created_time
               if hypothesis.frontier_node else -1)
        print(f't={t}, p_t={p_t}, Action={action}', file=sys.stderr)
        hypothesis.apply_action(action)
    return jastor.to_source(asdl_ast_to_java_ast(hypothesis.tree, grammar))


def test(java_code, check_hypothesis=False):
    # get the (domain-specific) java AST of the example Java code snippet
    java_ast = javalang.parse.parse(java_code)

    # convert the java AST into general-purpose ASDL AST used by tranX
    asdl_ast = java_ast_to_asdl_ast(java_ast, grammar)
    # print('String representation of the ASDL AST: \n%s' % asdl_ast.to_string())
    # print('Size of the AST: %d' % asdl_ast.size)

    # we can also convert the ASDL AST back into Java AST
    java_ast_reconstructed = asdl_ast_to_java_ast(asdl_ast, grammar)

    src0 = removeComments(java_code)
    src1 = removeComments(jastor.to_source(java_ast))
    src2 = removeComments(jastor.to_source(java_ast_reconstructed))
    if check_hypothesis:
        src3 = code_from_hyp(asdl_ast)
        src3 = removeComments(src3)
    if not ((src1.replace(" ", "").replace("\n", "").strip()
             == src2.replace(" ", "").replace("\n", "").strip()
             == src0.replace(" ", "").replace("\n", "").strip())) or (
               (check_hypothesis
                and (src3.replace(" ", "").replace("\n", "").strip()
                     != src1.replace(" ", "").replace("\n", "").strip()))):
        cprint(bcolors.BLUE,
               f"))))))) Original Java code      :\n{src0}\n(((((((\n",
               file=sys.stderr)
        # get the surface code snippets from the original Python AST,
        # the reconstructed AST and the AST generated using actions
        # they should be the same
        cprint(bcolors.CYAN,
               f"}}}}}}}}}}}}}} Java AST                :\n{src1}\n{{{{{{{{{{{{{{\n",
               file=sys.stderr)
        cprint(bcolors.GREEN,
               f"]]]]]]] Java AST from ASDL      :\n{src2}\n[[[[[[[\n",
               file=sys.stderr)
        if check_hypothesis:
            cprint(bcolors.MAGENTA,
                  f">>>>>>> Java AST from hyp       :\n{src3}\n<<<<<<<\n",
                  file=sys.stderr)
        return False
        # raise Exception("Test failed")

    else:
        return True

java_code = [
    """public class Test {}""",
    """package javalang.brewtab.com; class Test {}""",
    """class Test { String s = "bepo"; }""",
    """class Test {
        public static void main(String[] args) {}
    }""",
    """class Test {
        public static void main(String[] args) {int i = 42; ++i;}
    }""",
    """class Test {
        public static void main(String[] args) {
            System.out.println();
        }
    }""",
    """class Test {
        public static void main(String[] args) {
            for (int i = 42; i < args.length; i++)
                System.out.print(i == 666 ? args[i] : " " + args[i]);
            System.out.println();
        }
    }""",
    """package javalang.brewtab.com;
        class Test {
        public static void main(String[] args) {
            for (int i = 42; i < args.length; i++)
                System.out.print(i == 666 ? args[i] : " " + args[i]);
            System.out.println();
        }
    }""",
    ]

if __name__ == '__main__':
    check_hypothesis = False
    #for i, java in enumerate(java_code):
        #print(f'Test ({i+1}/{len(java_code)}). Code:\n"""\n{java}\n"""',
              #file=sys.stderr)
        #if not test(java, check_hypothesis):
            #print(f"Test failed for code:\n{java_code}", file=sys.stderr)
            #exit(1)
        #print()
    filepath = "test/java/com/github/javaparser/VisitorTest.java"
    #filepath = "test/AnnotationJavadoc.java"
    #filepath = "test/test_sourcecode/com/github/javaparser/printer/JavaConcepts.java"
    #filepath = "test/test_sourcecode/javasymbolsolver_0_6_0/src/java-symbol-solver-core/com/github/javaparser/symbolsolver/SourceFileInfoExtractor.java"
    #for subdir, _, files in os.walk(r'test'):
        #for filename in files:
            #filepath = os.path.join(subdir, filename)

    if filepath.endswith(".java"):
        cprint(bcolors.ENDC,
                f"\n−−−−−−−−−−\nTesting Java file {bcolors.MAGENTA}{filepath}",
                file=sys.stderr)
        with open(filepath, "r") as f:
            try:
                java = f.read()
                if not test(java, check_hypothesis):
                    cprint(bcolors.RED,
                            f"**Warn**{bcolors.ENDC} Test failed for "
                            f"file: {bcolors.MAGENTA}{filepath}",
                            file=sys.stderr)
                    #print(java, file=sys.stderr)
                    print("", file=sys.stderr)
                    #exit(1)
            except UnicodeDecodeError:
                cprint(bcolors.RED,
                        f"Error: Cannot decode file as UTF-8. Ignoring: "
                        f"{filepath}",
                        file=sys.stderr)
            except JavaSyntaxError as e:
                cprint(bcolors.RED,
                        f"Error: Java syntax error: {e}. Ignoring: "
                        f"{filepath}",
                        file=sys.stderr)

