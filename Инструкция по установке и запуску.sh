# Создайте папку проекта
mkdir hh_parser_site
cd hh_parser_site

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте структуру папок
mkdir templates static

# Скопируйте все файлы в соответствующие папки

# Запустите приложение
python app.py