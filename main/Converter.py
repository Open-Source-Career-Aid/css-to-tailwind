# enum
from enum import Enum
from llama_index.llms.openai import OpenAI
import re
import os
import json
from PROMPTS import CSS_TO_TAILWIND_CONVERTER
from dotenv import load_dotenv
import tqdm
load_dotenv()

def extract_css_classes(css_text):
    pattern = r"(\.[-_a-zA-Z0-9]+\s*\{[^}]*\})"
    matches = re.findall(pattern, css_text, re.MULTILINE | re.DOTALL)
    return matches

class Format(Enum):
    CSS = 1

class Converter:
    def __init__(self, 
                format: Format,
                llm: OpenAI = OpenAI(model="gpt-3.5-turbo")):
        self.format = format
        self.llm = llm

    def convert(self, data: str) -> tuple:
        if self.format == Format.CSS:
            prompt = CSS_TO_TAILWIND_CONVERTER.replace("<<css>>", data)
            return tuple(self.llm.complete(prompt).text.split("\n"))
        return None
    
class ConverterRunner:
    def __init__(self,
                format: Format):
        self.format = format
        self.converter = Converter(format)
        self.converted_data = {}

    def _break_data_into_chunks(self, data: str) -> list:
        if self.format == Format.CSS:
            return extract_css_classes(data)
    
    def run(self, data: str) -> str:
        chunks = self._break_data_into_chunks(data)
        for chunk in tqdm.tqdm(chunks):
            if self.format == Format.CSS:
                _temp = self.converter.convert(chunk)
                self.converted_data[_temp[0]] = _temp[1]
        return self.converted_data
    
class FileIterator:
    def __init__(self, 
                folder_path: str):
        self.folder_path = folder_path
        self.csspairs = {}

    def _read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            return file.read()
        
    def convert_all_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in tqdm.tqdm(files):
                if file.endswith(".css"):
                    file_path = os.path.join(root, file)
                    self.csspairs[file] = ConverterRunner(Format.CSS).run(self._read_file(file_path))
        # export to json
        with open("converted.json", "w") as file:
            json.dump(self.csspairs, file, indent=4)
        return self.csspairs

if __name__ == "__main__":
    folder_path = "data/"
    FileIterator(folder_path).convert_all_files()