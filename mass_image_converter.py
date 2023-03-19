from dataclasses import dataclass
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
    tmp_dir = f'temp/{session_uuid()}'
    if not os.path.exists(tmp_dir):
        return None
    
    filenames = os.listdir(tmp_dir)
    nrows = 5
    for i in range(0, len(filenames), nrows):
        cols = st.columns(nrows)
        for j in range(nrows):
            n = i + j
            # print(f'i: {i}, j: {j}, n: {n}')
            if len(filenames) > n:
                name = filenames[n]
                image = load_image(name)
                cols[j].image(image, caption=name)
                cols[j].write(f'{image.format}, {image.width}x{image.height}')  # type: ignore


def garbage_cleanup():
    tmp_dir = f'temp/{session_uuid()}'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    gc.collect()
    print('Cleanup done')


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
            garbage_cleanup()

        with st.form('action'):
            do_resise = st.checkbox('Применить максимальный размер')
            new_size = st.selectbox('Максимальный размер', _sizes, index=len(_sizes)-1)
            change_ratio = st.radio('Изменить форму', ['Не изменять', 'Обрезать до квадрата', 'Расширить до квадрата', 'Расширить до 3:4'])
            remove_bg = st.checkbox('Удалить фон')
            out_format = st.selectbox('Выходной формат', ['JPEG', 'JPEG2000', 'PNG'])
            submited = st.form_submit_button('Обработать изображения')

            if submited:
                for fname in os.listdir(f'temp/{session_uuid()}'):
                    _image = load_image(fname)
                    if do_resise:
                        _image = helpers.resize_image(_image, new_size)  # type: ignore
                    if change_ratio == 'Обрезать до квадрата':
                        _image = helpers.square_crop(_image)
                    elif change_ratio == 'Расширить до квадрата':
                        _image = helpers.square_extend(_image)
                    elif change_ratio == 'Расширить до 3:4':
                        _image = helpers.rectangle_extend(_image)
                    if remove_bg:
                        _image = helpers.remove_bg(_image)
                    save_image(_image, fname)
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
