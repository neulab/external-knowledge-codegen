import argparse
import json
import os
import pickle
import sys

import numpy as np

from asdl.hypothesis import *
from asdl.lang.java.java_transition_system import (java_ast_to_asdl_ast,
                                                   asdl_ast_to_java_ast,
                                                   JavaTransitionSystem)
from asdl.transition_system import *
from components.action_info import get_action_infos
from components.dataset import Example
from components.vocab import Vocab, VocabEntry
from datasets.concode.evaluator import ConcodeEvaluator
from datasets.concode.util import *
from asdl.lang.java import jastor
from javalang.parser import JavaSyntaxError

assert jastor.__version__ == '0.7.1'


def preprocess_concode_dataset(train_file, valid_file, test_file, grammar_file,
                               src_freq=3, code_freq=3, mined_data_file=None,
                               api_data_file=None, vocab_size=20000,
                               num_mined=0, out_dir='data/concode',
                               num_examples=0):
    np.random.seed(1234)

    asdl_text = open(grammar_file).read()
    grammar = ASDLGrammar.from_text(asdl_text)
    transition_system = JavaTransitionSystem(grammar)

    print('process gold training data...', file=sys.stderr)
    train_examples = preprocess_dataset(train_file, name='train',
                                        transition_system=transition_system,
                                        num_examples=num_examples)

    # held out 200 examples for development
    # TODO use the Concode valid corpus instead
    full_train_examples = train_examples[:]
    np.random.shuffle(train_examples)
    #dev_examples = train_examples[:200]
    #train_examples = train_examples[200:]

    dev_examples = preprocess_dataset(valid_file, name='dev',
                                      transition_system=transition_system,
                                      num_examples=num_examples)
    mined_examples = []
    api_examples = []
    if mined_data_file and num_mined > 0:
        print("use mined data: ", num_mined)
        print("from file: ", mined_data_file)
        mined_examples = preprocess_dataset(
          mined_data_file, name='mined', transition_system=transition_system,
          num_examples=num_mined)
        pickle.dump(mined_examples,
                    open(os.path.join(out_dir,
                                      'mined_{}.bin'.format(num_mined)), 'wb'))

    if api_data_file:
        print("use api docs from file: ", api_data_file)
        name = os.path.splitext(os.path.basename(api_data_file))[0]
        api_examples = preprocess_dataset(api_data_file, name='api',
                                          transition_system=transition_system,
                                          num_examples=num_examples)
        pickle.dump(api_examples,
                    open(os.path.join(out_dir, name + '.bin'), 'wb'))

    if mined_examples and api_examples:
        pickle.dump(mined_examples + api_examples,
                    open(os.path.join(out_dir,
                                      'pre_{}_{}.bin'.format(num_mined, name)),
                         'wb'))

    # combine to make vocab
    train_examples += mined_examples
    train_examples += api_examples
    print(f'{len(train_examples)} training instances', file=sys.stderr)
    print(f'{len(dev_examples)} dev instances', file=sys.stderr)

    print('process testing data...', flush=True)
    test_examples = preprocess_dataset(test_file, name='test',
                                       transition_system=transition_system)
    print(f'{len(test_examples)} testing instances', file=sys.stderr)

    src_vocab = VocabEntry.from_corpus([e.src_sent for e in train_examples],
                                       size=vocab_size,
                                       freq_cutoff=src_freq)
    #primitive_tokens = [map(lambda a: a.action.token,
                            #filter(lambda a: isinstance(a.action,
                                                        #GenTokenAction),
                                   #e.tgt_actions))
                        #for e in train_examples]
    primitive_tokens = [map(lambda a: a.token,
                            filter(lambda a: isinstance(a, GenTokenAction),
                                   e.tgt_actions))
                        for e in train_examples]
    primitive_vocab = VocabEntry.from_corpus(primitive_tokens, size=vocab_size,
                                             freq_cutoff=code_freq)

    # generate vocabulary for the code tokens!
    code_tokens = [transition_system.tokenize_code(e.tgt_code, mode='decoder')
                   for e in train_examples]

    code_vocab = VocabEntry.from_corpus(code_tokens, size=vocab_size,
                                        freq_cutoff=code_freq)

    vocab = Vocab(source=src_vocab, primitive=primitive_vocab, code=code_vocab)
    print('generated vocabulary %s' % repr(vocab), file=sys.stderr)

    action_lens = [len(e.tgt_actions) for e in train_examples]
    print('Max action len: %d' % max(action_lens), file=sys.stderr)
    print('Avg action len: %d' % np.average(action_lens), file=sys.stderr)
    print(f'Actions larger than 100: '
          f'{len(list(filter(lambda x: x > 100, action_lens)))}',
          file=sys.stderr)

    pickle.dump(train_examples,
                open(os.path.join(out_dir,
                                  'train.all_{}.bin'.format(num_mined)),
                     'wb'))
    pickle.dump(full_train_examples,
                open(os.path.join(out_dir, 'train.gold.full.bin'), 'wb'))
    pickle.dump(dev_examples, open(os.path.join(out_dir, 'dev.bin'), 'wb'))
    pickle.dump(test_examples, open(os.path.join(out_dir, 'test.bin'), 'wb'))
    if mined_examples and api_examples:
        vocab_name = (f'vocab.src_freq{src_freq}.code_freq{code_freq}'
                      f'.mined_{num_mined}.{name}.bin')
    elif mined_examples:
        vocab_name = (f'vocab.src_freq{src_freq}.code_freq{code_freq}'
                      f'.mined_{num_mined}.bin')
    elif api_examples:
        vocab_name = f'vocab.src_freq{src_freq}.code_freq{code_freq}'
        f'.{name}.bin'
    else:
        vocab_name = f'vocab.src_freq{src_freq}.code_freq{code_freq}.bin'
    pickle.dump(vocab, open(os.path.join(out_dir, vocab_name), 'wb'))


def preprocess_dataset(file_path, transition_system, name='train',
                       num_examples=None):
    try:
        dataset = json.load(open(file_path))
    except Exception as e:
        # TODO handle opening errors
        dataset = [json.loads(jline) for jline in open(file_path).readlines()]
    if num_examples:
        dataset = dataset[:num_examples]
    print(f"preprocess_dataset {file_path}, json is loaded", file=sys.stderr)
    examples = []
    evaluator = ConcodeEvaluator(transition_system)
    f = open(file_path + '.debug', 'w')
    skipped_list = []
    for i, example_json in enumerate(dataset):
        print(f"preprocess_dataset example n°{i+1}/{len(dataset)}", file=sys.stderr)
        try:
            example_dict = preprocess_example(example_json)
            snippet = example_dict['canonical_snippet']
            print(f"canonical_snippet:\n{snippet}",
                  file=sys.stderr)

            try:
                java_ast = javalang.parse.parse_member_declaration(snippet)
            except JavaSyntaxError as e:
                print(f"Java syntax error: {e.description}, at {e.at} "
                      f"in:\n{snippet}",
                      file=sys.stderr)
                raise
            canonical_code = jastor.to_source(java_ast).strip()
            print(f"canonical_code:\n{canonical_code}", file=sys.stderr)
            tgt_ast = java_ast_to_asdl_ast(java_ast, transition_system.grammar)
            tgt_actions = transition_system.get_actions(tgt_ast)

            ## sanity check
            #hyp = Hypothesis()
            #for t, action in enumerate(tgt_actions):
                #assert action.__class__ in transition_system.get_valid_continuation_types(hyp)
                #if isinstance(action, ApplyRuleAction):
                    #assert action.production in transition_system.get_valid_continuating_productions(hyp)
                ## p_t = -1
                ## f_t = None
                ## if hyp.frontier_node:
                ##     p_t = hyp.frontier_node.created_time
                ##     f_t = hyp.frontier_field.field.__repr__(plain=True)
                ##
                ## # print('\t[%d] %s, frontier field: %s, parent: %d' % (t, action, f_t, p_t))
                #hyp = hyp.clone_and_apply_action(action)

            #assert hyp.frontier_node is None and hyp.frontier_field is None
            #hyp.code = code_from_hyp = jastor.to_source(asdl_ast_to_java_ast(
                #hyp.tree, transition_system.grammar)).strip()
            ## print(code_from_hyp)
            ## print(canonical_code)
            #assert code_from_hyp == canonical_code

            #decanonicalized_code_from_hyp = decanonicalize_code(
              #code_from_hyp, example_dict['slot_map'])
            #assert compare_ast(ast.parse(example_json['snippet']),
                               #ast.parse(decanonicalized_code_from_hyp))
            #assert transition_system.compare_ast(
              #transition_system.surface_code_to_ast(decanonicalized_code_from_hyp),
              #transition_system.surface_code_to_ast(example_json['snippet']))

            #tgt_action_infos = get_action_infos(example_dict['intent_tokens'],
                                                #tgt_actions)
        #except (AssertionError, JavaSyntaxError, ValueError, OverflowError) as e:
        except (ValueError, OverflowError) as e:
            print(f"Intercpting exception: {e} in:\n{snippet}",
                  file=sys.stderr)
            skipped_list.append(example_json['question_id'])
            continue
        example = Example(idx=f'{i}-{example_json["question_id"]}',
                          src_sent=example_dict['intent_tokens'],
                          #tgt_actions=tgt_action_infos,
                          tgt_actions=tgt_actions,
                          tgt_code=canonical_code,
                          tgt_ast=tgt_ast,
                          meta=dict(example_dict=example_json,
                                    slot_map=example_dict['slot_map']))
        # assert evaluator.is_hyp_correct(example, hyp)

        examples.append(example)

        # log!
        f.write(f'Example: {example.idx}\n')
        if 'rewritten_intent' in example.meta['example_dict']:
            f.write(f"Original Utterance: "
                    f"{example.meta['example_dict']['rewritten_intent']}\n")
        else:
            f.write(f"Original Utterance: "
                    f"{example.meta['example_dict']['intent']}\n")
        f.write(f"Original Snippet: "
                f"{example.meta['example_dict']['snippet']}\n")
        f.write(f"\n")
        f.write(f"Utterance: {' '.join(example.src_sent)}\n")
        f.write(f"Snippet: {example.tgt_code}\n")
        f.write(
          f"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    f.close()
    print('Skipped due to exceptions: %d' % len(skipped_list), file=sys.stderr)
    return examples


def preprocess_example(example_json):
    """
    In Conala, this method allowed to replace occurrences of python code names
    in rewritten snippet and in code by a common representation. There is no
    such things in our Concode corpus currently but a lot of specificaly quoted
    names that conflict with this preprocessing. So currrently, just recopy
    intent and snippet.
    """

    intent = example_json['intent']
    slot_map = {}
    snippet = example_json['snippet']
    intent_tokens = tokenize_intent(intent)
    return {'canonical_intent': intent,
            'intent_tokens': intent_tokens,
            'slot_map': slot_map,
            'canonical_snippet': snippet}
    #intent = example_json['intent']
    #if 'rewritten_intent' in example_json:
        #rewritten_intent = example_json['rewritten_intent']
    #else:
        #rewritten_intent = None

    #if rewritten_intent is None:
        #rewritten_intent = intent
    #canonical_intent, slot_map = canonicalize_intent(rewritten_intent)
    #intent_tokens = tokenize_intent(canonical_intent)

    #snippet = example_json['snippet']
    #print(f"preprocess_example snippet={snippet}", file=sys.stderr)
    #try:
        #canonical_snippet = canonicalize_code(snippet, slot_map)
    #except JavaSyntaxError as e:
        #print(f"Java syntax error: {e.description}, at {e.at} in:\n{snippet}", file=sys.stderr)
        #raise
    #print(f"preprocess_example canonical_snippet={canonical_snippet}",
          #file=sys.stderr)
    #try:
        #decanonical_snippet = decanonicalize_code(canonical_snippet, slot_map)
    #except JavaSyntaxError as e:
        #print(f"Java syntax error: {e.description}, at {e.at} in:\n{snippet}",
              #file=sys.stderr)
        #raise
    #print(f"preprocess_example decanonical_snippet={decanonical_snippet}",
          #file=sys.stderr)

    #try:
        #reconstructed_snippet = jastor.to_source(
            #javalang.parse.parse_member_declaration(snippet)).strip()
    #except JavaSyntaxError as e:
        #print(f"Java syntax error: {e.description}, at {e.at} in:\n{snippet}",
              #file=sys.stderr)
        #raise
    #print(f"preprocess_example reconstructed_snippet={reconstructed_snippet}",
          #file=sys.stderr)
    #try:
        #reconstructed_decanonical_snippet = jastor.to_source(
            #javalang.parse.parse_member_declaration(

                #decanonical_snippet)).strip()
    #except JavaSyntaxError as e:
        #print(f"Java syntax error: {e.description}, at {e.at} in:\n{snippet}",
              #file=sys.stderr)
        #raise
    #print(f"preprocess_example reconstructed_decanonical_snippet="
          #f"{reconstructed_decanonical_snippet}",
          #file=sys.stderr)

    #assert compare_ast(
        #javalang.parse.parse_member_declaration(reconstructed_snippet),
        #javalang.parse.parse_member_declaration(reconstructed_decanonical_snippet))

    #return {'canonical_intent': canonical_intent,
            #'intent_tokens': intent_tokens,
            #'slot_map': slot_map,
            #'canonical_snippet': canonical_snippet}


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--train', type=str,
                            help='Path to train file',
                            default='data/concode/concode_train.json')
    arg_parser.add_argument('--valid', type=str,
                            help='Path to valid file',
                            default='data/concode/concode_valid.json')
    arg_parser.add_argument('--test', type=str,
                            help='Path to test file',
                            default='data/concode/concode_test.json')
    arg_parser.add_argument('--grammar', type=str,
                            help='Path to grammar file',
                            default='asdl/lang/java/java_asdl.simplified.txt')
    arg_parser.add_argument('--pretrain', type=str,
                            help='Path to pretrain file')
    arg_parser.add_argument('--out_dir', type=str, default='data/concode',
                            help='Path to output file')
    arg_parser.add_argument('--num_examples', type=int, default=0,
                            help='Max number of examples to use in any set')
    arg_parser.add_argument('--num_mined', type=int, default=0,
                            help='First k number from mined file')
    arg_parser.add_argument('--freq', type=int, default=3,
                            help='minimum frequency of tokens')
    arg_parser.add_argument('--vocabsize', type=int, default=20000,
                            help='First k number from pretrain file')
    arg_parser.add_argument('--include_api', type=str,
                            help='Path to apidocs file')
    args = arg_parser.parse_args()

    # the json files can converted from the concode format using the script
    # data/concode/concode2conala.py
    preprocess_concode_dataset(
      train_file=args.train,
      valid_file=args.valid,
      test_file=args.test,
      mined_data_file=args.pretrain,
      api_data_file=args.include_api,
      grammar_file=args.grammar,
      src_freq=args.freq,
      code_freq=args.freq,
      vocab_size=args.vocabsize,
      num_mined=args.num_mined,
      out_dir=args.out_dir,
      num_examples=args.num_examples)
