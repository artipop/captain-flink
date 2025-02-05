# Captain Flink

## Prerequisites
- Install Java (version 11 is [recommended](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/java_compatibility/))
- Install Python (version 3.11)

## Setup
Create virtual env
```shell
python -m venv .venv
source .venv/bin/activate
```
Install the required packages
- `pip install apache-flink`
- `pip install silero-vad` and `pip install soundfile` (required for audio I/O, see other [options](https://github.com/snakers4/silero-vad/wiki/Examples-and-Dependencies#dependencies))
- Install pywhispercpp (depending on the system)
  - for macOS using CoreML: `WHISPER_COREML=1 pip install git+https://github.com/absadiki/pywhispercpp`
  - for Nvidia GPU using CUDA: `GGML_CUDA=1 pip install git+https://github.com/absadiki/pywhispercpp`
  - general installation `pip install pywhispercpp`
- (Optional) Install dependencies for MP3 processing:
  - `pip install pydub` + ffmpeg should be installed

## Running the Application
Then run `python process.py`.

To submit a job on a cluster read [this guide](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/cli/).

## Using Ubuntu 22
Install Java
```shell
sudo apt install openjdk-11-jdk
```
Install Python if not installed
```shell
sudo apt install python
```
or use [PyEnv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) to install specific Python version.

Install Flink
```shell
wget https://dlcdn.apache.org/flink/flink-1.20.0/flink-1.20.0-bin-scala_2.12.tgz
tar -xzf flink-*.tgz
```

(Optional) Install FFMpeg
```shell
sudo apt install ffmpeg
```

Start Flink cluster
```shell
cd flink-1.20.0
./bin/start-cluster.sh
```

## Useful commands
Turn 8kHz audio into 16kHz
```shell
ffmpeg -i audio.wav -acodec pcm_s16le -ar 16000 out2.wav
```
