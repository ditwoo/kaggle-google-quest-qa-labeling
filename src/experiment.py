import pickle
from collections import OrderedDict

import numpy as np
import scipy.sparse as sp
from catalyst.dl import ConfigExperiment
from sklearn.model_selection import train_test_split

from .datasets import FieldsDataset, SequencesCollator
from .datasets.augmentations import CombineSeqs, SeqElementsShuffler, Compose
# from .datasets import VectorDataset


class Experiment(ConfigExperiment):
    def get_datasets(
        self,
        stage: str,
        train_pickle: str,
        valid_pickle: str,
        seq_percentile: int = 75,
        **kwargs,
    ):  
        text_cols = ["question_title", "question_body", "answer"]
        targets = [
            "question_asker_intent_understanding", 
            "question_body_critical",
            "question_conversational",
            "question_expect_short_answer",
            "question_fact_seeking",
            "question_has_commonly_accepted_answer",
            "question_interestingness_others",
            "question_interestingness_self",
            "question_multi_intent",
            "question_not_really_a_question",
            "question_opinion_seeking",
            "question_type_choice",
            "question_type_compare",
            "question_type_consequence",
            "question_type_definition",
            "question_type_entity",
            "question_type_instructions",
            "question_type_procedure",
            "question_type_reason_explanation",
            "question_type_spelling",
            "question_well_written",
            "answer_helpful",
            "answer_level_of_information",
            "answer_plausible",
            "answer_relevance",
            "answer_satisfaction",
            "answer_type_instructions",
            "answer_type_procedure",
            "answer_type_reason_explanation",
            "answer_well_written",
        ]
        
        with open(train_pickle, "rb") as f:
            df = pickle.load(f)

        max_len = max(df.apply(lambda r: sum([len(r[c]) for c in text_cols]), axis=1))
        print(f"Train size - {df.shape[0]}")
        print(f"Train max len - {max_len}", flush=True)

        if stage != "finetune":
            augs = Compose(
                SeqElementsShuffler("question_title", p=0.3),
                SeqElementsShuffler("question_body", p=0.3),
                SeqElementsShuffler("answer", p=0.3),
                CombineSeqs(text_cols, "seq", glue_token=0),
            )
        else:
            augs = CombineSeqs(text_cols, "seq", glue_token=0)

        datasets = OrderedDict()
        datasets["train"] = dict(
            dataset=FieldsDataset(df, text_cols, targets, augs),
            collate_fn=SequencesCollator(max_len=max_len, percentile=seq_percentile),
        )

        with open(valid_pickle, "rb") as f:
            df = pickle.load(f)

        max_len = max(df.apply(lambda r: sum([len(r[c]) for c in text_cols]), axis=1))
        print(f"Valid size - {df.shape[0]}")
        print(f"Valid max len - {max_len}", flush=True)

        datasets["valid"] = dict(
            dataset=FieldsDataset(df, text_cols, targets, CombineSeqs(text_cols, "seq", glue_token=0)),
            collate_fn=SequencesCollator(max_len=max_len, percentile=seq_percentile),
        )
        return datasets
