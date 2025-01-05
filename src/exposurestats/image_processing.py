import base64
from io import BytesIO
from pathlib import Path

import rawpy
from PIL import Image

RAWPI_EXTENSIONS = {
    # Sony
    ".arw",
    ".sr2",
    # Canon
    ".cr2",
    ".cr3",
    # Nikon
    ".nef",
    # Generic/Adobe
    ".dng",
    # Fujifilm
    ".raf",
    # Olympus
    ".orf",
    # Panasonic
    ".rw2",
    # Pentax
    ".pef",
    # Olympus ORI file is a standard ORF file of the first standard resolution image taken in the sequence used to create the HR shot.
    ".ori",
}


def encode_image(image_path: str) -> bytes:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def open_raw_image(image_path: Path | str) -> bytes:
    """Opens a RAW image file and extracts its embedded JPEG preview.

    Args:
        image_path: Path to the RAW image file

    Returns:
        Embedded JPEG preview as bytes
    """
    with rawpy.imread(str(image_path)) as raw:
        thumb = raw.extract_thumb()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            return thumb.data
        # If no JPEG thumb available, process the RAW image
        rgb = raw.postprocess()
        img = Image.fromarray(rgb)
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()


def open_image(image_path: Path | str) -> bytes:
    """Opens an image file and returns its bytes. Supports both JPEG/PNG and RAW formats.

    Args:
        image_path: Path to the image file

    Returns:
        Image file contents as bytes
    """
    image_path = Path(image_path)

    if image_path.suffix.lower() in RAWPI_EXTENSIONS:
        return open_raw_image(image_path)

    with open(image_path, "rb") as f:
        return f.read()


def resize_image(image: bytes, target_size: tuple[int, int] = (512, 512), preserve_ratio: bool = False) -> bytes:
    """Resizes an image to the target size while maintaining aspect ratio.

    Args:
        image: Image in bytes to resize
        target_size: Desired output dimensions (width, height)
        preserve_ratio: Whether to preserve the aspect ratio

    Returns:
        Resized image as bytes
    """

    # Convert bytes to PIL Image
    img = Image.open(BytesIO(image))

    if preserve_ratio:
        target_ratio = target_size[0] / target_size[1]
        img_ratio = img.size[0] / img.size[1]

        # Determine dimensions to maintain aspect ratio
        if img_ratio > target_ratio:
            # Image is wider than target
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)
        else:
            # Image is taller than target
            new_height = target_size[1]
            new_width = int(new_height * img_ratio)
    else:
        new_width, new_height = target_size

    # Resize image
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create new image with padding
    new_img = Image.new("RGB", target_size, (0, 0, 0))
    paste_x = (target_size[0] - new_width) // 2
    paste_y = (target_size[1] - new_height) // 2
    new_img.paste(img, (paste_x, paste_y))

    # Convert back to bytes
    buffer = BytesIO()
    new_img.save(buffer, format="JPEG")
    return buffer.getvalue()


def to_base64(image_bytes: bytes) -> str:
    """Converts image bytes to base64 string.

    Args:
        image_bytes: Image data as bytes

    Returns:
        Base64 encoded string of the image
    """
    import base64

    return base64.b64encode(image_bytes).decode("utf-8")


def image_to_base64(image_path: Path, target_size: tuple[int, int] = (512, 512)) -> str:
    """Convert an image file to base64 encoded string.

    Args:
        image_path: Path to the image file
        target_size: Target dimensions as (width, height) tuple

    Returns:
        Base64 encoded string of the resized image
    """
    img = open_image(image_path)
    img_ = resize_image(img, target_size=target_size)
    out = to_base64(img_)
    return out
