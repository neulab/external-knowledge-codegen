# coding=utf-8

import argparse
import colorama
import os
import re
import sys
from clang.cindex import Index
from clang.cindex import TranslationUnit
from typing import List

import cppastor
import cpplang
from asdl.lang.cpp.cpp_transition_system import *
from asdl.hypothesis import *


# read in the grammar specification of Cpp SE8, defined in ASDL
asdl_text = open('cpp_asdl.simplified.txt').read()
grammar = ASDLGrammar.from_text(asdl_text)
# print(grammar, file=sys.stderr)

# initialize the Cpp transition parser
parser = CppTransitionSystem(grammar)


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
    string = re.sub(re.compile("^\\s*#.*\n"), "", string)
    string = re.sub(re.compile("\\s*#.*\n"), "", string)
    # remove all occurance streamed comments (/*COMMENT */) from string
    string = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", string)
    # remove all occurance singleline comments (//COMMENT\n ) from string
    string = re.sub(re.compile("//.*"), "", string)
    return string


def code_from_hyp(asdl_ast, debug=False):
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
            if action.production not in grammar[
                  hypothesis.frontier_field.type]:
                raise Exception(f"{bcolors.BLUE}{action.production}"
                                f"{bcolors.ENDC} should be in {bcolors.GREEN}"
                                f"{grammar[hypothesis.frontier_field.type]}"
                                f"{bcolors.ENDC}")
            assert action.production in grammar[hypothesis.frontier_field.type]

        if debug:
            p_t = (hypothesis.frontier_node.created_time
                   if hypothesis.frontier_node else -1)
            print(f't={t}, p_t={p_t}, Action={action}', file=sys.stderr)
        hypothesis.apply_action(action)
    cpp_ast = asdl_ast_to_cpp_ast(hypothesis.tree, grammar)
    source = cppastor.to_source(cpp_ast)
    return source


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


def test(cpp_code, check_hypothesis=False, fail_on_error=False, member=False,
         debug=False):
    # get the (domain-specific) cpp AST of the example Cpp code snippet
    if debug:
        print(f'Cpp code: \n{cpp_code}')
    if member:
        cpp_ast = cpplang.parse.parse_member_declaration(cpp_code)
    #else:
        #tu = TranslationUnit.from_source("test.cc", args=None,
                                         #unsaved_files=[("test.cc", cpp_code)],
                                         #options=0, index=None)
        #if not tu:
            #parser.error("unable to load input")
        #cpp_ast = tu.cursor
    else:
        cpp_ast = cpplang.parse.parse(cpp_code)

    # convert the cpp AST into general-purpose ASDL AST used by tranX
    asdl_ast = cpp_ast_to_asdl_ast(cpp_ast, grammar)
    if debug:
        print(f'String representation of the ASDL AST:')
        print(f'{asdl_ast.to_string()}')
        print(f'Size of the AST: {asdl_ast.size}')

    # we can also convert the ASDL AST back into Cpp AST
    cpp_ast_reconstructed = asdl_ast_to_cpp_ast(asdl_ast, grammar)
    if debug:
        print(f'String representation of the reconstructed CPP AST:')
        print(f'{cpp_ast_reconstructed}')
        #print(f'Size of the AST: {asdl_ast.size}')

    # get the surface code snippets from the original Python AST,
    # the reconstructed AST and the AST generated using actions
    # they should be the same
    src0 = removeComments(cpp_code)
    simp0 = simplify(src0)
    src1 = removeComments(cppastor.to_source(cpp_ast))
    simp1 = simplify(src1)
    src2 = removeComments(cppastor.to_source(cpp_ast_reconstructed))
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
                   f"))))))) Original Cpp code      :\n{src0}\n(((((((\n",
                   file=sys.stderr)
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Cpp AST                :\n{src1}\n"
                   f"{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            common_prefix(simp0, simp1)
        elif simp1 != simp2:
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Cpp AST                :\n{src1}"
                   f"\n{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            cprint(bcolors.GREEN,
                   f"]]]]]]] Cpp AST from ASDL      :\n{src2}\n[[[[[[[\n",
                   file=sys.stderr)
            common_prefix(simp1, simp2)
        elif check_hypothesis:
            cprint(bcolors.BLUE,
                   f"))))))) Original Cpp code      :\n{src0}\n(((((((\n",
                   file=sys.stderr)
            cprint(bcolors.CYAN,
                   f"}}}}}}}}}}}}}} Cpp AST                :\n{src1}\n"
                   f"{{{{{{{{{{{{{{\n",
                   file=sys.stderr)
            cprint(bcolors.MAGENTA,
                   f">>>>>>> Cpp AST from hyp       :\n{src3}\n<<<<<<<\n",
                   file=sys.stderr)
            common_prefix(simp1, simp3)
        # if fail_on_error:
            # raise Exception("Test failed")
        # else:
        return False

    else:
        return True


cpp_code = [
    """public class Test {}""",
    """package cpplang.brewtab.com; class Test {}""",
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
    """package cpplang.brewtab.com;
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
    if (filepath.endswith(".cpp") or filepath.endswith(".cc") or filepath.endswith(".h")
            or filepath.endswith(".hpp")):
        cprint(bcolors.ENDC,
               f"\n−−−−−−−−−−\nTesting Cpp file {number:5d}/{total:5d} "
               f"{bcolors.MAGENTA}{filepath}",
               file=sys.stderr)
        with open(filepath, "r") as f:
            try:
                cpp = f.read()
                if not test(cpp, check_hypothesis=check_hypothesis,
                            fail_on_error=fail_on_error, member=member,
                            debug=debug):
                    cprint(bcolors.RED,
                           f"**Warn**{bcolors.ENDC} Test failed for "
                           f"file: {bcolors.MAGENTA}{filepath}",
                           file=sys.stderr)
                    # print(cpp, file=sys.stderr)
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
    if nb_ok == nb_ko == 0:
        print(f"No tests, no stats")
        return None
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
                            help='If set, use the hardcoded Cpp files list. '
                                  'Otherwise, walk the test directory for '
                                  'Cpp files')
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
        "test.cpp"
        # "test/test_sourcecode/com/github/cppparser/printer/CppConcepts.cpp"
        # "test/Test.cpp",
        # "test/Final.cpp",
        # "test/ComplexGeneric.cpp",
        # "test/DiamondCall.cpp",
        # "test/AnnotationCppdoc.cpp",
        # "test/Implements.cpp",
        # "test/Wildcard.cpp",
        # "test/CallOnCast.cpp",
        # "test/cpp/com/github/cppparser/VisitorTest.cpp",
        # "test/test_sourcecode/com/github/cppparser/printer/CppConcepts.cpp",
        # "test/test_sourcecode/cppsymbolsolver_0_6_0/src/cpp-symbol-solver-core/com/github/cppparser/symbolsolver/SourceFileInfoExtractor.cpp",
        # "test/cpp/com/github/cppparser/SlowTest.cpp",
        # "test/cpp/com/github/cppparser/symbolsolver/Issue3038Test.cpp",
        # "test/test_sourcecode/cppparser_new_src/cppparser-generated-sources/com/github/cppparser/ASTParser.cpp",
        # "test/resources/issue1599/A.cpp",
        # "test/resources/issue241/TypeWithMemberType.cpp",
        # "test/resources/cppssist_symbols/main_jar/src/com/github/cppparser/cppsymbolsolver/cppssist_symbols/main_jar/EnumInterfaceUserOwnJar.cpp",
        # "test/ParameterizedCall.cpp",
        # "test/test_sourcecode/cppsymbolsolver_0_6_0/src/cpp-symbol-solver-core/com/github/cppparser/symbolsolver/cppparsermodel/DefaultVisitorAdapter.cpp",
        # "test/resources/issue2366/Test.cpp",
        # "test/resources/recursion-issue/Base.cpp",
        # "test/resources/issue1868/B.cpp",
        # "test/resources/issue1574/BlockComment.cpp",
        # "test/resources/issue1574/ClassWithOrphanComments.cpp",
        # "test/resources/TypeResolutionWithSameNameTest/02_ignore_static_non_type_import/another/MyEnum.cpp",
        # "test/resources/cppssist_generics/cppparser/GenericClass.cpp",
        # "test/resources/com/github/cppparser/samples/CppConcepts.cpp",
        # "test/test_sourcecode/cppsymbolsolver_0_6_0/src/cpp-symbol-solver-core/com/github/cppparser/symbolsolver/cppparsermodel/TypeExtractor.cpp",
        # "test/test_sourcecode/cppsymbolsolver_0_6_0/src/cpp-symbol-solver-core/com/github/cppparser/symbolsolver/cppparsermodel/declarations/CppParserAnonymousClassDeclaration.cpp",
    ]
    test_num = 0

    files = None
    if args.list:
        files = filepaths
    elif args.file:
        files = args.file
    else:
        files = collect_files(args.dir)
    print(files)
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
            else:
                nb_ko += 1
    stats(nb_ok, nb_ko)
