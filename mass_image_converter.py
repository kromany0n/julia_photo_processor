from dataclasses import dataclass
from io import BytesIO
import uuid
import os
import gc
import yaml
import shutil
import streamlit as st
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit_authenticator as stauth
import helpers

gc.enable()


@dataclass()
class SessionImage():
    name: str
    image: Image.Image


def session_uuid():
    if 'uuid' not in st.session_state:
        st.session_state.uuid = str(uuid.uuid4())

    return st.session_state.uuid


def load_image(name: str):
    return Image.open(f'temp/{session_uuid()}/{name}')


def save_image(image: Image.Image, name: str):
    return image.save(f'temp/{session_uuid()}/{name}')


def process_uploaded_images(uploaded_files: list[UploadedFile]):
    tmp_dir = f'temp/{session_uuid()}'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)

    if 'images' not in st.session_state.keys():
        st.session_state.images = []

    for uf in uploaded_files:
        with open(f'temp/{session_uuid()}/{uf.name}', 'wb') as f:
            f.write(uf.getbuffer())
            thumb_image = Image.open(BytesIO(uf.getvalue()))
            thumb_image.thumbnail((300, 300))
            thumb = SessionImage(uf.name, thumb_image)
            st.session_state.images.append(thumb)  # type: ignore


def prepare_download_file(img_out_format: str):
    tmp_dir = f'temp/{session_uuid()}'

    for thumb in st.session_state.images:
        fname = thumb.name.split('.')[0]
        extention = img_out_format.lower()
        format = img_out_format.lower()

        image = Image.open(f'{tmp_dir}/{thumb.name}')

        if img_out_format == 'JPEG':
            extention = 'jpg'
            format = 'jpeg'
            image = image.convert('RGB')
        elif img_out_format == 'JPEG2000':
            extention = 'jpg'
            format = 'jpeg2000'
            image = image.convert('RGBA')

        image.save(f'{tmp_dir}/{fname}.{extention}', format)

    shutil.make_archive(tmp_dir, 'zip', tmp_dir)
    return f'temp/{session_uuid()}.zip'


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
                thumb = st.session_state.images[n]
                image = load_image(thumb.name)
                cols[j].image(thumb.image, caption=thumb.name)
                cols[j].write(f'{image.format}, {image.width}x{image.height}')  # type: ignore


def garbage_cleanup():
    tmp_dir = f'temp/{session_uuid()}'
    shutil.rmtree(tmp_dir)
    if 'images' in st.session_state.keys():
        del st.session_state['images']
    gc.collect()


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
    session_uuid()

    with st.form('uploader', clear_on_submit=True):
        uploaded_files = st.file_uploader("Выберите файлы", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'tiff'])
        submitted = st.form_submit_button("Загрузить")

        if submitted and uploaded_files is not None and not _download_file:
            process_uploaded_images(uploaded_files)

    with st.sidebar:
        if st.button('Очистка'):
            if 'images' in st.session_state.keys():
                for i in range(len(st.session_state.images)-1, 0, -1):
                    del st.session_state.images[i]
                del st.session_state['images']
            print('Cleanup done')
            gc.collect()
            st.experimental_rerun()

        with st.form('action'):
            do_resise = st.checkbox('Применить максимальный размер')
            new_size = st.selectbox('Максимальный размер', _sizes, index=len(_sizes)-1)
            do_square = st.radio('Оквадратить', ['Не изменять', 'Обрезать до квадрата', 'Расширить до квадрата'])
            do_remove_bg = st.checkbox('Удалить фон')
            out_format = st.selectbox('Выходной формат', ['JPEG', 'JPEG2000', 'PNG'])
            submited = st.form_submit_button('Обработать изображения')

            if submited:
                if 'images' in st.session_state:
                    for thumb in st.session_state.images:
                        _image = load_image(thumb.name)
                        if do_resise:
                            _image = helpers.resize_image(_image, new_size)  # type: ignore
                        if do_square == 'Обрезать до квадрата':
                            _image = helpers.square_crop(_image)
                        elif do_square == 'Расширить до квадрата':
                            _image = helpers.square_extend(_image)
                        if do_remove_bg:
                            _image = helpers.remove_bg(_image)
                        save_image(_image, thumb.name)
                        del _image

                    _download_file = prepare_download_file(out_format)  # type: ignore
                    st.success('Обработка завершена')

        if _download_file:
            st.download_button(
                label='Скачать',
                data=open(_download_file, 'rb'),
                file_name='archive.zip',
                mime='application/zip'
            )

    draw_image_grid()

gc.collect()
