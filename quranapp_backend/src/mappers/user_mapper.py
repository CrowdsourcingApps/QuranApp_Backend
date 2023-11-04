from src.dal.models import User as UserDal
from src.models import UserModel


def map_to_dal(user: UserModel) -> UserDal:
    return UserDal(id=user.id, alias=user.alias, name=user.name, surname=user.surname)


def map_to_model(user: UserDal) -> UserModel:
    return UserModel(id=user.id, alias=user.alias, name=user.name, surname=user.surname)
