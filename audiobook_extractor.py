import eyed3
import json

class AudiobookMetadataExtractor:
    def __init__(self, file_path):
        self.file_path = file_path

    @staticmethod
    def milliseconds_to_seconds(milliseconds):
        return int(milliseconds / 1000)

    def extract_metadata(self, is_milliseconds):
        audiofile = eyed3.load(self.file_path)

        # Basic metadata
        metadata = {
            "title": audiofile.tag.title,
            "artist": audiofile.tag.artist,
            "album": audiofile.tag.album,
            "album_artist": audiofile.tag.album_artist,
            "track_num": audiofile.tag.track_num,
            "genre": audiofile.tag.genre.name if audiofile.tag.genre else None,
            "chapters": []
        }

        # Extracting chapters
        if audiofile.tag is not None:
            for frame in audiofile.tag.frame_set.get(b'CHAP'):
                if is_milliseconds:
                    start_time = frame.times.start
                    end_time = frame.times.end
                    metadata["chapters"].append((start_time, end_time))
                else:
                    start_time = self.milliseconds_to_seconds(frame.times.start)
                    end_time = self.milliseconds_to_seconds(frame.times.end)
                    metadata["chapters"].append((start_time, end_time))
        return metadata

    def get_chapter_data(self, is_milliseconds):
        metadata = self.extract_metadata(is_milliseconds)
        return metadata.get("chapters", [])