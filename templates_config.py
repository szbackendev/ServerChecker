from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

# Инициализируем среду с помощью загрузчика каталогов
# Это говорит Jinja2 искать шаблоны в папке templates
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True
)

templates = Jinja2Templates(env=env)