from pathlib import Path
from PIL import Image
from io import BytesIO
import hashlib

source = Path("assets/rock_unified_sprite_prototype.png").read_bytes()
target_sha = "4b86a3d6ab629d7bf13a9a0f93ea0837a0112eef"
expected_length = 7431
extra = len(source) - expected_length
assert extra == 27, f"Unexpected transfer size: {len(source)}"

def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()

original = None
for offset in range(0, len(source) - extra + 1):
    candidate = source[:offset] + source[offset + extra:]
    if blob_sha(candidate) == target_sha:
        original = candidate
        print(f"Restored approved source image exactly by removing transfer artifact at byte {offset}")
        break

assert original is not None, "Cannot restore the exact original sprite: abort without changing assets"
image = Image.open(BytesIO(original)).convert("RGBA")
assert image.size == (384, 173), image.size
image.load()

# Expand the four authentic key poses into eight smooth animation frames.
# Two sprite rows share the same rock design; only exhaust direction differs.
frame_w = image.width // 4
frame_h = image.height // 2
sheet = Image.new("RGBA", (8 * frame_w, 2 * frame_h))
for row in range(2):
    for frame in range(4):
        frame_a = image.crop((frame * frame_w, row * frame_h,
                              (frame + 1) * frame_w, (row + 1) * frame_h))
        next_frame = (frame + 1) % 4
        frame_b = image.crop((next_frame * frame_w, row * frame_h,
                              (next_frame + 1) * frame_w, (row + 1) * frame_h))
        sheet.alpha_composite(frame_a, (frame * 2 * frame_w, row * frame_h))
        sheet.alpha_composite(Image.blend(frame_a, frame_b, .5),
                              ((frame * 2 + 1) * frame_w, row * frame_h))

output = Path("assets/frosty_rocks_integrated_thrusters_8frames.png")
sheet.save(output, optimize=True)
check = Image.open(output)
check.verify()
print(f"Verified {output}: {sheet.size[0]}x{sheet.size[1]}, 8 frames per platform mode")
