import os
from faster_whisper import WhisperModel

# choices: base, small, medium, large-v3
model_size = os.environ.get('MODEL_SIZE', 'base')

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
model = WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe(filepath):
    text = ""
    segments, info = model.transcribe(filepath, beam_size=5)
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        text += "\n" + segment.text
    return text

