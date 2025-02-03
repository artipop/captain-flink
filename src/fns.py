import time
from typing import Tuple

import numpy
import numpy as np
import torch
import torch.nn.functional as f
from pyflink.common import Types
from pyflink.datastream import MapFunction, KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ListStateDescriptor
from silero_vad import VADIterator

from models import vad_model, whisper_model


class SpeechToTextMapFunction(MapFunction):
    def __init__(self, sampling_rate=16000, sample_size=512):
        self.whisper_model = None
        self.buffer_state = None
        self.buffer_state_updated = False
        self.vad_iterator = None
        self.sampling_rate = sampling_rate
        self.sample_size = sample_size
        self.start_collect = time.time()
        self.end_collect = time.time()

    def open(self, runtime_context: RuntimeContext):
        self.vad_iterator = VADIterator(vad_model, sampling_rate=self.sampling_rate,
                                        min_silence_duration_ms=500)  # , speech_pad_ms=1000)
        self.whisper_model = whisper_model
        self.buffer_state = runtime_context.get_list_state(
            ListStateDescriptor("buffer", Types.LIST(Types.FLOAT()))
        )

    def map(self, value: Tuple[numpy.ndarray]):
        arr = value[0]  # (512,)  # Tuple[numpy.ndarray]
        chunk = torch.from_numpy(arr)
        if len(chunk) < self.sample_size:
            # we can pad the last chunk
            chunk = f.pad(chunk, (0, self.sample_size - chunk.size(dim=0)))
            # or we can signal that it's the end of the record and break the loop
            # return
        speech_dict = self.vad_iterator(chunk)
        if speech_dict:
            if 'start' in speech_dict:
                self.start_collect = time.time()
                self.buffer_state.add(chunk.numpy().tolist())
                self.buffer_state_updated = True
            elif 'end' in speech_dict:
                buffer = self.buffer_state.get()
                numpy_arrays = [np.array(arr, dtype=np.float32) for arr in buffer]
                np_arr = np.concatenate(numpy_arrays)
                self.end_collect = time.time()
                print(f"buf {self.end_collect - self.start_collect:.6f}")
                # print('send to whisper')
                start_time = time.time()
                segments = self.whisper_model.transcribe(np_arr, new_segment_callback=print)
                end_time = time.time()
                print(f"whisper {end_time - start_time:.6f}")
                # print(segments)
                self.buffer_state_updated = False
                self.buffer_state.clear()
                return segments
        if self.buffer_state_updated:
            self.buffer_state.add(chunk.numpy().tolist())
        chunk_duration = self.sample_size / self.sampling_rate
        time.sleep(chunk_duration)
        # print(chunk_duration)
        return ""  # transformed value


# noinspection DuplicatedCode
class SpeechToTextProcessFunction(KeyedProcessFunction):
    def __init__(self):
        self.whisper_model = None
        self.buffer_state = None
        self.buffer_state_updated = False
        self.vad_iterator = None
        self.sampling_rate = 16000
        self.sample_size = 512

    def open(self, runtime_context: RuntimeContext):
        self.vad_iterator = VADIterator(vad_model, sampling_rate=self.sampling_rate,
                                        min_silence_duration_ms=500)  # , speech_pad_ms=1000)
        self.whisper_model = whisper_model
        self.buffer_state = runtime_context.get_list_state(
            ListStateDescriptor("buffer", Types.LIST(Types.FLOAT()))
        )

    def process_element(self, value: Tuple[numpy.ndarray], ctx: 'KeyedProcessFunction.Context'):
        arr = value[0]  # (512,)  # Tuple[numpy.ndarray]
        chunk = torch.from_numpy(arr)
        if len(chunk) < self.sample_size:
            # we can pad the last chunk, or we can signal that it's the end of the record and break the loop
            chunk = f.pad(chunk, (0, self.sample_size - chunk.size(dim=0)))
            # or we can signal that it's the end of the record and break the loop
            # return
        speech_dict = self.vad_iterator(chunk)
        if speech_dict:
            if 'start' in speech_dict:
                self.buffer_state.add(arr)
                self.buffer_state_updated = True
            elif 'end' in speech_dict:
                buffer = self.buffer_state.get()
                numpy_arrays = [np.array(arr, dtype=np.float32) for arr in buffer]
                np_arr = np.concatenate(numpy_arrays)
                _ = self.whisper_model.transcribe(np_arr, new_segment_callback=print)
                self.buffer_state_updated = False
                self.buffer_state.clear()
        if self.buffer_state_updated:
            self.buffer_state.add(arr)
