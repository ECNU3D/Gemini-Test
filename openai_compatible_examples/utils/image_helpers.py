import base64
import mimetypes
import os

# Function to encode the image file to a base64 data URL
def encode_image_to_base64(image_path: str) -> str:
    """Encodes an image file to a base64 data URL string.

    Args:
        image_path: The path to the image file.

    Returns:
        A base64 encoded data URL string (e.g., data:image/jpeg;base64,...).

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the file type is not recognized or supported.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at: {image_path}")

    # Guess the MIME type of the image
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith('image'):
        raise ValueError(f"Could not determine image type or unsupported file type: {mime_type}")

    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        binary_data = image_file.read()

    # Encode the binary data to base64
    base64_encoded_data = base64.b64encode(binary_data)

    # Decode the base64 bytes to a string
    base64_string = base64_encoded_data.decode('utf-8')

    # Format as a data URL
    data_url = f"data:{mime_type};base64,{base64_string}"
    return data_url

# Example Usage (optional - can be run if script is executed directly)
if __name__ == '__main__':
    # Create a dummy image file for testing if it doesn't exist
    dummy_image_path = "dummy_image.png"
    if not os.path.exists(dummy_image_path):
        try:
            from PIL import Image
            img = Image.new('RGB', (60, 30), color = 'red')
            img.save(dummy_image_path)
            print(f"Created dummy image: {dummy_image_path}")
        except ImportError:
            print("Pillow not installed, skipping dummy image creation.")
            # As a fallback, create a tiny text file named like an image
            with open(dummy_image_path, "w") as f:
              f.write("dummy")
            print(f"Created dummy text file named: {dummy_image_path}")
        except Exception as e:
             print(f"Error creating dummy image: {e}")


    if os.path.exists(dummy_image_path):
        try:
            print(f"\nEncoding image: {dummy_image_path}")
            data_url_result = encode_image_to_base64(dummy_image_path)
            print("\nSuccessfully encoded image.")
            # Truncate for display
            print(f"Data URL (truncated): {data_url_result[:80]}...")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error during example usage: {e}")
        finally:
            # Clean up the dummy file
            # os.remove(dummy_image_path)
            # print(f"Cleaned up {dummy_image_path}")
            print(f"(Note: Dummy file {dummy_image_path} may remain for manual inspection)")
    else:
        print("\nSkipping example usage as dummy image could not be created.") 