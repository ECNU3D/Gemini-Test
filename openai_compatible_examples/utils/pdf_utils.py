import os
from typing import List, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None # Will be handled in the function

def convert_pdf_to_pngs(pdf_path: str, dpi: int = 200, output_folder: Optional[str] = None) -> List[str]:
    """Converts a PDF file to a list of PNG images using PyMuPDF.

    Args:
        pdf_path: The path to the PDF file.
        dpi: The target resolution for the output images, in dots per inch.
        output_folder: Optional. The folder to save the PNG images.
                       If None, a folder with the PDF's name will be created
                       in the same directory as the PDF.

    Returns:
        A list of paths to the created PNG image files.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ImportError: If PyMuPDF (fitz) is not installed.
        RuntimeError: If any other error occurs during PDF processing.
    """
    if not fitz:
        raise ImportError(
            "PyMuPDF (fitz) is not installed. "
            "Please install it by running: pip install PyMuPDF"
        )

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    if output_folder is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_folder = os.path.join(pdf_dir, pdf_filename)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_paths: List[str] = []
    try:
        doc = fitz.open(pdf_path)
        # PyMuPDF uses a matrix to scale. Default DPI is 72.
        # zoom_x = dpi / 72.0
        # zoom_y = dpi / 72.0
        # Simplified: if dpi is 200, zoom factor is 200/72 = 2.777...
        # For higher quality, you might want to increase this. Let's use a direct scaling factor based on DPI.
        # A common approach is to render at a higher DPI then scale if needed, but for direct PNG output, setting a matrix is key.
        # Matrix for DPI scaling: fitz.Matrix(zoom_x, zoom_y)
        # zoom_factor = dpi / 72.0 # Default PDF DPI is often 72
        # mat = fitz.Matrix(zoom_factor, zoom_factor)

        # More direct way to set DPI for get_pixmap:
        # The get_pixmap function itself has a dpi parameter as of recent versions of PyMuPDF.
        # However, if we want to be compatible with older versions or use the matrix approach consistently:
        zoom = dpi / 72  # Calculate zoom factor based on desired DPI
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat, alpha=False)  # Use the matrix for scaling
            image_filename = f"page_{page_num + 1}.png"
            image_path = os.path.join(output_folder, image_filename)
            pix.save(image_path)
            image_paths.append(image_path)
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to PNGs with PyMuPDF: {e}") from e
    return image_paths

# Example Usage (optional - can be run if script is executed directly)
if __name__ == '__main__':
    # Example for PDF conversion
    # Create a dummy PDF for testing if it doesn't exist and if reportlab is installed
    dummy_pdf_path = "dummy_document.pdf"
    if not os.path.exists(dummy_pdf_path):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            c = canvas.Canvas(dummy_pdf_path, pagesize=letter)
            c.drawString(100, 750, "Hello World!")
            c.showPage()
            c.drawString(100, 750, "This is page 2.")
            c.save()
            print(f"Created dummy PDF: {dummy_pdf_path}")
        except ImportError:
            print("reportlab not installed, skipping dummy PDF creation.")
            print("To run this example, please install reportlab: pip install reportlab")
        except Exception as e:
            print(f"Error creating dummy PDF: {e}")

    if os.path.exists(dummy_pdf_path):
        print(f"\nConverting PDF: {dummy_pdf_path} using PyMuPDF")
        try:
            if not fitz:
                print("PyMuPDF (fitz) is not installed. Skipping PDF conversion example.")
                print("Please install it by running: pip install PyMuPDF")
            else:
                png_files = convert_pdf_to_pngs(dummy_pdf_path, dpi=150) # Using a moderate DPI for example
                print("\nSuccessfully converted PDF to PNGs:")
                for png_file in png_files:
                    print(f" - {png_file}")
                print(f"(Note: Dummy PDF {dummy_pdf_path} and its output folder may remain for manual inspection)")

        except (FileNotFoundError, RuntimeError, ImportError) as e:
            print(f"Error during PDF conversion example: {e}")
    else:
        print("\nSkipping PDF conversion example as dummy PDF could not be created.") 