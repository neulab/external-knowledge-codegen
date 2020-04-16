# coding=utf-8


class ExampleProcessor(object):
    """
    Process a raw input utterance using domain-specific procedures (e.g., stemming),
    and post-process a generated hypothesis to the final form
    """
    def pre_process_utterance(self, utterance):
        raise NotImplementedError

    def post_process_hypothesis(self, hyp, meta_info, **kwargs):
        raise NotImplementedError


def get_example_processor_cls(dataset):
    if dataset == 'conala':
        from datasets.conala.example_processor import ConalaExampleProcessor
        return ConalaExampleProcessor
    else:
        raise RuntimeError()
