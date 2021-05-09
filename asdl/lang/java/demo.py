# coding=utf-8

import argparse
import colorama
import os
import re
import sys
from typing import List

import jastor
import javalang
from javalang.parser import JavaSyntaxError
from asdl.lang.java.java_transition_system import *
from asdl.hypothesis import *


# read in the grammar specification of Java SE8, defined in ASDL
asdl_text = open('java_asdl.simplified.txt').read()
grammar = ASDLGrammar.from_text(asdl_text)
# print(grammar, file=sys.stderr)

# initialize the Java transition parser
transition_system = JavaTransitionSystem(grammar)


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


def cprint(color: bcolors, string: str, **kwargs) -> None:
    print(f"{color}{string}{bcolors.ENDC}", **kwargs)


def removeComments(string: str) -> str:
    # remove all occurance streamed comments (/*COMMENT */) from string
    string = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", string)
    # remove all occurance singleline comments (//COMMENT\n ) from string
    string = re.sub(re.compile("//.*"), "", string)
    return string


def code_from_hyp(asdl_ast, debug=False):
    # get the sequence of gold-standard actions to construct the ASDL AST
    actions = transition_system.get_actions(asdl_ast)
    # a hypothesis is a(n) (partial) ASDL AST generated using a sequence of
    # tree-construction actions
    hyp = Hypothesis()
    for t, action in enumerate(actions):
        # the type of the action should belong to one of the valid continuing
        # types of the transition system
        valid_continuating_types = transition_system.get_valid_continuation_types(hyp)
        if action.__class__ not in valid_continuating_types:
            print(f"Error: Valid continuation types are {valid_cont_types} "
                  f"but current action class is {action.__class__}",
                  file=sys.stderr)
            raise Exception(f"{action.__class__} is not in {valid_cont_types}")

        # if it's an ApplyRule action, the production rule should belong to the
        # set of rules with the same LHS type as the current rule
        if isinstance(action, ApplyRuleAction):
            valid_continuating_productions = transition_system.get_valid_continuating_productions(hyp)
            if action.production not in valid_continuating_productions and hyp.frontier_node:
                raise Exception(f"{bcolors.BLUE}{action.production}"
                                f"{bcolors.ENDC} should be in {bcolors.GREEN}"
                                f"{grammar[hyp.frontier_field.type] if hyp.frontier_field else ''}"
                                f"{bcolors.ENDC}")
                assert action.production in valid_continuating_productions

        p_t = -1
        f_t = None
        if hyp.frontier_node:
            p_t = hyp.frontier_node.created_time
            f_t = hyp.frontier_field.field.__repr__(plain=True)
        if debug:
            print(f'\t[{t}] Action: {action}, frontier field: {f_t}, '
                  f'parent: {p_t}')
        hyp = hyp.clone_and_apply_action(action)
    assert hyp.frontier_node is None and hyp.frontier_field is None
    java_ast = asdl_ast_to_java_ast(hyp.tree, transition_system.grammar)
    code_from_hyp = jastor.to_source(java_ast).strip()
    return code_from_hyp


def simplify(code: str) -> str:
    return (code.replace(" ", "")
            .replace("\t", "")
            .replace("\n", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
            .lower())


def common_prefix(str1: str, str2: str) -> None:
    common_prefix = os.path.commonprefix([str1, str2])
    percent_ok = int(float(len(common_prefix))*100/len(str1))
    print(f"Common prefix end: {common_prefix[-100:]} ({percent_ok}%)",
          file=sys.stderr)


def test(java_code, check_hypothesis=False, fail_on_error=False, member=False,
         debug=False):
    # get the (domain-specific) java AST of the example Java code snippet
    if debug:
        print(f'Java code: \n{java_code}')
    if member:
        java_ast = javalang.parse.parse_member_declaration(java_code)
    else:
        java_ast = javalang.parse.parse(java_code)

    # convert the java AST into general-purpose ASDL AST used by tranX
    asdl_ast = java_ast_to_asdl_ast(java_ast, grammar)
    if debug:
        print(f'String representation of the ASDL AST:')
        print(f'{asdl_ast.to_string()}')
        print(f'Size of the AST: {asdl_ast.size}')
        print(f"ASDL AST: {asdl_ast.to_string()}", file=sys.stderr)

    # we can also convert the ASDL AST back into Java AST
    java_ast_reconstructed = asdl_ast_to_java_ast(asdl_ast, grammar)

    # get the surface code snippets from the original Python AST,
    # the reconstructed AST and the AST generated using actions
    # they should be the same
    src0 = removeComments(java_code)
    simp0 = simplify(src0)
    src1 = removeComments(jastor.to_source(java_ast))
    simp1 = simplify(src1)
    src2 = removeComments(jastor.to_source(java_ast_reconstructed))
    simp2 = simplify(src2)
    if check_hypothesis:
        #try:
        src3 = code_from_hyp(asdl_ast, debug)
        #except Exception as e:
            #print(f"{e}", file=sys.stderr)
            #return False
        src3 = removeComments(src3)
        simp3 = simplify(src3)
    if ((not (simp1 == simp2 == simp0)) or (
               (check_hypothesis and (simp3 != simp1)))):
        if simp0 != simp1:
            cprint(bcolors.BLUE,
                   f"))))))) Original Java code      :\n{src0}\n(((((((\n",
                   file=sys.stderr)
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Java AST                :\n{src1}\n"
                   f"{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            common_prefix(simp0, simp1)
        elif simp1 != simp2:
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Java AST                :\n{src1}"
                   f"\n{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            cprint(bcolors.GREEN,
                   f"]]]]]]] Java AST from ASDL      :\n{src2}\n[[[[[[[\n",
                   file=sys.stderr)
            common_prefix(simp1, simp2)
        elif check_hypothesis:
            cprint(bcolors.BLUE,
                   f"))))))) Original Java code      :\n{src0}\n(((((((\n",
                   file=sys.stderr)
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Java AST                :\n{src1}\n"
                   f"{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            cprint(bcolors.MAGENTA,
                   f">>>>>>> Java AST from hyp       :\n{src3}\n<<<<<<<\n",
                   file=sys.stderr)
            common_prefix(simp1, simp3)
        # if fail_on_error:
            # raise Exception("Test failed")
        # else:
        return False

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


def test_filepath(filepath: str,
                  check_hypothesis: bool = False,
                  fail_on_error=False,
                  member=False,
                  number: int = 0,
                  total: int = 0,
                  debug: bool = False):
    if filepath.endswith(".java"):
        cprint(bcolors.ENDC,
               f"\n−−−−−−−−−−\nTesting Java file {number:5d}/{total:5d} "
               f"{bcolors.MAGENTA}{filepath}",
               file=sys.stderr)
        with open(filepath, "r") as f:
            try:
                java = f.read()
                if not test(java, check_hypothesis=check_hypothesis,
                            fail_on_error=fail_on_error, member=member,
                            debug=debug):
                    cprint(bcolors.RED,
                           f"**Warn**{bcolors.ENDC} Test failed for "
                           f"file: {bcolors.MAGENTA}{filepath}",
                           file=sys.stderr)
                    # print(java, file=sys.stderr)
                    return False
                    # exit(1)
                else:
                    cprint(bcolors.GREEN,
                           f"Success for file: {bcolors.MAGENTA}{filepath}",
                           file=sys.stderr)
                    return True
            except UnicodeDecodeError:
                cprint(bcolors.RED,
                       f"Error: Cannot decode file as UTF-8. Ignoring: "
                       f"{filepath}", file=sys.stderr)
                return False
    else:
        return None


def stats(nb_ok: int, nb_ko: int):
    print(f"Succes: {nb_ok}/{nb_ok+nb_ko} ({int(nb_ok*100.0/(nb_ok+nb_ko))}%)")


def collect_files(dir: str) -> int:
    res = []
    for subdir, _, files in os.walk(dir):
        for filename in files:
            filepath = os.path.join(subdir, filename)
            res.append(filepath)
    return res


def load_exclusions(exclusions_file: str) -> List[str]:
    exclusions = []
    if exclusions_file:
        with open(exclusions_file, 'r') as ex:
            for exclusion in ex.readlines():
                exclusion = exclusion.strip()
                if exclusion and exclusion[0] != '#':
                    exclusions.append(exclusion)
    print(f"loaded exclusions are: {exclusions}", file=sys.stderr)
    return exclusions


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('-D', '--debug', default=False,
                            action='store_true',
                            help='If set, print additional debug messages.')
    arg_parser.add_argument('-c', '--check_hypothesis', default=False,
                            action='store_true',
                            help='If set, the hypothesis parse tree will be '
                            'tested.')
    arg_parser.add_argument('-F', '--fail_on_error', default=False,
                            action='store_true',
                            help=('If set, exit at first error. Otherwise, '
                                  'continue on next file.'))
    arg_parser.add_argument('-l', '--list', default=False,
                            action='store_true',
                            help='If set, use the hardcoded Java files list. '
                                  'Otherwise, walk the test directory for '
                                  'Java files')
    arg_parser.add_argument('-m', '--member', default=False,
                            action='store_true',
                            help='If set, consider the file content as the '
                                  'code of a member instead of a complete '
                                  'compilation unit.')
    arg_parser.add_argument('-x', '--exclude', action='append', default=[],
                            type=str,
                            help='Exclude the given file from being tested.')
    arg_parser.add_argument('-X', '--exclusions', type=str,
                            help='Read the exclusions from the given file.')
    arg_parser.add_argument('-f', '--file', action='append',
                            type=str,
                            help='Set the given file to be tested.')
    arg_parser.add_argument('-d', '--dir', default='test/',
                            type=str,
                            help='Set the files in the given dir to be tested.')
    args = arg_parser.parse_args()

    fail_on_error = args.fail_on_error
    check_hypothesis = args.check_hypothesis
    exclusions = args.exclude
    exclusions.extend(load_exclusions(args.exclusions))
    nb_ok = 0
    nb_ko = 0
    filepaths = [
        "test.java"
        # "test/test_sourcecode/com/github/javaparser/printer/JavaConcepts.java"
        # "test/Test.java",
        # "test/Final.java",
        # "test/ComplexGeneric.java",
        # "test/DiamondCall.java",
        # "test/AnnotationJavadoc.java",
        # "test/Implements.java",
        # "test/Wildcard.java",
        # "test/CallOnCast.java",
        # "test/java/com/github/javaparser/VisitorTest.java",
        # "test/test_sourcecode/com/github/javaparser/printer/JavaConcepts.java",
        # "test/test_sourcecode/javasymbolsolver_0_6_0/src/java-symbol-solver-core/com/github/javaparser/symbolsolver/SourceFileInfoExtractor.java",
        # "test/java/com/github/javaparser/SlowTest.java",
        # "test/java/com/github/javaparser/symbolsolver/Issue3038Test.java",
        # "test/test_sourcecode/javaparser_new_src/javaparser-generated-sources/com/github/javaparser/ASTParser.java",
        # "test/resources/issue1599/A.java",
        # "test/resources/issue241/TypeWithMemberType.java",
        # "test/resources/javassist_symbols/main_jar/src/com/github/javaparser/javasymbolsolver/javassist_symbols/main_jar/EnumInterfaceUserOwnJar.java",
        # "test/ParameterizedCall.java",
        # "test/test_sourcecode/javasymbolsolver_0_6_0/src/java-symbol-solver-core/com/github/javaparser/symbolsolver/javaparsermodel/DefaultVisitorAdapter.java",
        # "test/resources/issue2366/Test.java",
        # "test/resources/recursion-issue/Base.java",
        # "test/resources/issue1868/B.java",
        # "test/resources/issue1574/BlockComment.java",
        # "test/resources/issue1574/ClassWithOrphanComments.java",
        # "test/resources/TypeResolutionWithSameNameTest/02_ignore_static_non_type_import/another/MyEnum.java",
        # "test/resources/javassist_generics/javaparser/GenericClass.java",
        # "test/resources/com/github/javaparser/samples/JavaConcepts.java",
        # "test/test_sourcecode/javasymbolsolver_0_6_0/src/java-symbol-solver-core/com/github/javaparser/symbolsolver/javaparsermodel/TypeExtractor.java",
        # "test/test_sourcecode/javasymbolsolver_0_6_0/src/java-symbol-solver-core/com/github/javaparser/symbolsolver/javaparsermodel/declarations/JavaParserAnonymousClassDeclaration.java",
    ]
    test_num = 0

    files = None
    if args.list:
        files = filepaths
    elif args.file:
        files = args.file
    else:
        files = collect_files(args.dir)

    total = len(files)
    for filepath in files:
        test_num += 1
        if filepath not in exclusions:
            test_result = test_filepath(filepath,
                                        check_hypothesis=check_hypothesis,
                                        fail_on_error=fail_on_error,
                                        member=args.member,
                                        number=test_num,
                                        total=total,
                                        debug=args.debug)
            if test_result is not None:
                if test_result:
                    nb_ok = nb_ok + 1
                else:
                    nb_ko = nb_ko + 1
                    if fail_on_error:
                        stats(nb_ok, nb_ko)
                        exit(1)
    stats(nb_ok, nb_ko)
