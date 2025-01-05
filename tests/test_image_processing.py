import base64
from io import BytesIO

import pytest
from PIL import Image

from exposurestats.image_processing import (
    encode_image,
    image_to_base64,
    open_image,
    resize_image,
    to_base64,
)


@pytest.fixture
def sample_image_path(tmp_path):
    """Creates a sample test image."""
    img_path = tmp_path / "test_image.jpg"
    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_image_bytes(sample_image_path):
    """Returns sample image as bytes."""
    with open(sample_image_path, "rb") as f:
        return f.read()


def test_encode_image(sample_image_path):
    """Test encoding image to base64."""
    encoded = encode_image(str(sample_image_path))
    assert isinstance(encoded, str)
    # Verify it's valid base64
    assert base64.b64decode(encoded)


def test_open_image(sample_image_path):
    """Test opening image file."""
    # Test with Path object
    img_bytes = open_image(sample_image_path)
    assert isinstance(img_bytes, bytes)

    # Test with string path
    img_bytes = open_image(str(sample_image_path))
    assert isinstance(img_bytes, bytes)


def test_resize_image(sample_image_bytes):
    """Test image resizing functionality."""
    # Test without preserving ratio
    resized = resize_image(sample_image_bytes, (50, 50), preserve_ratio=False)
    img = Image.open(BytesIO(resized))
    assert img.size == (50, 50)

    # Test with preserving ratio
    resized = resize_image(sample_image_bytes, (50, 100), preserve_ratio=True)
    img = Image.open(BytesIO(resized))
    assert img.size == (50, 100)  # Target size with padding


def test_to_base64(sample_image_bytes):
    """Test converting image bytes to base64."""
    b64_str = to_base64(sample_image_bytes)
    assert isinstance(b64_str, str)
    # Verify it's valid base64
    decoded = base64.b64decode(b64_str)
    assert isinstance(decoded, bytes)


def test_image_to_base64(sample_image_path):
    """Test end-to-end image to base64 conversion."""
    b64_str = image_to_base64(sample_image_path, target_size=(256, 256))
    assert isinstance(b64_str, str)

    # Verify the decoded image has correct dimensions
    img_data = base64.b64decode(b64_str)
    img = Image.open(BytesIO(img_data))
    assert img.size == (256, 256)


def test_invalid_image_path():
    """Test handling of invalid image paths."""
    with pytest.raises(FileNotFoundError):
        open_image("nonexistent.jpg")


def test_resize_image_different_ratios(sample_image_bytes):
    """Test resizing with different aspect ratios."""
    # Test wide target
    resized = resize_image(sample_image_bytes, (200, 100), preserve_ratio=True)
    img = Image.open(BytesIO(resized))
    assert img.size == (200, 100)

    # Test tall target
    resized = resize_image(sample_image_bytes, (100, 200), preserve_ratio=True)
    img = Image.open(BytesIO(resized))
    assert img.size == (100, 200)


def _test_open_raw_image(raw_file_path):
    """Test opening image file."""
    # Test with Path object
    img_bytes = open_image(raw_file_path)
    resized = resize_image(img_bytes, (256, 256), preserve_ratio=True)
    assert isinstance(img_bytes, bytes)
    assert isinstance(resized, bytes)


if __name__ == "__main__":
    _test_open_raw_image("data/images/P4240313.ORF")
    _test_open_raw_image("data/images/PC260752.ORI")
