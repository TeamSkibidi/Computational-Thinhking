from user_entity import UserEntity

user = UserEntity(username="test", email="t@t.com", hashed_password="")
user.set_password("123456")
print(user.hashed_password)  # hash
print(user.verify_password("123456"))  # True
print(user.verify_password("sai"))     # False