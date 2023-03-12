import streamlit_authenticator as stauth
import random
import string

def get_random_string(length: int) -> str:
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return result_str

password = get_random_string(16)
hashed_password = stauth.Hasher([password]).generate()
print(password, hashed_password[0], sep='\n')