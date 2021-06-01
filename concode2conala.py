#!/usr/bin/env python3

import json

import argparse

# concode format:
#[
    #{
        #"nl": [
            #"Generate",
            #"mappings",
            #"for",
            #"each",
            # …
        #],
        #"code": [
            #"void",
            #"function",
            #"(",
            #"ScriptOrFnNode",
            #"arg0",
            # …
        #],
        #"varNames": [
            #"parent",
            #"isParsed",
            # …
        #],
        #"varTypes": [
            #"Container",
            #"boolean",
            # …
        #],
        #"methodNames": [
            #"getParent",
            #"getUserType",
            # …
        #],
        #"methodReturns": [
            #"Container",
            #"byte[]",
            # …
        #],


# conala format
#[
  #{
    #"intent": "How to convert a list of multiple integers into a single integer?",
    #"rewritten_intent": "Concatenate elements of a list 'x' of multiple integers to a single integer",
    #"snippet": "sum(d * 10 ** i for i, d in enumerate(x[::-1]))",
    #"question_id": 41067960
  #},
  #{
    #"intent": "How to convert a list of multiple integers into a single integer?",
    #"rewritten_intent": "convert a list of integers into a single integer",
    #"snippet": "r = int(''.join(map(str, x)))",
    #"question_id": 41067960
  #},


def text_from_concode_nl(concode_nl: list):
    return " ".join(concode_nl)


def code_from_concode_nl(concode_code: list):
    return " ".join(concode_code)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('--src', type=str,
                            required=True,
                            help='Path to the source file in concode format')
    arg_parser.add_argument('--tgt', type=str,
                            required=True,
                            help='Path to the target file in conala format')
    arg_parser.add_argument('--fields', action="store_true",
                            help='Add fields to the intent')
    arg_parser.add_argument('--methods', action="store_true",
                            help='Add methods to the intent')

    args = arg_parser.parse_args()

    conala = []
    id = 0
    with open(args.src, "r") as concode_file:
        concode = json.load(concode_file)
        with open(args.tgt, "w") as conala_file:
            for concode_example in concode:
                id += 1
                conala_example = {}
                intent = text_from_concode_nl(concode_example["nl"])
                # "concode_field_sep","concode_elem_sep","concode_func_sep"
                if args.fields and concode_example["varTypes"]:
                    intent += " concode_field_sep " + " concode_field_sep ".join(
                      [' concode_elem_sep '.join(el)
                       for el in zip(concode_example["varTypes"],
                                     concode_example["varNames"])])
                if args.methods:
                    intent += " concode_func_sep " + " concode_func_sep ".join(
                      [' concode_elem_sep '.join(el)
                       for el in zip(concode_example["methodReturns"],
                                     concode_example["methodNames"])])

                snippet = code_from_concode_nl(concode_example["code"])
                conala_example["question_id"] = id
                conala_example["intent"] = intent
                conala_example["snippet"] = snippet
                conala.append(conala_example)
            conala_file.write(json.dumps(conala, indent=4))
