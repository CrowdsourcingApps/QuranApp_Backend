import uuid

from src.dal.models import User
from src.services.users import check_if_alias_exists, get_user_by_id, get_user_by_alias, create_user, delete_user


def test_create_user(db_session):
    user_data = {'id': str(uuid.uuid4()), 'alias': ' tEsT_aLiAs ', 'name': '   Test_Name', 'surname': 'Test_Surname   '}
    user = User(**user_data)

    # Ensure user does not exist
    assert not check_if_alias_exists(db_session, user.alias)
    assert get_user_by_id(db_session, user.id) is None
    assert get_user_by_alias(db_session, user.alias) is None
    assert not delete_user(db_session, user.id)

    # Create user
    create_user(db_session, user)

    # Check if user now exists
    user = get_user_by_id(db_session, user.id)

    assert user is not None
    assert user.alias == 'test_alias'
    assert user.name == 'Test_Name'
    assert user.surname == 'Test_Surname'
    assert check_if_alias_exists(db_session, user.alias)
    assert get_user_by_alias(db_session, user.alias) is not None
    assert delete_user(db_session, user.id)
