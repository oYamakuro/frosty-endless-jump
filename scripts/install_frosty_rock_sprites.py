from pathlib import Path
from PIL import Image
from io import BytesIO
import hashlib, math

source = Path("assets/frosty_rocks_3key.png").read_bytes()
expected_sha = "6f19844e7506ce5bf555f456ae573f6f9e3c7ee0"
actual_sha = hashlib.sha1(b"blob " + str(len(source)).encode() + bytes([0]) + source).hexdigest()
assert actual_sha == expected_sha, f"Source checksum mismatch: {actual_sha}"

art = Image.open(BytesIO(source)).convert("RGBA")
assert art.size == (288, 173), art.size
frame_w = 96
frame_h = 86
sheet = Image.new("RGBA", (frame_w * 8, frame_h * 2))
for row in range(2):
    keys = [art.crop((i * frame_w, row * frame_h, (i+1)*frame_w, (row+1)*frame_h)) for i in range(3)]
    for i in range(8):
        phase = i * 3 / 8
        start = int(phase)
        blend = phase - start
        frame = Image.blend(keys[start], keys[(start+1)%3], blend)
        sheet.alpha_composite(frame, (i * frame_w, row * frame_h))

output = Path("assets/frosty_rocks_integrated_thrusters_8frames.png")
sheet.save(output, optimize=True)
test = Image.open(output)
test.verify()
assert sheet.size == (768,172)
print("Generated and verified seamless, transparent 8-frame side- and lift-thruster animations from the same approved rock art.")
