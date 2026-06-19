from fastapi import FastAPI
from auth import sign_in, sign_up
from ip_handler import funcs_choice


app = FastAPI()


@app.get("/")
def main():
    return {"message": "Hello World"}


# сделать получение даты локально или time.google.com
# def current_date(detailed = False):
#     if detailed:
#         pass
#     else:
#         pass


def start():
    # 1. Проверка всех зависимостей.
    # 2. Выбор пользователя(регистрация/логин)
    while True:
        user_choice = int(input("1. Вход\n2. Регистрация\nВыберите [1-2]: "))
        if user_choice == 1:
            if sign_in():
                print("Успешный вход.")
                break  # пускаем
            else:
                print("Не удалось войти.")
                continue  # не пускаем
        else:
            if sign_up():
                print("Успешная регистрация.")
                break  # пускаем
            else:
                print("Не удалось зарегистрироваться.")
                continue  # не пускаем
    # 3. ...
    funcs_choice()


if __name__ == "__main__":
    start()
