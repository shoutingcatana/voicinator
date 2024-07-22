import os
from faster_whisper import WhisperModel


# choices: base, small, medium, large-v3
model_size_1 = os.environ.get('MODEL_SIZE_STAGE_1', 'small')
model_size_2 = os.environ.get('MODEL_SIZE_STAGE_2', 'medium')


# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model_1 = WhisperModel(model_size_1, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8

model_1 = WhisperModel(model_size_1, device="cpu", compute_type="int8")
model_2 = WhisperModel(model_size_2, device="cpu", compute_type="int8")


def transcribe(filepath, used_model):
    text = ""
    segments, info = used_model.transcribe(filepath, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    for segment in segments:

        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        text += "\n" + segment.text
    return text

