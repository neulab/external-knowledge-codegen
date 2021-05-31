import argparse
import json
import os
import pickle
import sys

import numpy as np

from asdl.hypothesis import *
from asdl.lang.py3.py3_transition_system import python_ast_to_asdl_ast, asdl_ast_to_python_ast, Python3TransitionSystem
from asdl.transition_system import *
from components.action_info import get_action_infos
from components.dataset import Example
from components.vocab import Vocab, VocabEntry
from datasets.conala.evaluator import ConalaEvaluator
from datasets.conala.util import *

assert astor.__version__ == '0.7.1'

def preprocess_conala_dataset(train_file,
                              test_file,
                              grammar_file,
                              src_freq=3,
                              code_freq=3,
                              rewritten=True,
                              mined_data_file=None,
                              api_data_file=None,
                              vocab_size=20000,
                              num_examples=0,
                              num_mined=0,
                              num_dev=200,
                              debug=False,
                              start_at=0,
                              out_dir='data/conala'):
    np.random.seed(1234)
    try:
        os.makedirs(out_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    asdl_text = open(grammar_file).read()
    grammar = ASDLGrammar.from_text(asdl_text)
    transition_system = Python3TransitionSystem(grammar)

    print('process gold training data...')
    train_examples = preprocess_dataset(train_file,
                                        name='train',
                                        transition_system=transition_system,
                                        num_examples=num_examples,
                                        debug=debug,
                                        start_at=start_at,
                                        rewritten=rewritten)

    # held out 200 examples for development
    full_train_examples = train_examples[:]
    np.random.shuffle(train_examples)
    dev_examples = train_examples[:num_dev]
    train_examples = train_examples[num_dev:]

    mined_examples = []
    api_examples = []
    if mined_data_file and num_mined > 0:
        print("use mined data: ", num_mined)
        print("from file: ", mined_data_file)
        mined_examples = preprocess_dataset(mined_data_file,
                                            name='mined',
                                            transition_system=transition_system,
                                            num_examples=num_mined,
                                            debug=debug,
                                            start_at=start_at,
                                            rewritten=rewritten)
        pickle.dump(mined_examples, open(os.path.join(out_dir, 'mined_{}.bin'.format(num_mined)), 'wb'))

    if api_data_file:
        print("use api docs from file: ", api_data_file)
        name = os.path.splitext(os.path.basename(api_data_file))[0]
        api_examples = preprocess_dataset(api_data_file, name='api',
                                          transition_system=transition_system,
                                          debug=debug,
                                          start_at=start_at,
                                          rewritten=rewritten)
        pickle.dump(api_examples, open(os.path.join(out_dir, name + '.bin'), 'wb'))

    if mined_examples and api_examples:
        pickle.dump(mined_examples + api_examples, open(os.path.join(out_dir, 'pre_{}_{}.bin'.format(num_mined, name)), 'wb'))

    # combine to make vocab
    train_examples += mined_examples
    train_examples += api_examples
    print(f'{len(train_examples)} training instances', file=sys.stderr)
    print(f'{len(dev_examples)} dev instances', file=sys.stderr)

    print('process testing data...')
    test_examples = preprocess_dataset(test_file, name='test',
                                       transition_system=transition_system,
                                       rewritten=rewritten)
    print(f'{len(test_examples)} testing instances', file=sys.stderr)

    src_vocab = VocabEntry.from_corpus([e.src_sent for e in train_examples], size=vocab_size,
                                       freq_cutoff=src_freq)
    primitive_tokens = [map(lambda a: a.action.token,
                            filter(lambda a: isinstance(a.action, GenTokenAction), e.tgt_actions))
                        for e in train_examples]
    primitive_vocab = VocabEntry.from_corpus(primitive_tokens, size=vocab_size, freq_cutoff=code_freq)

    # generate vocabulary for the code tokens!
    code_tokens = [transition_system.tokenize_code(e.tgt_code, mode='decoder') for e in train_examples]

    code_vocab = VocabEntry.from_corpus(code_tokens, size=vocab_size, freq_cutoff=code_freq)

    vocab = Vocab(source=src_vocab, primitive=primitive_vocab, code=code_vocab)
    print('generated vocabulary %s' % repr(vocab), file=sys.stderr)

    action_lens = [len(e.tgt_actions) for e in train_examples]
    print('Max action len: %d' % max(action_lens), file=sys.stderr)
    print('Avg action len: %d' % np.average(action_lens), file=sys.stderr)
    print('Actions larger than 100: %d' % len(list(filter(lambda x: x > 100, action_lens))), file=sys.stderr)

    pickle.dump(train_examples, open(os.path.join(out_dir, 'train.all_{}.bin'.format(num_mined)), 'wb'))
    pickle.dump(full_train_examples, open(os.path.join(out_dir, 'train.gold.full.bin'), 'wb'))
    pickle.dump(dev_examples, open(os.path.join(out_dir, 'dev.bin'), 'wb'))
    pickle.dump(test_examples, open(os.path.join(out_dir, 'test.bin'), 'wb'))
    if mined_examples and api_examples:
        vocab_name = 'vocab.src_freq%d.code_freq%d.mined_%s.%s.bin' % (src_freq, code_freq, num_mined, name)
    elif mined_examples:
        vocab_name = 'vocab.src_freq%d.code_freq%d.mined_%s.bin' % (src_freq, code_freq, num_mined)
    elif api_examples:
        vocab_name = 'vocab.src_freq%d.code_freq%d.%s.bin' % (src_freq, code_freq, name)
    else:
        vocab_name = 'vocab.src_freq%d.code_freq%d.bin' % (src_freq, code_freq)
    pickle.dump(vocab, open(os.path.join(out_dir, vocab_name), 'wb'))


def preprocess_dataset(file_path, transition_system, name='train',
                       num_examples=None, debug=False,
                       start_at=0,
                       rewritten=True):
    try:
        dataset = json.load(open(file_path))
    except Exception as e:
        # TODO handle opening errors
        dataset = [json.loads(jline) for jline in open(file_path).readlines()]
    if num_examples:
        dataset = dataset[:num_examples]
    examples = []
    evaluator = ConalaEvaluator(transition_system)
    f = open(file_path + '.debug', 'w')
    skipped_list = []
    for i, example_json in enumerate(dataset):
        if i < start_at:
            continue
        if debug:
            print(f"preprocess_dataset example n°{i+1}/{len(dataset)}",
                  end='\n', file=sys.stderr)
        else:
            print(f">>>>>>>> preprocess_dataset example n°{i+1}/{len(dataset)}",
                  end='\r', file=sys.stderr)
        try:
            example_dict = preprocess_example(example_json,
                                              rewritten=rewritten)

            snippet = example_dict['canonical_snippet']
            if debug:
                print(f"canonical_snippet:\n{snippet}", file=sys.stderr)

            lang_ast = ast.parse(snippet)
            canonical_code = astor.to_source(lang_ast).strip()
            if debug:
                print(f"canonical_code:\n{canonical_code}", file=sys.stderr)
            tgt_ast = python_ast_to_asdl_ast(lang_ast, transition_system.grammar)
            tgt_actions = transition_system.get_actions(tgt_ast)

            # sanity check
            hyp = Hypothesis()
            for t, action in enumerate(tgt_actions):
                valid_continuating_types = transition_system.get_valid_continuation_types(hyp)
                if action.__class__ not in valid_continuating_types:
                    print(f"Error: Valid continuation types are {valid_continuating_types} "
                          f"but current action class is {action.__class__}",
                          file=sys.stderr)
                    assert action.__class__ in valid_continuating_types
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
                    print(f'\t[{t}] {action}, frontier field: {f_t}, '
                          f'parent: {p_t}')
                hyp = hyp.clone_and_apply_action(action)

            assert hyp.frontier_node is None and hyp.frontier_field is None
            lang_ast = asdl_ast_to_python_ast(hyp.tree, transition_system.grammar)
            code_from_hyp = astor.to_source(lang_ast).strip()

            hyp.code = code_from_hyp
            if debug:
                print(f"code_from_hyp:\n{code_from_hyp}", file=sys.stderr)
            assert code_from_hyp == canonical_code

            decanonicalized_code_from_hyp = decanonicalize_code(code_from_hyp, example_dict['slot_map'])
            assert compare_ast(ast.parse(example_json['snippet']), ast.parse(decanonicalized_code_from_hyp))
            assert transition_system.compare_ast(transition_system.surface_code_to_ast(decanonicalized_code_from_hyp),
                                                 transition_system.surface_code_to_ast(example_json['snippet']))

            tgt_action_infos = get_action_infos(example_dict['intent_tokens'], tgt_actions)
        except (AssertionError, SyntaxError, ValueError, OverflowError) as e:
            skipped_list.append(example_json['question_id'])
            continue
        example = Example(idx=f'{i}-{example_json["question_id"]}',
                          src_sent=example_dict['intent_tokens'],
                          tgt_actions=tgt_action_infos,
                          tgt_code=canonical_code,
                          tgt_ast=tgt_ast,
                          meta=dict(example_dict=example_json,
                                    slot_map=example_dict['slot_map']))
        assert evaluator.is_hyp_correct(example, hyp)

        examples.append(example)

        # log!
        f.write(f'Example: {example.idx}\n')
        if rewritten and 'rewritten_intent' in example.meta['example_dict']:
            f.write(f"Original Utterance: {example.meta['example_dict']['rewritten_intent']}\n")
        else:
            f.write(f"Original Utterance: {example.meta['example_dict']['intent']}\n")
        f.write(f"Original Snippet: {example.meta['example_dict']['snippet']}\n")
        f.write(f"\n")
        f.write(f"Utterance: {' '.join(example.src_sent)}\n")
        f.write(f"Snippet: {example.tgt_code}\n")
        f.write(f"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    f.close()
    print('Skipped due to exceptions: %d' % len(skipped_list), file=sys.stderr)
    return examples


def preprocess_example(example_json, rewritten=True):
    intent = example_json['intent']
    if rewritten and 'rewritten_intent' in example_json:
        rewritten_intent = example_json['rewritten_intent']
    else:
        rewritten_intent = None

    if not rewritten or rewritten_intent is None:
        rewritten_intent = intent
    snippet = example_json['snippet']

    canonical_intent, slot_map = canonicalize_intent(rewritten_intent
                                                     if rewritten else intent)
    canonical_snippet = canonicalize_code(snippet, slot_map)
    intent_tokens = tokenize_intent(canonical_intent)
    decanonical_snippet = decanonicalize_code(canonical_snippet, slot_map)

    reconstructed_snippet = astor.to_source(ast.parse(snippet)).strip()
    reconstructed_decanonical_snippet = astor.to_source(ast.parse(decanonical_snippet)).strip()

    assert compare_ast(ast.parse(reconstructed_snippet), ast.parse(reconstructed_decanonical_snippet))

    return {'canonical_intent': canonical_intent,
            'intent_tokens': intent_tokens,
            'slot_map': slot_map,
            'canonical_snippet': canonical_snippet}


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    # ### General configuration ####
    arg_parser.add_argument('--train', type=str, help='Path to train file',
                            default='data/conala/conala-train.json')
    arg_parser.add_argument('--test', type=str, help='Path to test file',
                            default='data/conala/conala-test.json')
    arg_parser.add_argument('--mined', type=str, help='Path to mined file')
    arg_parser.add_argument('--grammar', type=str,
                            help='Path to language grammar',
                            default='asdl/lang/py3/py3_asdl.simplified.txt')
    arg_parser.add_argument('--out_dir', type=str, default='data/conala',
                            help='Path to output file')
    arg_parser.add_argument('--freq', type=int, default=3,
                            help='minimum frequency of tokens')
    arg_parser.add_argument('--vocabsize', type=int, default=20000,
                            help='First k number from pretrain file')
    arg_parser.add_argument('--include_api', type=str,
                            help='Path to apidocs file')
    arg_parser.add_argument('-r', '--no_rewritten', action='store_false',
                            help='If set, will not use the manually rewritten '
                                 'intents.')
    arg_parser.add_argument('--num_examples', type=int, default=0,
                            help='Max number of examples to use in any set')
    arg_parser.add_argument('--num_dev', type=int, default=200,
                            help='Max number of dev examples to use')
    arg_parser.add_argument('--num_mined', type=int, default=0,
                            help='First k number from mined file')
    args = arg_parser.parse_args()

    # the json files can be downloaded from http://conala-corpus.github.io
    preprocess_conala_dataset(train_file=args.train,
                              test_file=args.test,
                              mined_data_file=args.mined,
                              api_data_file=args.include_api,
                              grammar_file=args.grammar,
                              src_freq=args.freq, code_freq=args.freq,
                              vocab_size=args.vocabsize,
                              num_examples=args.num_examples,
                              num_mined=args.num_mined,
                              num_dev=args.num_dev,
                              out_dir=args.out_dir,
                              rewritten=args.no_rewritten)
