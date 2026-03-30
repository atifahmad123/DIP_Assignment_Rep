"""
Image Steganography Application
================================
Author  : [Your Name]
Reg. No : [Your Registration Number]
Course  : Digital Image Processing
Assignment : 01  —  Q5 & Q6

Description:
    This application hides a secret image inside a cover image using
    LSB (Least Significant Bit) steganography, and can also extract
    the hidden image back.

GitHub Repository : https://github.com/[your-username]/image-steganography
"""

import numpy as np
from PIL import Image
import os
import struct


# ─────────────────────────────────────────────────────────────────────────────
# CORE LSB STEGANOGRAPHY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def hide_image(cover_path: str, secret_path: str, output_path: str,
               bits: int = 4) -> bool:
    """
    Hide a secret image inside a cover image using LSB steganography.

    Parameters
    ----------
    cover_path  : Path to the cover (carrier) image.
    secret_path : Path to the secret image to hide.
    output_path : Where to save the stego image.
    bits        : Number of LSBs to use (1–7). More bits → higher
                  capacity but more visible distortion. Default = 4.

    Returns
    -------
    True on success, False on failure.
    """
    try:
        cover  = Image.open(cover_path).convert('RGB')
        secret = Image.open(secret_path).convert('RGB')

        # Resize secret to fit inside cover
        secret = secret.resize(cover.size, Image.LANCZOS)

        cover_arr  = np.array(cover,  dtype=np.uint8)
        secret_arr = np.array(secret, dtype=np.uint8)

        # Store original secret dimensions in first 8 bytes of the image
        h, w = secret_arr.shape[:2]

        # --- embed ---
        # Clear the `bits` LSBs of cover, then write top `bits` of secret
        mask_clear  = 0xFF & ~((1 << bits) - 1)   # e.g. 0xF0 for bits=4
        shift       = 8 - bits                      # e.g. 4 for bits=4

        stego_arr = (cover_arr & mask_clear) | (secret_arr >> shift)

        # Pack width/height into the very first pixel's bytes as a watermark
        stego_arr[0, 0, 0] = (w >> 8) & 0xFF
        stego_arr[0, 0, 1] = w & 0xFF
        stego_arr[0, 0, 2] = bits

        stego_arr[0, 1, 0] = (h >> 8) & 0xFF
        stego_arr[0, 1, 1] = h & 0xFF
        stego_arr[0, 1, 2] = 0  # reserved

        stego_img = Image.fromarray(stego_arr)
        stego_img.save(output_path, format='PNG')   # PNG is lossless — vital!

        print(f"[✓] Secret image hidden successfully → {output_path}")
        print(f"    Cover  : {cover_path}  ({cover.size})")
        print(f"    Secret : {secret_path}  ({secret.size})")
        print(f"    Bits used per channel : {bits}")
        return True

    except Exception as exc:
        print(f"[✗] Error hiding image: {exc}")
        return False


def extract_image(stego_path: str, output_path: str) -> bool:
    """
    Extract the hidden image from a stego image.

    Parameters
    ----------
    stego_path  : Path to the stego (carrier) image that contains the secret.
    output_path : Where to save the recovered secret image.

    Returns
    -------
    True on success, False on failure.
    """
    try:
        stego_arr = np.array(Image.open(stego_path).convert('RGB'),
                             dtype=np.uint8)

        # Read metadata from watermark pixels
        w    = (int(stego_arr[0, 0, 0]) << 8) | int(stego_arr[0, 0, 1])
        bits = int(stego_arr[0, 0, 2])
        h    = (int(stego_arr[0, 1, 0]) << 8) | int(stego_arr[0, 1, 1])

        if bits == 0 or bits > 7:
            raise ValueError("Could not detect steganography metadata. "
                             "Was this image encoded with this app?")

        # Extract the LSBs and shift them back to MSB position
        mask  = (1 << bits) - 1          # e.g. 0x0F for bits=4
        shift = 8 - bits                  # e.g. 4 for bits=4

        secret_arr = ((stego_arr & mask) << shift).astype(np.uint8)

        # Crop to original secret dimensions
        secret_arr = secret_arr[:h, :w]

        secret_img = Image.fromarray(secret_arr)
        secret_img.save(output_path)

        print(f"[✓] Hidden image extracted successfully → {output_path}")
        print(f"    Detected size : {w} × {h} px")
        print(f"    Bits used     : {bits}")
        return True

    except Exception as exc:
        print(f"[✗] Error extracting image: {exc}")
        return False


def calculate_psnr(original_path: str, stego_path: str) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio between original cover
    and stego image to measure visual distortion.

    Higher PSNR → less visible distortion (> 40 dB is generally imperceptible).
    """
    orig  = np.array(Image.open(original_path).convert('RGB'), dtype=np.float64)
    stego = np.array(Image.open(stego_path).convert('RGB'),    dtype=np.float64)

    if orig.shape != stego.shape:
        stego = np.array(
            Image.open(stego_path).convert('RGB').resize(
                (orig.shape[1], orig.shape[0])),
            dtype=np.float64)

    mse  = np.mean((orig - stego) ** 2)
    if mse == 0:
        return float('inf')
    psnr = 10 * np.log10(255.0 ** 2 / mse)
    return round(psnr, 2)


def image_capacity(cover_path: str, bits: int = 4) -> dict:
    """
    Report how much data (in bytes / pixels) can be hidden inside
    the given cover image.
    """
    img  = Image.open(cover_path).convert('RGB')
    w, h = img.size
    total_pixels   = w * h
    bytes_per_pixel = (bits * 3) // 8          # 3 channels
    capacity_bytes  = total_pixels * bytes_per_pixel
    capacity_kb     = round(capacity_bytes / 1024, 2)

    return {
        'width'          : w,
        'height'         : h,
        'total_pixels'   : total_pixels,
        'bits_used'      : bits,
        'capacity_bytes' : capacity_bytes,
        'capacity_kb'    : capacity_kb,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIMPLE TEXT-BASED CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import sys

    banner = """
╔══════════════════════════════════════════════════════╗
║          IMAGE STEGANOGRAPHY APPLICATION             ║
║          LSB (Least Significant Bit) Method          ║
╚══════════════════════════════════════════════════════╝
"""
    print(banner)
    print("Commands:")
    print("  1. Hide image    — embed a secret image in a cover image")
    print("  2. Extract image — recover the hidden image from a stego image")
    print("  3. PSNR          — measure distortion of stego vs original")
    print("  4. Capacity      — check how much can be hidden in an image")
    print("  5. Exit")
    print()

    while True:
        choice = input("Enter choice (1-5): ").strip()

        if choice == '1':
            cover   = input("  Cover image path  : ").strip()
            secret  = input("  Secret image path : ").strip()
            output  = input("  Output path       : ").strip()
            bits    = int(input("  Bits to use (1-7) [default 4]: ").strip() or 4)
            hide_image(cover, secret, output, bits)

        elif choice == '2':
            stego  = input("  Stego image path  : ").strip()
            output = input("  Output path       : ").strip()
            extract_image(stego, output)

        elif choice == '3':
            orig  = input("  Original cover path : ").strip()
            stego = input("  Stego image path    : ").strip()
            psnr  = calculate_psnr(orig, stego)
            print(f"  PSNR = {psnr} dB  ({'Imperceptible' if psnr > 40 else 'Visible distortion'})")

        elif choice == '4':
            path = input("  Cover image path  : ").strip()
            bits = int(input("  Bits to use (1-7) [default 4]: ").strip() or 4)
            cap  = image_capacity(path, bits)
            print(f"  Image size      : {cap['width']} × {cap['height']} px")
            print(f"  Capacity        : {cap['capacity_bytes']} bytes  ({cap['capacity_kb']} KB)")

        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1–5.")


if __name__ == '__main__':
    main()
