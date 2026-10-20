<p align="center"><a href="README.md">English</a> · <strong>Русский</strong></p>

<p align="center">
  <img src="docs/banner.svg" alt="TokenTrim — Сожмите код на 60-80% для промптов нейросетей" width="100%">
</p>

<p align="center">
  <a href="https://github.com/Palladiymateria/tokentrim/actions/workflows/tests.yml"><img src="https://img.shields.io/badge/tests-passing-10b981?style=flat&logo=githubactions&logoColor=white" alt="Тесты"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3.10 или новее">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-10b981?style=flat" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/runtime_dependencies-0-10b981?style=flat" alt="Ноль сторонних зависимостей">
  <a href="https://github.com/Palladiymateria/tokentrim/stargazers"><img src="https://img.shields.io/github/stars/Palladiymateria/tokentrim?style=flat" alt="GitHub stars"></a>
</p>

<p align="center">
  <strong>Сожмите вашу кодовую базу на 60–80% для контекстного окна LLM.</strong><br>
  Сохраняет сигнатуры, типы данных и интерфейсы, сворачивая внутреннюю логику реализации.<br>
  Без API-ключей, без отправки в сеть, без сторонних зависимостей.
</p>

<p align="center">
  <a href="#быстрый-старт">Быстрый старт</a> ·
  <a href="#до-и-после">До и после</a> ·
  <a href="#параметры">Параметры</a> ·
  <a href="#поддерживаемые-языки">Языки</a> ·
  <a href="#как-это-работает">Как это работает</a>
</p>

---

<p align="center">
  <img src="docs/terminal.svg" alt="Интерактивная сессия TokenTrim" width="100%">
</p>

## Зачем нужен TokenTrim?

При работе с ИИ-ассистентами (Claude, ChatGPT, Cursor, DeepSeek, Copilot) копирование файлов целиком быстро забивает контекстное окно, увеличивает задержку ответа, ухудшает точность рассуждений модели и стоит реальных денег.

В 90% сценариев **модели не нужна реализация каждого вспомогательного цикла** — ей нужны:
* **Сигнатуры функций и методов**
* **Аннотации типов и возвращаемые значения**
* **Структуры классов и датаклассы**
* **Docstrings и контракты API**

**TokenTrim** использует нативный синтаксический анализ (AST), удаляя внутренности функций и бойлерплейт, оставляя код **синтаксически валидным** и понятным для языковых моделей.

---

## До и после

### Исходный Python (52 строки · ~460 токенов)
```python
class PaymentProcessor:
    """Обрабатывает регулярные платежи и повторные попытки списания."""

    def __init__(self, api_key: str, max_retries: int = 3):
        self.api_key = api_key
        self.max_retries = max_retries
        self._session = self._init_session()

    def charge(self, user_id: str, amount_cents: int) -> TransactionResult:
        """Списывает средства с карты пользователя с экспоненциальной задержкой."""
        for attempt in range(self.max_retries):
            try:
                raw_resp = self._session.post(
                    "https://api.stripe.com/v1/charges",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"customer": user_id, "amount": amount_cents},
                )
                if raw_resp.status_code == 200:
                    return TransactionResult(status="success", id=raw_resp.json()["id"])
            except NetworkError as err:
                time.sleep(2 ** attempt)
        raise PaymentFailedError(f"Failed to charge user {user_id}")
```

### Сжатый скелет (12 строк · ~85 токенов — **экономия 81.5%**)
```python
class PaymentProcessor:
    """Обрабатывает регулярные платежи и повторные попытки списания."""

    def __init__(self, api_key: str, max_retries: int=3):
        ...

    def charge(self, user_id: str, amount_cents: int) -> TransactionResult:
        """Списывает средства с карты пользователя с экспоненциальной задержкой."""
        ...
```
*(Обратите внимание: документация, типы аргументов и имена методов полностью сохранены, а внутренняя реализация свернута в идиоматическое многоточие Python `...`)*

---

## Быстрый старт

Требуется **Python 3.10 или новее**. Работает на Windows, macOS и Linux без установки внешних библиотек.

### 1. Клонирование репозитория
```sh
git clone https://github.com/Palladiymateria/tokentrim.git
cd tokentrim
```

### 2. Мгновенный запуск
Без установки зависимостей:

```sh
# Сжать файл и скопировать прямо в буфер обмена
python -m tokentrim src/services/auth.py --clip

# Сжать всю директорию с выводом статистики экономии токенов
python -m tokentrim src/ --stats

# Удалить docstrings для экстремального сжатия
python -m tokentrim src/ --no-docstrings --clip
```

### 3. (Опционально) Установка в систему через pip
```sh
pip install -e .
tokentrim src/api/users.py --clip -s
```

---

## Параметры командной строки

```text
использование: tokentrim [-h] [-c] [-o FILE] [-s] [--no-docstrings] [-e EXCLUDE] [--json] [-v] [target]

Сжимает кодовую базу на 60-80% для контекстных окон LLM. Ноль зависимостей, 100% локально.

позиционные аргументы:
  target                Путь к файлу или папке (по умолчанию: текущая папка)

опции:
  -h, --help            Показать справку
  -c, --clip            Скопировать результат прямо в буфер обмена системы
  -o FILE, --output FILE
                        Записать результат в указанный файл
  -s, --stats           Вывести таблицу со статистикой экономии строк и токенов
  --no-docstrings       Удалить docstrings для максимального сокращения токенов
  -e, --exclude PATTERN Шаблон исключения (можно указывать несколько раз)
  --json                Вывести результат в формате JSON
  -v, --version         Показать версию утилиты
```

---

## Поддерживаемые языки

| Язык | Расширения | Что сохраняется |
| :--- | :--- | :--- |
| **Python** | `.py` | AST: классы, датаклассы, методы, функции, типы, декораторы, docstrings, `__all__` |
| **TypeScript** | `.ts`, `.tsx` | Интерфейсы, типы, классы, сигнатуры функций |
| **JavaScript** | `.js`, `.jsx`, `.mjs` | Классы, экспортируемые функции, сигнатуры методов |
| **Go** | `.go` | Пакеты, импорты, структуры, интерфейсы, сигнатуры func |
| **Rust** | `.rs` | Трейты, структуры, перечисления (enum), блоки impl, сигнатуры fn |

---

## Линейка инструментов Palladiymateria

`tokentrim` органично дополняет другие инструменты экосистемы:
* [**RepoMap**](https://github.com/Palladiymateria/repomap) — Превращает дерево файлов проекта в единый структурированный контекстный файл.
* [**ShareCheck**](https://github.com/Palladiymateria/sharecheck) — Локальный аудит безопасности перед публикацией репозитория на GitHub.
* [**TokenTrim**](https://github.com/Palladiymateria/tokentrim) — Сжимает файлы в компактные скелеты для контекстных окон нейросетей.

---

## Тестирование

Запуск тестов через стандартный модуль `unittest`:

```sh
python -m unittest discover -s tests -v
```

---

## Лицензия

[MIT](LICENSE) © 2026 Palladiy
