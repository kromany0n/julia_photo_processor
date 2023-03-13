from dataclasses import dataclass
from io import BytesIO
import uuid
import os
import yaml
from shutil import make_archive, rmtree
import streamlit as st
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit_authenticator as stauth
import helpers


@dataclass()
class SessionImage():
    name: str
    image: Image.Image


def get_session_uuid():
    if 'uuid' not in st.session_state:
        st.session_state.uuid = str(uuid.uuid4())

    return st.session_state.uuid


@st.cache_data()
def process_uploaded_images(uploaded_files: list[UploadedFile]):
    return [SessionImage(f.name, Image.open(BytesIO(f.getvalue()))) for f in uploaded_files]


def prepare_download_file(img_out_format: str):
    session_uuid = get_session_uuid()
    tmp_dir = f'temp/{session_uuid}'

    if os.path.exists(tmp_dir):
        rmtree(tmp_dir)
    os.mkdir(tmp_dir)

    for img in st.session_state.images:
        fname = img.name.split('.')[0]
        extention = img_out_format.lower()
        format = img_out_format.lower()

        if img_out_format == 'JPEG':
            extention = 'jpg'
            format = 'jpeg'
            img.image = img.image.convert('RGB')
        elif img_out_format == 'JPEG2000':
            extention = 'jpg'
            format = 'jpeg2000'
            img.image = img.image.convert('RGBA')

        img.image.save(f'{tmp_dir}/{fname}.{extention}', format)

    make_archive(tmp_dir, 'zip', tmp_dir)
    return f'temp/{session_uuid}.zip'


def resize_images(new_size_str: str):
    for i, img in enumerate(st.session_state.images):
        new_size = new_size_str.split('x')
        width = int(new_size[0])
        height = int(new_size[1])
        if width < img.image.width and height < img.image.height:
            st.session_state.images[i].image = img.image.resize((width, height))


def square_crop_images():
    for i, img in enumerate(st.session_state.images):
        st.session_state.images[i].image = helpers.square_crop(img.image)


def square_extend_images():
    for i, img in enumerate(st.session_state.images):
        st.session_state.images[i].image = helpers.square_extend(img.image)


def remove_background():
    for i, img in enumerate(st.session_state.images):
        st.session_state.images[i].image = helpers.remove_bg(img.image)


def draw_image_grid():
    nrows = 5
    if 'images' not in st.session_state:
        return None

    for i in range(0, len(st.session_state.images), nrows):
        cols = st.columns(nrows)
        for j in range(nrows):
            n = i + j
            # print(f'i: {i}, j: {j}, n: {n}')
            if len(st.session_state.images) > n:
                img = st.session_state.images[n]
                cols[j].image(img.image, caption=img.name)
                cols[j].write(f'{img.image.format}, {img.image.width}x{img.image.height}')  # type: ignore


# our app
st.set_page_config(layout="wide")

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=yaml.loader.SafeLoader)

authenticator = stauth.Authenticate(  # type: ignore
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)


name, authentication_status, username = authenticator.login('Login', 'main')  # type: ignore

_sizes = [f'{i}x{i}' for i in range(1000, 3501, 500)]
_download_file = None

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
elif authentication_status == True:
    with st.sidebar:
        with st.form('action'):
            do_resise = st.checkbox('Применить максимальный размер')
            new_size = st.selectbox('Максимальный размер', _sizes, index=len(_sizes)-1)
            do_square = st.radio('Оквадратить', ['Не изменять', 'Обрезать до квадрата', 'Расширить до квадрата'])
            do_remove_bg = st.checkbox('Удалить фон')
            out_format = st.selectbox('Выходной формат', ['JPEG', 'JPEG2000', 'PNG'])
            submited = st.form_submit_button('Обработать изображения')

            if submited:
                if 'images' in st.session_state:
                    if do_resise:
                        resize_images(new_size)  # type: ignore
                    if do_square == 'Обрезать до квадрата':
                        square_crop_images()
                    elif do_square == 'Расширить до квадрата':
                        square_extend_images()
                    if do_remove_bg:
                        remove_background()

                    _download_file = prepare_download_file(out_format)  # type: ignore
                    st.success('Обработка завершена')

        if _download_file:
            st.download_button(
                label='Скачать',
                data=open(_download_file, 'rb'),
                file_name='archive.zip',
                mime='application/zip'
            )

    uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'tiff'])

    if uploaded_files and not _download_file:
        st.session_state.images = process_uploaded_images(uploaded_files)

    draw_image_grid()
