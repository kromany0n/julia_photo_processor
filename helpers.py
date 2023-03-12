# from io import BytesIO
from PIL import Image
import rembg

def square_crop(img: Image.Image) -> Image.Image:
    if img.width > img.height:
        leftover = img.width - img.height
        left = int(leftover/2)
        upper = 0
        right = left + img.height
        lower = img.height
    elif img.height > img.width:
        leftover = img.height - img.width
        left = 0
        upper = int(leftover)
        right = img.width
        lower = leftover + img.width
    else:
        return img
    
    box = (left, upper, right, lower)
    return img.crop(box)

def square_extend(img: Image.Image):
    max_dimention = max(img.size)
    new_image = Image.new("RGBA", (max_dimention, max_dimention), 'white')
    if img.width > img.height:
        diff = img.width - img.height
        left = 0
        upper = int(diff/2)
        right = img.width
        lower = upper + img.height
    elif img.height > img.width:
        diff = img.height - img.width
        left = int(diff/2)
        upper = 0
        right = left + img.width
        lower = img.height
    else:
        return img
    
    box = (left, upper, right, lower)
    new_image.paste(img, box)
    return new_image
        

# def compress(img: Image.Image, size: tuple[int, int]) -> Image.Image:
#     return img

def remove_bg(img: Image.Image) -> Image.Image:
    session = rembg.new_session("u2net")
    result = Image.new("RGBA", img.size, 'white')
    cleared = rembg.remove(img, session = session) # type: ignore
    result.paste(cleared, mask=cleared)
    return result
    

