import os
import zipfile
import subprocess
from PIL import Image
import fitz  # PyMuPDF

def compress_image(input_path, target_size, output_path, min_quality=10):
    quality = 95
    while quality >= min_quality:
        with Image.open(input_path) as img:
            img.save(output_path, optimize=True, quality=quality)
        if os.path.getsize(output_path) <= target_size:
            return True
        quality -= 5
    return False

def compress_video(input_path, target_size, output_path):
    duration_cmd = ["ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
    try:
        duration = float(subprocess.check_output(duration_cmd).decode().strip())
    except:
        print("Error getting video duration")
        return False

    bitrate = (target_size * 8) / duration
    bitrate_k = int(bitrate / 1000)

    ffmpeg_cmd = [
        "ffmpeg", "-i", input_path,
        "-b:v", f"{bitrate_k}k",
        "-bufsize", f"{bitrate_k}k",
        "-y", output_path
    ]

    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.getsize(output_path) <= target_size

def compress_pdf(input_path, target_size, output_path):
    zoom = 1.0
    while zoom > 0.1:
        doc = fitz.open(input_path)
        mat = fitz.Matrix(zoom, zoom)
        new_doc = fitz.open()
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img_pdf = fitz.open()
            rect = fitz.Rect(0, 0, pix.width, pix.height)
            page = img_pdf.new_page(width=pix.width, height=pix.height)
            page.insert_image(rect, pixmap=pix)
            new_doc.insert_pdf(img_pdf)
        new_doc.save(output_path)
        new_doc.close()
        if os.path.getsize(output_path) <= target_size:
            return True
        zoom -= 0.1
    return False

def compress_other(input_path, target_size, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(input_path, os.path.basename(input_path))
    return os.path.getsize(output_path) <= target_size

def compress_file(input_path, target_size_mb, output_path=None):
    ext = os.path.splitext(input_path)[1].lower()
    target_size = int(target_size_mb * 1024 * 1024)

    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    if output_path is None:
        base, ext_no_dot = os.path.splitext(input_path)
        output_path = f"{base}_compressed{ext_no_dot}"

    if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        print("Compressing image...")
        success = compress_image(input_path, target_size, output_path)
    elif ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
        print("Compressing video...")
        success = compress_video(input_path, target_size, output_path)
    elif ext == ".pdf":
        print("Compressing PDF...")
        success = compress_pdf(input_path, target_size, output_path)
    else:
        print("Compressing using zip...")
        if not output_path.endswith(".zip"):
            output_path += ".zip"
        success = compress_other(input_path, target_size, output_path)

    if success:
        print(f"✅ Compression successful: {output_path}")
    else:
        print("❌ Could not reach target size.")

# ============================
# Runtime Input
# ============================

if __name__ == "__main__":
    input_path = input("📥 Enter input file name (with extension): ")
    target_size = float(input("🎯 Enter target size in MB: "))
    output_path = input("📤 Enter output file name (with extension): ")
    compress_file(input_path, target_size, output_path)
