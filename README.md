1. Для добавления логина и пароля в хранилище необходимо открыть консоль Python и ввести команды:

    import keyring

    keyring.set_password("Server", "User", "Ввести пароль")

    keyring.set_password("Server", "User", "Ввести пароль")

    keyring.set_password("Jenkins", "User", "Ввести пароль")

2. Для проверки пароля ввести:

    keyring.get_password("("Server", ", "User")

    keyring.get_password("("Server", ", "User")

    keyring.get_password("Jenkins", "User")

3. Python должен быть версии 3.9

4. PuTTY должна быть версии 0.70

5. В файле Functions.py проверить пути до установленных программ Putty и 7z, а также пути до логов и файлов. Указать свой логин

6. Если скрипт при первом запуске завис, то необходимо через cmd выполнить команду ниже вручную для каждого сервера, чтобы прогрузить ssh ключи

    Команда:"C:\Program Files\PuTTY\plink.exe" 11.111.111.111 -ssh -l User -pw password ls "/data/share/"

7. Библиотеки из проекта:

    beautifulsoup4     4.12.3
    certifi            2024.8.30
    charset-normalizer 3.4.0idna
    3.10importlib_metadata 8.5.0
    jenkinsapi         0.3.13
    keyring            23.0.1
    lxml               5.2.2
    pip                22.3.1
    pytz               2024.2
    pywin32            306
    pywin32-ctypes     0.2.3
    requests           2.32.3
    setuptools         65.5.1
    six                1.16.0
    soupsieve          2.5
    urllib3            2.2.3
    wheel              0.38.4
    zipp               3.21.0
