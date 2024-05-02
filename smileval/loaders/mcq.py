from .base import Experiment, ExperimentMetadata, ExperimentContext, ExperimentOutcome, Loader

import random
import csv
import json

from .templates import mcq as mcq_templates

default_formatting = {
    "presentation_selection_type": mcq_templates.PRESENTATION_SELECTION_TYPES["capital_alphabet"],
    "question_answer_format": "{}\n{}",
    "sep": mcq_templates.SEP_PARENTHESES
}

class MCQQuestionAskExperiment(Experiment):
    def __init__(self, question: str, answer_choices: list[str], correct_answers: list[str] = [], formatting = default_formatting, points: int = 1, use_shuffle = False):
        self.question = question
        self.answer_choices = answer_choices
        self.correct_answers = correct_answers
        # prob won't use this in case of shuffling
        # print(self.correct_answers, answer_choices)
        self.correct_indexes = [
            self.answer_choices.index(answer) for answer in correct_answers
        ]
        self.metadata = ExperimentMetadata(None, points)
        # give one sample interaction chain to help weaker LLMs
        self.give_example = False
        self.shuffle = use_shuffle
        self.max_points = points
        self.formatting = formatting

    async def execute(self, context: ExperimentContext) -> ExperimentOutcome:
        outcome = ExperimentOutcome(self.get_metadata(), context)

        answer_choices = self.answer_choices[:]

        if self.shuffle:
            random.shuffle(answer_choices)

        prompt = self.formatting["question_answer_format"].format(self.question,mcq_templates.format_choices(answer_choices, self.formatting["presentation_selection_type"]["choices"], self.formatting["sep"]))

        system_prompt = default_formatting["presentation_selection_type"]["system"]

        answer = await context.generate(prompt, system_prompt)

        symbols = self.formatting["presentation_selection_type"]["choices"]

        if answer in symbols:
            chosen_index = symbols.index(answer)
            if chosen_index < len(answer_choices):
                answer_text = answer_choices[chosen_index]
                if answer_text in self.correct_answers:
                    outcome.set_score_off_bool(True)

        return outcome

    def get_metadata(self) -> ExperimentMetadata:
        return self.metadata

class MCQQuestionLoader(Loader):
    def __init__(self, input_file_path: str, formatting_config: dict = default_formatting, mode: str | None = None, skip_first_item = False, use_shuffle = False):
        self.input_file_path = input_file_path
        self.input_file = open(input_file_path, "r")
        self.formatting_config = formatting_config
        self.mode = mode
        if self.mode == None:
            if self.input_file_path.endswith(".csv"):
                self.mode = "csv"
                self.proxy_reader = csv.reader(self.input_file)
                if skip_first_item:
                    _ = next(self.proxy_reader)
        self.use_shuffle = use_shuffle

    def __next__(self) -> Experiment:
        try:
            if self.mode == "csv":
                line = next(self.proxy_reader)
                answer = line.pop()
                question = line.pop(0)
                answer_choices = line[:]
                return MCQQuestionAskExperiment(question, answer_choices, correct_answers = [answer], formatting = self.formatting_config, use_shuffle = self.use_shuffle)
        except StopIteration:
            self.input_file.close()
            raise StopIteration()