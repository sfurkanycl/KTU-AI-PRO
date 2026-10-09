"""Download the replacement Turkish voice (model files only, no remote code)."""
from pathlib import Path
from urllib.request import urlretrieve

BASE = Path(__file__).resolve().parent / "local_models"
SOURCE = "https://huggingface.co/99eren99/piper-turkish-tts/resolve/main/"


def main():
    BASE.mkdir(exist_ok=True)
    female = BASE / "drifting-female"
    female.mkdir(exist_ok=True)
    female_source = "https://huggingface.co/Vyvo/drifting-tts-tr/resolve/main/"
    for name in ("onnx/config.json", "onnx/text_encoder.onnx", "onnx/generator.onnx",
                 "onnx/vocoder.onnx", "voices.json", "README.md"):
        destination = female / Path(name).name
        if not destination.exists():
            temporary = destination.with_suffix(destination.suffix + ".download")
            urlretrieve(female_source + name, temporary)
            temporary.replace(destination)
        print(destination.name)
    for source, target in [("model.onnx", "tr_TR-eren.onnx"),
                           ("config.json", "tr_TR-eren.onnx.json"),
                           ("README.md", "tr_TR-eren-source.md")]:
        destination = BASE / target
        if not destination.exists():
            temporary = destination.with_suffix(destination.suffix + ".download")
            urlretrieve(SOURCE + source, temporary)
            temporary.replace(destination)
        print(target)


if __name__ == "__main__":
    main()
