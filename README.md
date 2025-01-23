Для добавления логина и пароля в хранилище необходимо открыть консоль Python и ввести команды:
    import keyring
    keyring.set_password("Server", "User", "Ввести пароль")
    keyring.set_password("Server", "User", "Ввести пароль")
    keyring.set_password("Jenkins", "User", "Ввести пароль")

Для проверки пароля ввести:
    keyring.get_password("("Server", ", "User")
    keyring.get_password("("Server", ", "User")
    keyring.get_password("Jenkins", "User")

Python должен быть версии 3.9

PuTTY должна быть версии 0.70

В файле Functions.py проверить пути до установленных программ Putty и 7z, а также пути до логов и файлов. Указать свой логин

Если скрипт при первом запуске завис, то необходимо через cmd выполнить команду ниже вручную для каждого сервера, чтобы прогрузить ssh ключи
Команда:"C:\Program Files\PuTTY\plink.exe" 11.111.111.111 -ssh -l User -pw password ls "/data/share/"
