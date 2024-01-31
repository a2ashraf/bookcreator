from pydub import AudioSegment

class AudioSplitter:
    def __init__(self, source_path, source_file, split_files_path):
        self.source_path = source_path
        self.source_file = source_file
        self.split_files_path = split_files_path
        self.audio = None
        self.chapters = []

    def load_audio(self):
        self.audio = AudioSegment.from_file(f"{self.source_path}{self.source_file}")

    def set_chapters(self, chapters):
        self.chapters = chapters

    def split_and_save(self):
        if self.audio is None:
            raise Exception("Audio file not loaded. Call load_audio() first.")

        if not self.chapters:
            raise Exception("Chapters not set. Call set_chapters() first.")

        for i, (start, end) in enumerate(self.chapters):
            segment = self.audio[start:end]
            segment.export(f"{self.split_files_path}segment_{i}.wav", format="wav")
