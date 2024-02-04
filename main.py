import openai
import os
from pydub import AudioSegment
from audio_splitter import AudioSplitter
from audiobook_extractor import AudiobookMetadataExtractor
from google.cloud import storage, speech
from paragrapher import Paragrapher
from rephraser import Rephraser
from config import OPENAI_API_KEY
from config import GPT_MODEL
from config import GCS_PROJECT
from config import GCS_BUCKET
from elevenlabs import generate, play

target_language = 'French'  # Change to your target language
openai.api_key = OPENAI_API_KEY
google_cloud_project = GCS_PROJECT

source_file = "prayer_art_of_believing.mp3"
base_path = "/Users/Ahsan/Documents/WORK/audiobooks_project/"
source_path = f"{base_path}source_book/"
split_files_path = f"{base_path}output/"
audio = AudioSegment.from_file(f"{source_path}{source_file}")
gcs_bucket_name = GCS_BUCKET  # Replace with your GCS bucket name
transcribed_text_path = f'{base_path}transcribed_segments/'
output_path = f'{transcribed_text_path}{target_language}/'.lower()
gpt_model = GPT_MODEL
gcs_blob_name = "extracted_audio.mp3"  # Placeholder name of file in GCS bucket

# Step 5 - With the rewritten files, it then translates it
def translate_paragraph(paragraph, target_language):
    response = openai.chat.completions.create(
        model=gpt_model,
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

def translate_to_language(target_language):
    for file_name in os.listdir(transcribed_text_path):
        if file_name.endswith('.txt'):
            input_file = f'{transcribed_text_path}rephrased_transcript/{file_name}'
            print(input_file)
            output_file = f'{output_path}{os.path.splitext(file_name)[0]}_{target_language[:2].lower()}.txt'
            print(output_file)
            translate_file(input_file, output_file, target_language)


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
    audio.export(output_audio_file, format="mp3")


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


# Step 6 - create the audio book version of it.

# start - step 1 - splits one audiobook into chapter segments
def split_audiobook_into_audio_segments_by_chapters():
    audiobook_path = os.path.join(source_path, "prayer_art_of_believing.mp3")
    chapters = get_chapters_from_file(audiobook_path)
    split_input_file_into_segments(chapters)


# step 2: get transcripts for each file - done
def get_transcripts_from_audio():
    for i, segment_file_name in enumerate(sorted(os.listdir(split_files_path))):
        if segment_file_name.endswith(".wav"):
            segment_file_path = os.path.join(split_files_path, segment_file_name)
            upload_audio_to_gcs(segment_file_path, gcs_bucket_name, gcs_blob_name)

            gcs_uri = f"gs://{gcs_bucket_name}/{gcs_blob_name}"
            transcribed_text = transcribe_long_audio_with_google_cloud(gcs_uri)

            transcript_file = os.path.join(transcribed_text_path, f"transcript_{i}.txt")
            with open(transcript_file, "w") as file:
                file.write(transcribed_text)


# Step 3 - With the list of text files, it splits it up into paragraphs done
def paragraphize_text():
    openai_key = OPENAI_API_KEY
    paragrapher = Paragrapher(transcribed_text_path, openai_key)
    paragrapher.process_files()


# Step 4 - With each paragraph it rewrites it - done
def rewrite_each_paragraph():
    source_folder = os.path.join(transcribed_text_path, "paragraphed_transcript")
    openai_key = OPENAI_API_KEY
    rephraser = Rephraser(source_folder, openai_key)
    rephraser.process_files()

# split_audiobook_into_audio_segments_by_chapters()   #step 1: Take audiobook and create chapters from it
# get_transcripts_from_audio()                        #step 2: Get the text from the audiobook
# paragraphize_text()                                 #step 3: create paragraphs from the long form text obtained in step 2
# rewrite_each_paragraph()                            #step 4: Rewrite all paragraphs using openai
# translate_to_language(target_language)              #step 5: Translate to a desired language

