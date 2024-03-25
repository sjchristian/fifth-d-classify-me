import json
import os
from typing import List, Optional

import requests
from pydantic import BaseModel


class Options(BaseModel):
    max_words: int
    min_words: Optional[int] = 0
    max_sentences: Optional[int] = None
    language: str


class Url(BaseModel):
    url: str
    language: str


class UrlSummarySpec(BaseModel):
    options: Options
    urls: List[Url]


def load_json_file(path: str) -> list | dict:
    with open(path, "r") as file:
        data = json.load(file)
    return data


def form_request(url: str, options: Options) -> dict:
    return {
        "url": url,
        **options.model_dump(),
    }


def make_request(payload: dict) -> dict:
    url = os.environ.get("SERVER_URL", "http://localhost:8000")
    response = requests.post(f"{url}/summarise", json=payload)
    return response.json()


def run_single_case(case: UrlSummarySpec) -> float:
    """Runs a test case, measuring adherence to the given spec.

    Args:
        case (UrlSummarySpec): _description_

    Raises:
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_

    Returns:
        float: _description_
    """
    strict_mode = os.environ.get("STRICT_MODE", False)
    num_correct = 0
    for url in case.urls:
        request = form_request(url.url, case.options)
        output = make_request(request)

        source_language_correct = url.language == output["original_language"]
        target_language_correct = case.options.language == output["target_language"]
        word_count = len(output.get('summary').split())

        if strict_mode:
            if not source_language_correct:
                raise ValueError(f"Expected source language {url.language}, got {output['original_language']}")
            elif not target_language_correct:
                raise ValueError(f"Expected target language {case.options.language}, got {output['target_language']}")
            elif word_count > case.options.max_words:
                raise ValueError(f"Word count exceeded: {word_count} > {case.options.max_words}")                       

        if not source_language_correct or not target_language_correct:
            print("[INCORRECT] Languages not as expected")
        elif word_count > case.options.max_words:
            print(f"[INCORRECT] Word count exceeded: {word_count} > {case.options.max_words}")
        elif case.options.min_words and word_count < case.options.min_words:
            print(f"[INCORRECT] Word count less than required: {word_count} < {case.options.min_words}")
        else:
            print("[CORRECT] Languages and word count as expected")
            num_correct += 1

    return num_correct / len(case.urls)


def iterate_test_cases(test_case_paths: list[str]) -> float:
    adherences = []
    for test_case_path in test_case_paths:
        data = load_json_file(test_case_path)
        spec = UrlSummarySpec(**data)
        adherence = run_single_case(spec)
        print(f"{test_case_path} adherence: {adherence * 100:.2f}%")
        adherences.append(adherence)

    return sum(adherences) / len(adherences)


def main():
    """Evaluates the summarisation service using a set of test cases. Adherence is measured on the source/target 
    languages and word count
    """
    data_dir = "data"
    test_cases = [
        "case_urls_short_fr.json",
        "case_urls_long_de.json",
        "case_urls_short_mixed.json"
    ]
    test_cases = [os.path.join(data_dir, test_case) for test_case in test_cases]
    avg_acc = iterate_test_cases(test_cases)
    print(f"Average adherence: {avg_acc * 100:.2f}%")


# Example usage:
if __name__ == "__main__":
    main()
