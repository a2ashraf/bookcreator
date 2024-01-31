import openai
import os
from pydub import AudioSegment
from audio_splitter import AudioSplitter
from audiobook_extractor import AudiobookMetadataExtractor
from google.cloud import storage, speech

root_path = "/Users/Ahsan/Desktop/part1/"
openai.api_key = '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'
target_language = 'French'  # Change to your target language
output_path = f'{root_path}{target_language}/'.lower()

source_path = "/Users/Ahsan/Documents/WORK/audiobooks_project/source_book/"
source_file = "prayer_art_of_believing.mp3"
split_files_path = "/Users/Ahsan/Documents/WORK/audiobooks_project/output/"
base_path = "/Users/Ahsan/Documents/WORK/audiobooks_project/"
audio = AudioSegment.from_file(f"{source_path}{source_file}")
gcs_bucket_name = "ahsanpodcast"  # Replace with your GCS bucket name
gcs_blob_name = "extracted_audio.mp3"  # Replace with the desired GCS blob name
transcribed_text_path = f'/Users/Ahsan/Documents/WORK/audiobooks_project/transcribed_segments/'
google_cloud_project = "melodic-zoo-242102"


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


# for file_name in os.listdir(root_path):
#     if file_name.endswith('.txt'):
#         input_file = f'{root_path}{file_name}'
#         print(input_file)
#         output_file = f'{output_path}{os.path.splitext(file_name)[0]}_{target_language[:2].lower()}.txt'
#         print(output_file)
#         translate_file(input_file, output_file, target_language)

# Step 1  - takes file, splits it, - done
def get_chapters_from_file(audiobook_path):
    extractor = AudiobookMetadataExtractor(audiobook_path)
    chapters = extractor.get_chapter_data(is_milliseconds=True)
    print("chapters =", chapters)
    return chapters


def split_input_file_into_segments(chapters_by_time):
    splitter = AudioSplitter(source_path, source_file, split_files_path)
    splitter.load_audio()
    splitter.set_chapters(chapters_by_time)
    splitter.split_and_save()


# Step 2 - sends each split file to google to get text - todo

def upload_audio_to_gcs(local_audio_file, gcs_bucket_name, gcs_blob_name):
    # Convert the original file to mono and save it
    mono_audio = "mono_audio/"
    base_mono_path = os.path.join(base_path, mono_audio)
    os.makedirs(os.path.dirname(base_mono_path), exist_ok=True)

    mono_audio_file = f"{base_mono_path}mono_{os.path.basename(local_audio_file)}"
    convert_to_mono(local_audio_file, mono_audio_file)
    # Initialize a GCS client
    storage_client = storage.Client(google_cloud_project)

    # Get the GCS bucket
    bucket = storage_client.bucket(gcs_bucket_name)

    # Upload the converted mono audio file to GCS
    blob = bucket.blob(gcs_blob_name)
    blob.upload_from_filename(mono_audio_file)


def convert_to_mono(input_audio_file, output_audio_file):
    audio = AudioSegment.from_wav(input_audio_file)
    audio = audio.set_channels(1)  # Convert to mono (single channel)
    audio.export(output_audio_file, format="wav")


def transcribe_long_audio_with_google_cloud(gcs_uri):
    # Initialize a Speech-to-Text client
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=22050,
        language_code="en-US",
    )

    # Use the asynchronous LongRunningRecognize method
    operation = client.long_running_recognize(config=config, audio=audio)

    # Wait for the operation to complete
    response = operation.result()
    transcribed_text = ""
    for result in response.results:
        transcribed_text += result.alternatives[0].transcript + " "
    return transcribed_text.strip()


# Step 3 - With the list of text files, it splits it up into paragraphs
# Step 4 - With each paragraph it rewrites it
# Step 5 - With the rewritten files, it then translates it

# start - step 1 - done
# audiobook_path = os.path.join(source_path, "prayer_art_of_believing.mp3")
# chapters = get_chapters_from_file(audiobook_path)
# split_input_file_into_segments(chapters)

# step 2: get transcripts for each file - done
# for i, segment_file_name in enumerate(sorted(os.listdir(split_files_path))):
#     if segment_file_name.endswith(".wav"):
#         segment_file_path = os.path.join(split_files_path, segment_file_name)
#         upload_audio_to_gcs(segment_file_path, gcs_bucket_name, gcs_blob_name)
#
#         gcs_uri = f"gs://{gcs_bucket_name}/{gcs_blob_name}"
#         transcribed_text = transcribe_long_audio_with_google_cloud(gcs_uri)
#
#         transcript_file = os.path.join(transcribed_text_path, f"transcript_{i}.txt")
#         with open(transcript_file, "w") as file:
#             file.write(transcribed_text)

