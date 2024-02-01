import os
import openai
from config import GPT_MODEL
class Rephraser:
    def __init__(self, source_folder, openai_key):
        self.source_folder = source_folder
        self.openai_key = openai_key
        self.output_folder = os.path.join(os.path.dirname(source_folder), 'rephrased_transcript')
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def process_files(self):
        for filename in os.listdir(self.source_folder):
            self.process_file(filename)
            # if filename.endswith('_paragraphed.txt'):


    def process_file(self, filename):
        with open(os.path.join(self.source_folder, filename), 'r') as file:
            paragraphs = file.read().split('\n\n')

        rephrased_text = ''
        for paragraph in paragraphs:
            if paragraph.strip():
                rephrased_paragraph = self.rephrase_paragraph(paragraph)
                rephrased_text += rephrased_paragraph + '\n\n'

        # output_filename = filename.replace('_paragraphed.txt', '_rephrased.txt')
        with open(os.path.join(self.output_folder, filename), 'w') as file:
            file.write(rephrased_text)

    def rephrase_paragraph(self, paragraph):
        openai.api_key = self.openai_key
        prompt = ("Rewrite the paragraph while expanding on the topic, "
                  "remove any references to specific names and where examples "
                  "are given of popular figures, replace them with alternative "
                  "examples which communicate the same point. The goal is to "
                  "have the paragraph rewritten so that it avoids being too "
                  "similar to the source paragraph while maintaining the context. "
                  "Split the results into multiple paragraphs containing 3 sentences "
                  "without reducing the content:\n\n" + paragraph)
        response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user",
                 "content": f"{prompt}"}
            ]
        )
        print(paragraph)
        print(response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
