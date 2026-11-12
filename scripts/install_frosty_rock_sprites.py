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
        print(f"Restored exact approved image by removing artifact at {offset}")
        break

if original is None:
    # Fallback: find the actual PNG byte layout and check all four CRCs.
    import zlib
    def png_score(data):
        if data[:8] != bytes([137,80,78,71,13,10,26,10]):
            return (-1, [])
        p = 8
        errors = []
        types = []
        while p < len(data):
            if p + 12 > len(data): return (-1, [])
            ln = int.from_bytes(data[p:p+4], "big")
            typ = data[p+4:p+8]
            if ln > len(data) - p - 12: return (-1, [])
            chunk = data[p+8:p+8+ln]
            check = int.from_bytes(data[p+8+ln:p+12+ln], "big")
            ok = (zlib.crc32(typ + chunk) & 0xffffffff) == check
            errors.append((typ.decode("ascii","replace"), ok))
            types.append(typ)
            p += 12 + ln
            if typ == b"IEND": break
        if p != len(data) or not types or types[-1] != b"IEND":return (-1,[])
        return (sum(ok for _,ok in errors),errors)
    best = (-1, None, None, None)
    for offset in range(0, len(source) - extra + 1):
        candidate = source[:offset] + source[offset + extra:]
        score, checks = png_score(candidate)
        if score > best[0]:best = (score,offset,checks,candidate)
        if score >= 4 and all(ok for _,ok in checks):
            try:
                image_check = Image.open(BytesIO(candidate))
                image_check.load()
                original = candidate
                print(f"Recovered PNG by validating all CRCs; offset={offset}; sha={blob_sha(candidate)}")
                break
            except Exception:pass
    print(f"Best PNG score: {best[0]}, offset={best[1]}, checks={best[2]}")
    if original is None and best[0] >= 3:
        try:
            image_check = Image.open(BytesIO(best[3]))
            image_check.load()
            original = best[3]
            print(f"Recovered image from mostly-valid PNG: offset={best[1]}")
        except Exception as exc:
            print("Best candidate Pillow error:", repr(exc))

assert original is not None, "Cannot recover a valid PNG; abort without changing assets"
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
