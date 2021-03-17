# coding=utf-8

import os
import sys

import jastor
import javalang
from javalang.parser import JavaSyntaxError
from asdl.lang.java.java_transition_system import *
from asdl.hypothesis import *


# read in the grammar specification of Python 2.7, defined in ASDL
asdl_text = open('java_asdl.simplified.txt').read()
grammar = ASDLGrammar.from_text(asdl_text)
print(grammar, flush=True)
# initialize the Java transition parser
parser = JavaTransitionSystem(grammar)

def code_from_hyp(asdl_ast):
    # get the sequence of gold-standard actions to construct the ASDL AST
    actions = parser.get_actions(asdl_ast)
    # a hypothesis is an (partial) ASDL AST generated using a sequence of
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
        print(f't={t}, p_t={p_t}, Action={action}', flush=True)
        hypothesis.apply_action(action)
    src3 = jastor.to_source(asdl_ast_to_java_ast(
      hypothesis.tree, grammar)).replace("\n", "").strip()
    print(f"Java AST from hypothesis: {src3}", flush=True)
    return src3


def test(java_code, check_hypothesis=False):
    # get the (domain-specific) java AST of the example Java code snippet
    java_ast = javalang.parse.parse(java_code)

    # convert the java AST into general-purpose ASDL AST used by tranX
    asdl_ast = java_ast_to_asdl_ast(java_ast, grammar)
    print('String representation of the ASDL AST: \n%s' % asdl_ast.to_string())
    print('Size of the AST: %d' % asdl_ast.size)

    # we can also convert the ASDL AST back into Java AST
    java_ast_reconstructed = asdl_ast_to_java_ast(asdl_ast, grammar)

    src0 = java_code.replace("\n", "").strip()
    print(f"Original Java code      : {src0}", flush=True)
    # get the surface code snippets from the original Python AST,
    # the reconstructed AST and the AST generated using actions
    # they should be the same
    src1 = jastor.to_source(java_ast).replace("\n", "").strip()
    print(f"Java AST                : {src1}", flush=True)
    src2 = jastor.to_source(java_ast_reconstructed).replace("\n", "").strip()
    print(f"Java AST from ASDL      : {src2}", flush=True)

    if not ((src1.replace(" ", "") == src2.replace(" ", "")
             == src0.replace(" ", ""))):
        return False
        # raise Exception("Test failed")

    if check_hypothesis:
        src3 = code_from_hyp(asdl_ast).replace(" ", "").replace("\n", "")
        return src3 == src0
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
              #flush=True)
        #if not test(java, check_hypothesis):
            #print(f"Test failed for code:\n{java_code}", file=sys.stderr)
            #exit(1)
        #print()

    for subdir, dirs, files in os.walk(r'test'):
        for filename in files:
            filepath = os.path.join(subdir, filename)

            if filepath.endswith(".java"):
                print(f"Testing Java file {filepath}", file=sys.stderr)
                with open(filepath, "r") as f:
                    try:
                        java = f.read()
                        if not test(java, check_hypothesis):
                            print(f"**Warn** Test failed for file: {filepath}",
                                  file=sys.stderr)
                            print(java, file=sys.stderr)
                            print()
                            # exit(1)
                    except UnicodeDecodeError:
                        print(f"Error: Cannot decode file as UTF-8. Ignoring: "
                              f"{filepath}",
                              file=sys.stderr)
                    except JavaSyntaxError as e:
                        print(f"Error: Java syntax error: {e}. Ignoring: "
                              f"{filepath}",
                              file=sys.stderr)

