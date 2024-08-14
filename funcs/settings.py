from passlib.context import CryptContext 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """ Función para verificar la contraseña """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """ Función para hashear la contraseña """
    return pwd_context.hash(password)