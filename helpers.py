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
        upper = int(leftover/2)
        right = img.width
        lower = upper + img.width
    else:
        return img
    
    box = (left, upper, right, lower)
    return img.crop(box)

def square_extend(img: Image.Image):
    max_dimention = max(img.size)
    new_image = Image.new("RGB", (max_dimention, max_dimention), 'white')
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


def rectangle_extend(img: Image.Image) -> Image.Image:
    ratio = 3/4
    new_width = img.width
    if ratio >= img.width/img.height:
        return img
    
    new_height = int(new_width/ratio)
    new_image = Image.new("RGB", (new_width, new_height), 'white')

    diff = new_height - img.height
    left = 0
    upper = int(diff/2)
    right = img.width
    lower = upper + img.height

    box = (left, upper, right, lower)
    new_image.paste(img, box)
    return new_image


def remove_bg(img: Image.Image) -> Image.Image:
    session = rembg.new_session("u2net") # type: ignore
    result = Image.new("RGB", img.size, 'white')
    cleared = rembg.remove(img, session = session) # type: ignore
    result.paste(cleared, mask=cleared) # type: ignore
    return result
    

def resize_image(image: Image.Image, new_size_str: str):
        new_size = new_size_str.split('x')
        width = int(new_size[0])
        height = int(new_size[1])
        if width < image.width and height < image.height:
            return image.resize((width, height))
        return image