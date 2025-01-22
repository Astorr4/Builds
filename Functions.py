import os
import re
import glob
import logging
import keyring
import requests
import subprocess
from bs4 import BeautifulSoup
from datetime import datetime
import win32com.client as win32
from urllib3 import disable_warnings
from jenkinsapi.jenkins import Jenkins
from logging.handlers import RotatingFileHandler
# Пути до программ и файлов
putty = r"C:\Program Files\PuTTY\\"
path_zip = r"C:\Program Files\7-Zip\\"
logs = r"C:\PyCharm Project\Builds\Logs\Logs.log"
build = r"C:\PyCharm Project\Builds\Logs\Builds.log"
path_to_artefact = r"C:\PyCharm Project\Builds\Files\\"
user = "user1"
mail = ['login@domain.ru']
'''-----------------------------------------Настройка логирования----------------------------------------------------'''
# Настройка обработчика RotatingFileHandler
file_handler = RotatingFileHandler(
    logs, maxBytes=1 * 1024 * 1024, backupCount=5, encoding="utf-8"
)  # 1 МБ
# Формат логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
# Настройка основного логгера
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат вывода
    handlers=[
        file_handler,  # Логирование в файл с ротацией
        logging.StreamHandler()  # Логирование в консоль
    ]
)
'''------------------------------------------------------------------------------------------------------------------'''
# Основная функция по копированию сборок


def copy_builds():
    '''------------------------------------------------Вводные данные------------------------------------------------'''
    # Логин для входа
    login = keyring.get_credential("Server", None).username
    # Пароль для входа
    password = keyring.get_password("Server", login)
    password_prod = keyring.get_password("Server-prod", login)
    # Список с информацией о серверах
    servers = {"Server1": ["11.111.11.111", "/data/share/deployment/Server1"],
               "Server2": ["22.222.22.222", "/data/share/deployment/Server2"],
               "Server3": ["33.333.33.333", "/data/share/deployment/Server3"],
               "Server4": ["44.444.44.444", "/data/share/deployment/Server4"],
               "Server5": ["55.555.55.555", "/data/share/deployment/Server5"]}
    '''--------------------------------------------------------------------------------------------------------------'''
    '''----------------------------------------------Работа с API Jenkins--------------------------------------------'''
    # Читаем установленную версию сбороки из логов
    with open(build, "r") as f:
        installed_build = int(f.read().strip())
    # Игнорирование предупреждений о проверке SSL сертификата
    disable_warnings()
    # Формируем ссылку на xml файл актуальной сборки прибавляя к номеру установленной 1
    xml_url = f'https://Jenkins/job/Builds/{installed_build + 1}/api/xml'
    # Пытаемся спарсить xml страницу актуальной сборки, если страницы еще не существует, то программа завершается
    try:
        # Создаем объект Jenkins
        jenkins = Jenkins("https://Jenkins/", username="admin",
                          password=keyring.get_password("Jenkins", "admin"), ssl_verify=False)
        # Получаем номер последней сборки из проекта "Builds"
        actual_build = jenkins.get_job("Builds").get_last_build().get_number()
        # Парсим данные из xml файла сборки
        response = requests.get(xml_url, auth=(
            'admin', keyring.get_password("Jenkins", "admin")), verify=False)
        # Сохраняем страницу в переменную и Создаем объект BeautifulSoup
        soup = BeautifulSoup(response.content, 'xml')
        # Парсим тэг
        tag = soup.find('Project').text
        # Парсим название папки с артефактом
        folder_artefact = tag.split('_', 1)[1].lower()
        # Парсим название артефакта
        artifact = [i.find('value').text for i in soup.find_all('parameter') if i.find('name').text == 'ARTIFACT_NAME'][
            0]
    except:  # Если сборка еще не вышла и страница не существует, то ловим ошибку
        # Пишем информацию в лог
        logging.info(
            f"Установлена последняя актуальная сборка - {installed_build}")
        # Завершаем работу скрипта
        exit()
    '''--------------------------------------------------------------------------------------------------------------'''
    '''--------------------------------------------Запись логов------------------------------------------------------'''
    # Если установленная версия меньше чем актуальная и это не Vanilla сборка
    if installed_build < actual_build and tag != 'Vanilla':
        # Записываем лог
        logging.info(f"Последняя установленная сборка - {installed_build}")
        logging.info(f"Следующая сборка - {installed_build + 1}")
        logging.info(f"Актуальная сборка - {actual_build}")
        logging.info(f"xml файл следующей сборки - {xml_url}")
        logging.info(f"Тэг следующей сборки - {tag}")
        # В файле с номером сборки обновляется номер установленной сборки
        with open(build, "w") as f:
            f.write(str(installed_build + 1))
    '''--------------------------------------------------------------------------------------------------------------'''
    # Очистка локальной папки с артефактом от старых файлов
    for file in glob.glob(os.path.join(f"{path_to_artefact}{folder_artefact}", "*")):
        try:
            os.remove(file)
        except:
            continue
    '''-------------------------------------Копирование сборки для прода-----------------------------------------'''
    if folder_artefact == "Server6":
        # Скачиваем артефакт
        process = subprocess.run(
            rf'"{putty}pscp.exe" -l {login} -pw {password} '
            rf'{login}@77.77.77.77:/data/share/deployment/{folder_artefact}/{artifact} '
            rf'"{path_to_artefact}{folder_artefact}"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode, f"Артефакт {artifact} скопирован на ПК",
                    f"Артефакт {artifact} НЕ скопирован на ПК. returncode - {process.returncode}")
        # Удаляются данные из папки с артефактами на сервере
        process = subprocess.run(
            fr'cmd /c echo y | "{putty}plink.exe" kpp-psmp -ssh -l {user}@{login}@Serv '
            fr'-pw {password_prod}@{password_prod}  "rm -f /data/share/Server6/*"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Папка с артефактами {folder_artefact} успешно очищена на сервере Serv",
                    f"Папка {folder_artefact} НЕ очищена. Код возврата - {process.returncode}")
        # Копируется артефакт на сервер
        process = subprocess.run(
            fr'echo y | "{putty}pscp.exe" -l {user}@{login}@Serv -pw {password}@{password} '
            fr'"{path_to_artefact}{folder_artefact}\{artifact}" '
            fr'"{user}@{login}@Serv@kpp-psmp:/data/share/Server6/"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Артефакт {folder_artefact} успешно скопирован на Serv",
                    f"Артефакт {folder_artefact} НЕ скопирован на Serv. returncode - {process.returncode}")
        # Распаковка артефакта на сервере
        process = subprocess.run(
            rf'cmd /c echo y | "{putty}plink.exe" "kpp-psmp" -ssh -l {user}@{login}@Serv '
            fr'-pw "{password_prod}@{password_prod}" "cd /data/share/Server6 && unzip -o {artifact}"',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Артефакт {folder_artefact} успешно распакован на Serv",
                    f"Артефакт {folder_artefact} НЕ распакован на Serv. returncode - {process.returncode}")
        # очищаем папку с тригером для устаноки сборки
        try:
            folder = r'N:\path\to\builds'
            os.remove(fr"{folder}\Server6.log")
            logging.info(f'Тригер на установку очищен в - {folder}')
        except Exception as error:
            logging.error(f'Ошибка при удалении триггера в {folder} - {error}')
        '''------------------------------------------------------------------------------------------------------'''
        '''--------------------------------Проверка дополнительных файлов----------------------------------------'''
        # Распаковка файла с настройками на ПК
        process = subprocess.run(
            rf'"{path_zip}7z.exe" x "{path_to_artefact}{folder_artefact}\{artifact}" '
            rf'-o"{path_to_artefact}{folder_artefact}\" gradle.properties -r',
            shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    "Файл с настройками успешно распакован на ПК",
                    f"Файл с настройками НЕ распакован на ПК. returncode - {process.returncode}")
        # парсинг файла с настройками
        data_config_prod = config_parser(
            f'{path_to_artefact}{folder_artefact}')
        # Достаем названия файлов с сервера
        server_files = subprocess.run(
            fr'cmd /c echo y | "{putty}plink.exe" "kpp-psmp" -ssh -l {user}@{login}@Serv '
            fr'-pw "{password_prod}@{password_prod}" find /data/share/deployment/ -type f',
            shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, server_files.returncode,
                    "Успешно получен список дополнительных файлов с сервера Serv",
                    f"Не получен список дополнительных файлов с сервера Serv. returncode - {server_files.returncode}")
        check_file(servers, server_files.stdout, data_config_prod, folder_artefact, login, password, password_prod,
                   logs, path_to_artefact, user)
        artifact_trigger(folder_artefact, artifact)
        # Отправка сообщения и запись логов о том, что сборка скопирована
        send_email_using_outlook(mail,
                                 f'Сборка {folder_artefact.upper()}_NEW скопирована на сервер - {artifact}',
                                 f'Сборка {folder_artefact.upper()}_NEW скопирована на сервер - {artifact}')
        logging.info(f'Сборка {folder_artefact} скопирована на сервер')
        '''------------------------------------------------------------------------------------------------------'''
    '''-------------------------------Копирование сборки для тестовых серверов-----------------------------------'''
    # Проверка есть ли папка артефакта в словаре с информацией о серверах
    if folder_artefact in servers.keys():
        # Скачиваем артефакт
        process = subprocess.run(
            rf'"{putty}pscp.exe" -l {login} -pw {password} '
            rf'{login}@77.77.77.777:/data/share/{folder_artefact}/{artifact} '
            rf'"{path_to_artefact}{folder_artefact}"',
            creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode, f"Артефакт {artifact} скопирован на ПК",
                    f"Артефакт {artifact} НЕ скопирован на ПК. returncode - {process.returncode}")
        # Удаляются данные из папки с артефактами на сервере
        process = subprocess.run(
            rf'"{putty}plink.exe" {servers[folder_artefact][0]} -ssh -l {login} -pw {password} rm '
            rf'-f {servers[folder_artefact][1]}/*',
            creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Папка с артефактами {folder_artefact} успешно очищена на сервере {servers[folder_artefact][0]}",
                    f"Папка {folder_artefact} НЕ очищена. Код возврата - {process.returncode}")
        # Копируется артефакт на сервер
        process = subprocess.run(
            rf'"{putty}pscp.exe" -l {login} -pw {password} "{path_to_artefact}{folder_artefact}\{artifact}" '
            rf'{login}@{servers[folder_artefact][0]}:{servers[folder_artefact][1]}"',
            creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Артефакт {folder_artefact} успешно скопирован на {servers[folder_artefact][0]}",
                    f"Артефакт {folder_artefact} НЕ скопирован на {servers[folder_artefact][0]}. returncode - {process.returncode}")
        # Распаковка артефакта на сервере
        process = subprocess.run(
            rf'"{putty}plink.exe" {servers[folder_artefact][0]} -ssh -l {login} -pw {password} '
            rf'"cd {servers[folder_artefact][1]}/ && unzip -o {artifact}"',
            creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    f"Артефакт {folder_artefact} успешно распакован на {servers[folder_artefact][0]}",
                    f"Артефакт {folder_artefact} НЕ распакован на {servers[folder_artefact][0]}. returncode - {process.returncode}")
        '''------------------------------------------------------------------------------------------------------'''
        '''-----------------------------------Проверка дополнительных файлов-------------------------------------'''
        # Распаковка файла с настройками на ПК
        process = subprocess.run(
            rf'"{path_zip}7z.exe" x "{path_to_artefact}{folder_artefact}\{artifact}" -o"{path_to_artefact}{folder_artefact}\" gradle.properties -r',
            creationflags=subprocess.CREATE_NO_WINDOW)
        check_error(folder_artefact, process.returncode,
                    "Файл с настройками успешно распакован на ПК",
                    f"Файл с настройками НЕ распакован на ПК. returncode - {process.returncode}")
        # парсинг файла с настройками
        data_config = config_parser(f'{path_to_artefact}{folder_artefact}')
        # Достаем названия файлов с сервера
        server_files = subprocess.run(
            fr'"{putty}plink.exe" {servers[folder_artefact][0]} -ssh -l {login} -pw {password} ls -1 "/data/share/"',
            shell=True, capture_output=True, text=True)
        check_error(folder_artefact, server_files.returncode,
                    f"Успешно получен список дополнительных файлов с сервера {servers[folder_artefact][0]}",
                    f"Не получен список дополнительных файлов с сервера {servers[folder_artefact][0]}. returncode - {server_files.returncode}")
        # Вызов функции check_file для проверки обновлений каждого из файлов
        check_file(servers, server_files.stdout, data_config, folder_artefact, login, password, password_prod, logs,
                   path_to_artefact, user)
        artifact_trigger(folder_artefact, artifact)
        # Отправка сообщения и запись логов о том, что сборка скопирована
        send_email_using_outlook(mail,
                                 f'Сборка {folder_artefact.upper()}_NEW скопирована на сервер - {artifact}',
                                 f'Сборка {folder_artefact.upper()}_NEW скопирована на сервер - {artifact}')
        logging.info(f'Сборка {folder_artefact} скопирована на сервер')
    '''--------------------------------------------------------------------------------------------------------------'''
# Функция проверяет обновление дополнительных файлов


def check_file(servers: dict, serverFiles: str, data_config, folder, login, password, password_prod, logs, path, gpbu):
    # Словарь, в котором лежат пути на севере для каждого из проверяемых файлов
    files = {"File": "/data/nexus/storage/installation/",
             "jboss": "/data/jboss/jboss/",
             "monitor": "/data/monitoring/",
             "webFile": "/data/Web/"}
    for filename in ["File", "jboss", "monitor", "webFile"]:
        # Сплитуем из пути название файла
        file = data_config[filename].split('/')[-1]
        fileVer = data_config[filename.replace("File", "Ver")]
        # если последней версии файла нет в списке файлов с сервера
        if file not in serverFiles:
            send_email_using_outlook(mail,
                                     f"Существует новая версия файла {filename}. Ожидается копирование.",
                                     f"Существует новая версия файла - {filename}")
            # Скачиваем файл с сервера на локальный ПК
            process = subprocess.run(
                rf'"{putty}pscp.exe" -l {login} -pw {password} {login}@88.88.88.88:{files[filename]}{fileVer}/{file} "{path}{folder}"''',
                shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            check_error(folder, process.returncode,
                        f"Файл {file} успешно скопирован на ПК",
                        f"Файл {file} НЕ скопирован на ПК. returncode - {process.returncode}")
            # Если сборка прома то подключаемся через КПП и качаем файл на сервер
            if folder == 'Server6':
                process = subprocess.run(
                    rf'cmd /c echo y | "{putty}pscp.exe" -l "{user}@{login}@Serv" -pw '
                    rf'"{password_prod}@{password_prod}" "{path}{folder}\{file}" "{user}@{login}@clp-p04asl@kpp-psmp:/data/share"',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                check_error(folder, process.returncode,
                            f"Файл {file} успешно скопирован на сервер clp-p04asl",
                            f"Файл {file} НЕ скопирован на сервер clp-p04asl. returncode - {process.returncode}")
            else:
                # Скачиваем файл на тестовый сервер
                process = subprocess.run(
                    rf'"{putty}pscp.exe" -l {login} -pw {password} "{path}{folder}\{file}" {login}@{servers[folder][0]}:/data/share/"',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                check_error(folder, process.returncode,
                            f"Файл {file} успешно скопирован на сервер {servers[folder[0]]}",
                            f"Файл {file} НЕ скопирован на сервер {servers[folder[0]]}. returncode - {process.returncode}")
            # Отправляем письмо и пишем логи
            send_email_using_outlook(mail,
                                     f"Файл для {folder.upper()}_NEW скопирован на сервер {filename}",
                                     f"Файл для {folder.upper()}_NEW скопирован на сервер - {filename}")
            logging.info(
                f"Файл для {folder.upper()}_NEW скопирован на сервер - {filename}")
        else:
            logging.error(f"Новых версий файла {file} не существует")
# Функция отправляет сообщения на почту. Принимает адреса почты в виде списка, текст сообщения, текст темы и файлы.


def send_email_using_outlook(email, mail_text, subject="", attach_filename=None):
    try:
        # Создание объекта Outlook
        outlook = win32.Dispatch('outlook.application')
        # Замена текста
        replacements = {
            "Cloud3": "&#127945", "BuildUAT1": "&#9917",
            "Cloud2": "&#9918", "CloudQA_PC": "&#127934",
            "Cloud1": "&#9917", "BuildUAT3": "&#127945",
            "UA": "&#9917", "UAT2_PC_NEW": "&#9918",
            "UANEW": "&#127945", "UAT4_PC_NEW": "&#127952",
            "QANEW": "&#127934", "ASMBK_PC_NEW": "&#127936",
            "Файл дампа на": "&#8252", "ERROR": "&#8252",
            "FATAL": "&#9940", "установлена и запущена": "&#9989",
            "скопирована на сервер": "&#128230", "Не получилось запустить": "&#129488",
            "запущен с ОШИБКАМИ": "&#128219", "не успешно": "&#128219",
            "установлена": "&#128077", "успешно завершен": "&#128077",
            "запущен": "&#128077", "установка начата": "&#129310"
        }
        # Применение замен в тексте письма
        original_mail_text = mail_text
        for key, value in replacements.items():
            if key in mail_text:
                mail_text = value + "; " + mail_text if key in ["Cloud3", "Build1", "Cloud2",
                                                                "CloudQA", "Cloud1", "Build3",
                                                                "Файл дампа на", "UA1_NEW", "UA2_NEW",
                                                                "UA3NEW", "UA4NEW",
                                                                "QANEW",
                                                                "Server6NEW"] else mail_text + " " + value
        # Проверка вложения
        if attach_filename:
            if os.path.isfile(attach_filename) and os.path.getsize(attach_filename) > 7000000:
                attach_filename = None
        # Создание и отправка письма
        mail = outlook.CreateItem(0)
        mail.To = ";".join(email)
        mail.Subject = subject
        mail.HTMLBody = mail_text
        if attach_filename:
            mail.Attachments.Add(attach_filename)
        mail.Send()
        return True
    except Exception as e:
        logging.error(f"Не удалось отправить письмо: {e}")
        return False
# Функция парсит переменные из файла gradle.properties в виде словаря "Переменная" : "Значение"


def config_parser(path: str):
    # Создается пустой словарь
    properties = {}
    # Открывается файл с настройками
    with open(fr'{path}\gradle.properties', 'r') as file:
        # Проходим по каждой строке файла
        for line in file:
            # Пропуск комментариев и пустых строк
            if line.strip() and not line.startswith('#'):
                # Строка разделяется на название переменной и ее значение
                key, value = line.strip().split('=', 1)
                # Добавляется в словарь
                properties[key] = value
    # Возвращается словарь со всеми переменными файла
    return properties
# Функция ловит ошибки, записывает логи и завершает работу скрипта


def check_error(folder_artefact, command, text, text_err, command_code=(0, 1)):
    # Если команда возвращает код 0 или 1 то все успешно
    if command in command_code:
        logging.info(text)
    # в остальных случаях это ошибка, пишет логи, отправляет письмо и завершает работу скрипта
    else:
        logging.error(text_err)
        send_email_using_outlook(mail,
                                 f'Сборка {folder_artefact.upper()}_NEW НЕ скопирована на сервер',
                                 f'Сборка {folder_artefact.upper()}_NEW НЕ скопирована на сервер')
        exit()


def artifact_trigger(folder_artefact, artifact):
    pattern = re.compile(rf"artifact.*\.{folder_artefact}.*\.zip")
    for filename in os.listdir(r'C:\path\to\builds'):
        file_path = os.path.join(r'C:\path\to\builds', filename)
        if os.path.isfile(file_path) and pattern.match(filename):
            os.remove(file_path)
    open(fr'C:\path\to\builds\{artifact}', 'w')
