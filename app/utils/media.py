from PIL import Image
from io import BytesIO
import hashlib

from ..db.enums import MediaSize

def resize_image(image_data: bytes, size: MediaSize, trim: bool = False) -> bytes:
	image = Image.open(BytesIO(image_data))
	
	match size:
		case MediaSize.large:
			image.thumbnail((1600, 1600))
		case MediaSize.medium:
			image.thumbnail((800, 800))
		case MediaSize.small:
			image.thumbnail((320, 320))
		case MediaSize.thumbnail:
			image.thumbnail((128, 128))

	image = trim_transparent(image) if trim else image

	output = BytesIO()
	image.save(output, format="PNG")
	return output.getvalue()


def verify_image_by_path(file_path: str, sha256_hash: str) -> bool:
	try:
		with open(file_path, "rb") as f:
			file_data = f.read()
			calculated_hash = hashlib.sha256(file_data).hexdigest()
			return calculated_hash == sha256_hash
	except FileNotFoundError as e:
		raise e
	

def trim_transparent(image: Image.Image) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    # Получаем альфа-канал (прозрачность)
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    return image