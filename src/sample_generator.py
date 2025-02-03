import numpy as np
import soundfile as sf


def get_sample_rate(file_path):
    with sf.SoundFile(file_path, mode='r') as audio_file:
        return audio_file.samplerate


def read_audio_in_chunks(file_path, chunk_size):
    with sf.SoundFile(file_path, mode='r') as audio_file:
        print('channels: {}'.format(audio_file.channels))
        print('audio length in seconds: {}'.format(audio_file.frames / audio_file.samplerate))
        while True:
            data = audio_file.read(chunk_size, dtype='float32')
            if np.ndim(data) > 1:
                data = np.mean(data, axis=1)
            if len(data) == 0:
                break
            yield data
