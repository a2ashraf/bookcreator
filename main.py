import openai
import os

root_path = "/Users/Ahsan/Desktop/part1/"
openai.api_key = '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'
target_language = 'French'  # Change to your target language
output_path=f'{root_path}{target_language}/'.lower()
def translate_paragraph(paragraph, target_language):
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "user",
             "content": f"Translate the following English text to {target_language}: {paragraph}"}
        ]
    )

    print(paragraph)
    print(response.choices[0].message.content.strip())

    return response.choices[0].message.content.strip()


def translate_file(input_file_path, output_file_path, target_language):
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(input_file_path, 'r', encoding='utf-8') as file:
        paragraphs = file.read().split('\n\n')

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for paragraph in paragraphs:
            if paragraph.strip():
                translated_paragraph = translate_paragraph(paragraph, target_language)
                file.write(translated_paragraph + '\n\n')

for file_name in os.listdir(root_path):
    if file_name.endswith('.txt'):
        input_file = f'{root_path}{file_name}'
        print(input_file)
        output_file = f'{output_path}{os.path.splitext(file_name)[0]}_{target_language[:2].lower()}.txt'
        print(output_file)
        translate_file(input_file, output_file, target_language)

