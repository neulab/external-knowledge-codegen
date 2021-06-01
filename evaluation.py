# coding=utf-8
from __future__ import print_function

import sys
import traceback
from tqdm import tqdm
from javalang.parse import parse_member_declaration
from javalang.parser import JavaSyntaxError


def decode(examples, model, args, verbose=False, **kwargs):
    # TODO: create decoder for each dataset

    if verbose:
        print('evaluating %d examples' % len(examples))

    was_training = model.training
    model.eval()

    decode_results = []
    count = 0
    for example in tqdm(examples, desc='Decoding', file=sys.stdout,
                        total=len(examples)):
        hyps = model.parse(example.src_sent, context=None,
                           beam_size=args.beam_size)
        decoded_hyps = []
        for hyp_id, hyp in enumerate(hyps):
            got_code = False
            try:
                code = model.transition_system.ast_to_surface_code(hyp.tree)
                try:
                    java_ast = parse_member_declaration(code)
                except JavaSyntaxError as e:
                    continue
                hyp.code = code
                got_code = True
                decoded_hyps.append(hyp)
            except Exception as e:
                if verbose:
                    print("Exception in converting tree to code:",
                          file=sys.stdout)
                    print('-' * 60, file=sys.stdout)
                    print(f'Example: {example.idx}', file=sys.stdout)
                    print(f'Intent: {" ".join(example.src_sent)}',
                          file=sys.stdout)
                    print('Target Code:', file=sys.stdout)
                    print(example.tgt_code, file=sys.stdout)
                    print(f'Hypothesis[{hyp_id}]:', file=sys.stdout)
                    print(hyp.tree.to_string(), file=sys.stdout)
                    if got_code:
                        print()
                        print(hyp.code)
                    traceback.print_exc(file=sys.stdout)
                    print('-' * 60, file=sys.stdout)

        count += 1

        decode_results.append(decoded_hyps)

    if was_training:
        model.train()

    return decode_results


def evaluate(examples, parser, evaluator, args, verbose=False,
             return_decode_result=False, eval_top_pred_only=False):
    decode_results = decode(examples, parser, args, verbose=verbose)
    # print(f"evaluation.evaluate decode_results: {decode_results}")
    eval_result = evaluator.evaluate_dataset(examples, decode_results,
                                             fast_mode=eval_top_pred_only,
                                             args=args)

    if return_decode_result:
        return eval_result, decode_results
    else:
        return eval_result
