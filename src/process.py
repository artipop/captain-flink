import argparse
import logging
import sys
import time

from pyflink.common import Encoder
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig, RollingPolicy

from fns import SpeechToTextMapFunction
from sample_generator import read_audio_in_chunks, get_sample_rate


def audio_processing(input_path: str, output_path: str):
    """
    Main function for processing an audio file.
    The data source for the DataStream (`ds`) can be modified to use a different input.
    Additionally, chained method calls on the `ds` object can be adjusted to alter the overall processing behavior.
    :param input_path:
    :param output_path:
    :return:
    """
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_runtime_mode(RuntimeExecutionMode.BATCH)
    env.set_parallelism(1)

    sample_rate = get_sample_rate(input_path)
    if sample_rate != 16000 and sample_rate != 8000:
        raise Exception("Sample rate must be 8000 or 16000, but is {}".format(sample_rate))
    chunk_size = 256 if sample_rate == 8000 else 512
    ext = input_path[-3:]
    if ext != "wav":
        raise Exception("Unsupported file type")
    generator = read_audio_in_chunks(input_path, chunk_size)
    ds = env.from_collection(
        [(chunk,) for chunk in generator],
    )
    (ds
     .key_by(lambda x: 0)
     .map(SpeechToTextMapFunction(sampling_rate=sample_rate, sample_size=chunk_size))
     )

    # send processing result to output file or stdout
    if output_path is not None:
        ds.sink_to(
            sink=FileSink.for_row_format(
                base_path=output_path,
                encoder=Encoder.simple_string_encoder())
            .with_output_file_config(
                OutputFileConfig.builder()
                .with_part_prefix("prefix")
                .with_part_suffix(f".{ext}")
                .build())
            .with_rolling_policy(RollingPolicy.default_rolling_policy())
            .build()
        )
    else:
        print("Printing result to stdout. Use --output to specify output path.")
        # ds.print()  # commented, cause it will print a lot of the intermediate results

    start_time = time.time()
    env.execute()
    end_time = time.time()
    print(f"execution time in seconds: {end_time - start_time:.6f}")


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        dest='input',
        required=False,
        help='Input file to process.')
    parser.add_argument(
        '--output',
        dest='output',
        required=False,
        help='Output file to write results to.')

    argv = sys.argv[1:]
    known_args, _ = parser.parse_known_args(argv)

    audio_processing(known_args.input, known_args.output)
