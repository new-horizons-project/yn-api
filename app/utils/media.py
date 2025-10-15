from PIL import Image
from io import BytesIO
import hashlib

from ..db.enums import MediaSize

def resize_image(image_data: bytes, size: MediaSize) -> bytes:
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

	output = BytesIO()
	image.save(output, format="PNG")
	return output.getvalue()


def verify_image_by_path(file_path: str, sha256_hash: str) -> bool:
	with open(file_path, "rb") as f:
		file_data = f.read()
		calculated_hash = hashlib.sha256(file_data).hexdigest()
		return calculated_hash == sha256_hash