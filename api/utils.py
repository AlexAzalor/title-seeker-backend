from datetime import datetime
import re
from typing import List
import filetype
from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
from app import schema as s

from app.logger import log


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def mark_as_deleted():
    current_timestamp = datetime.now().strftime("%y-%m-%d_%H:%M:%S:%f")

    return f"deleted-{current_timestamp}"


def get_error_message(lang: s.Language, text_uk: str, text_en: str) -> str:
    return text_uk if lang == s.Language.UK else text_en


def extract_values(input_string: List[str]) -> List[List[int]]:
    values_list: List[List[int]] = []

    for value in input_string:
        pattern = re.compile(r".*?\(([\d,]+)\)")
        match = pattern.match(value)

        if match:
            numbers_str = match.group(1)
            numbers_list = [int(num) for num in numbers_str.split(",")]
            values_list.append(numbers_list)
    return values_list


def extract_word(input_string: List[str]) -> List[str]:
    words_list: List[str] = []

    for word in input_string:
        pattern = re.compile(r"(.*?)\([\d,]+\)")
        match = pattern.match(word)

        if match:
            word = match.group(1).strip()
            words_list.append(word)
        else:
            words_list.append(word.strip())
    return words_list
