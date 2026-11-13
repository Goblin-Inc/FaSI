<div align="center">

# ⚡ FaSI — Fast Search Images

**Молниеносный десктопный оверлей для поиска, просмотра и копирования изображений по хоткею `Alt+Space` на базе PyQt6 и нативного ядра C++17 (`libfasi_core.so`)**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![C++17](https://img.shields.io/badge/C++-17-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)](https://isocpp.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Release](https://img.shields.io/github/v/release/Goblin-Inc/FaSI?style=for-the-badge&color=6366f1)](https://github.com/Goblin-Inc/FaSI/releases)

<br/>

![FaSI Desktop Overlay Preview](assets/screenshots/fasi_preview.png)

</div>

---

## 📖 О проекте

**FaSI (Fast Search Images)** — легковесный гибридный лаунчер и оверлей в стиле Spotlight / Rofi для Linux (X11 / Wayland / KDE Plasma), созданный для мгновенного поиска референсов, обоев, иконок и иллюстраций прямо поверх активных окон без открытия тяжёлого браузера.

### ✨ Ключевые возможности
- **Мгновенный вызов (`Alt+Space` / `SIGUSR1`)**: работает в режиме единого процесса (Single-Instance daemon). Повторный запуск бинарника или нажатие хоткея отправляет сигнал `SIGUSR1` уже запущенному процессу и открывает окно за **< 10 мс**.
- **Гибридное ядро Python + C++17 (`libfasi_core.so`)**:
  - Нативный модуль `cpp_core/image_cache.cpp` отвечает за быструю генерацию FNV-1a (64-bit) ключей кэша и низкоуровневое управление дисковым пулом превью.
  - Многопоточный `ImageLoader` (`QThreadPool`) асинхронно загружает миниатюры параллельно без единого фриза интерфейса.
- **Мульти-провайдерный поиск с авто-фоллбэком**:
  - Поддержка **Yandex Images**, **Google / Bing Images** и **DuckDuckGo Images** с переключением в 1 клик.
  - Интеллектуальная очистка поискового запроса (`clean_query`) — автоматически отсекает лишние разговорные слова (*«найди фото...», «покажи картинку...»*).
- **Встроенный Lightbox и буфер обмена**:
  - Клик по карточке открывает полноразмерное превью с метаданными и разрешением.
  - Копирование самой картинки (`QPixmap`) или прямой ссылки (`URL`) в системный буфер обмена одним нажатием.

---

## ⌨️ Горячие клавиши и управление

| Клавиша / Действие | Описание |
|---|---|
| `Alt + Space` | Показать / скрыть оверлей FaSI поверх всех окон |
| `Enter` | Запустить поиск по введённому запросу |
| `Клик по карточке` | Открыть полноразмерное превью изображения (`ImagePreviewDialog`) |
| `Copy Image` | Скопировать само изображение в системный буфер обмена (`Ctrl+V` в Discord / Telegram / GIMP) |
| `Copy URL` | Скопировать прямую ссылку на оригинал изображения |
| `Download` | Сохранить оригинал изображения на диск |
| `Esc` | Закрыть окно превью или свернуть оверлей в фоновый режим |

---

## 🏗️ Архитектура проекта

```
FaSI/
├── main.py                  # Single-Instance демон (/tmp/fasi_app.pid), обработка SIGUSR1, системный трей
├── ui/
│   ├── main_window.py       # Главное безрамочное окно с тенью, строкой поиска и 4-колоночной сеткой
│   ├── widgets.py           # Кастомные карточки ImagePreviewWidget и модальное окно просмотра
│   └── styles.py            # Тёмная тема оформления (QSS) в стиле Deep Indigo / Glassmorphism
├── core/
│   ├── search_engine.py     # Мульти-движок парсинга (Yandex, Google/Bing, DuckDuckGo) + очистка запросов
│   ├── image_loader.py      # Пул потоков QRunnable + привязка ctypes к нативной библиотеке C++17
│   └── settings.py          # Конфигурация провайдеров, таймаутов и лимитов выдачи
├── cpp_core/
│   ├── image_cache.cpp      # C++17 модуль: 64-bit FNV-1a хэширование URL и аудит дискового кэша
│   └── CMakeLists.txt       # Сборка разделяемой библиотеки libfasi_core.so
└── assets/
    └── fasi.svg             # Векторная иконка приложения для KDE / GNOME
```

---

## 📦 Установка и запуск

### Вариант 1: Готовый `.deb` пакет (Рекомендуется для Ubuntu / Debian / KDE Neon)
Перейдите в раздел [**Releases**](https://github.com/Goblin-Inc/FaSI/releases), скачайте `fasi_1.0.0_amd64.deb` и установите:

```bash
sudo dpkg -i fasi_1.0.0_amd64.deb
sudo apt-get install -f
```
После установки **FaSI** появится в меню приложений KDE/GNOME и будет доступен по команде `fasi`.

### Вариант 2: Portable-архив или запуск из исходников
```bash
git clone https://github.com/Goblin-Inc/FaSI.git
cd FaSI

# Сборка нативного C++17 модуля (опционально, предсобранный libfasi_core.so уже включён)
g++ -O3 -shared -fPIC cpp_core/image_cache.cpp -o cpp_core/libfasi_core.so

# Установка зависимостей и запуск
pip install -r requirements.txt
python3 main.py
```

---

## 📋 Changelog

### `v1.0.0` — Первый публичный релиз *(Текущая версия)*
- **Добавлено**: Нативное C++17 ядро `libfasi_core.so` с привязкой через `ctypes` и автоматическим Python-fallback.
- **Добавлено**: Мгновенное переключение видимости окна через UNIX-сигнал `SIGUSR1` и иконка в системном трее.
- **Добавлено**: Трёхкаскадный поисковый движок (`Yandex`, `Google/Bing`, `DuckDuckGo`) с фильтрацией естественного языка.
- **Добавлено**: Официальный `.deb` инсталлятор, SVG-иконка и `.desktop` интеграция для Linux.

---

<div align="center">
Разработано <a href="https://github.com/Goblin-Inc">@Goblin-Inc</a>
</div>
