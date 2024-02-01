import os
import openai
from config import GPT_MODEL

class Paragrapher:
    def __init__(self, folder_path, openai_key):
        self.folder_path = folder_path
        self.openai_key = openai_key
        self.output_folder = os.path.join(folder_path, 'paragraphed_transcript')
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def process_files(self):
        for filename in os.listdir(self.folder_path):
            if filename.endswith('.txt'):
                self.process_file(filename)

    def process_file(self, filename):
        with open(os.path.join(self.folder_path, filename), 'r') as file:
            text = file.read()

        chunks = self.split_into_chunks(text, 3500)
        paragraphed_text = ''
        for chunk in chunks:
            paragraphs = self.get_paragraphs(chunk)
            paragraphed_text += paragraphs + '\n'

        # output_filename = filename.replace('.txt', '_paragraphed.txt')
        with open(os.path.join(self.output_folder, filename), 'w') as file:
            file.write(paragraphed_text)

    def split_into_chunks(self, text, max_length):
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            else:
                # Find the last period within the max_length range
                split_index = text.rfind('.', 0, max_length) + 1

                # If no period is found, use the max_length as the split index
                if split_index == 0:
                    split_index = max_length

                # Split the text and continue with the remaining part
                chunks.append(text[:split_index])
                text = text[split_index:]

        return chunks

    def get_paragraphs(self, text):
        openai.api_key = self.openai_key
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user",
                 "content": f"Break the following text into coherent paragraphs:\n\n{text}"}
            ]
        )
        print(text)
        print(response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
