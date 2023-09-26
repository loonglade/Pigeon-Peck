from PIL import Image

def png_to_ico(png_path, ico_path):
    """Converts a PNG image to ICO format."""
    image = Image.open(png_path)
    image = image.resize((16, 16), Image.LANCZOS)
    image.save(ico_path, format='ICO')

png_to_ico("assets/images/logo.png", "assets/images/icon.ico")