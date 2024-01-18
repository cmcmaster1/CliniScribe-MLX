<img src="media/logo.png" width="200" height="200">

# PyQt Transcription with MLX

This application provides a GUI for live audio transcription and session management using MLX on MacOS.

## Setup and Installation

1. Clone the repository.
2. Install the required packages: `pip install -r requirements.txt`.
3. Download and place one of the MLX Whisper models in the models directory ([models on the hub](https://huggingface.co/models?search=mlx%20whisper))
4. Change config.py to reflect the directory of the Whisper model wihtin the models fodler
5. Run `main.py` inside the `src` directory.
6. (Optional): change the LLM in config.py (currently using mlx-community/Mistral-7B-Instruct-v0.2-4bit-mlx, which will be automatically downloaded the first time you run the app)

## Features

- (Semi-)Live audio transcription.
- Session management with SQLite database.
- Text summarization.
- Barely functional.
- Reassuringly ugly.

## Acknowledgements

* MLX (https://github.com/ml-explore/mlx)
* The Whisper implementation is a straight up copy from the MLX Examples repo (https://github.com/ml-explore/mlx-examples) - I haven't even bothered to just take what I need at this stage (TODO: trim code from the whisper folder)
