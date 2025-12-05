import sys
import io
import logging
import functools
import requests
import unittest
import json
from requests.exceptions import RequestException

# 1. Реализация декоратора logger
def logger(func=None, *, handle=sys.stdout):
    """
    Параметризуемый декоратор для логирования вызовов функций.
    handle: sys.stdout, io.StringIO, logging.Logger
    """
    if func is None:
        # Если handle передан, возвращаем частично применённый декоратор
        return lambda f: logger(f, handle=handle)

    @functools.wraps(func)
    def inner(*args, **kwargs):
        # Определяем тип обработчика
        is_logging_obj = hasattr(handle, 'info') and hasattr(handle, 'error')

        # Формируем строку аргументов
        args_str = ', '.join(map(repr, args))
        kwargs_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args_str = ', '.join(filter(None, [args_str, kwargs_str]))

        # Логируем старт вызова
        start_msg = f"INFO: Calling {func.__name__}({all_args_str})\n"
        if is_logging_obj:
            handle.info(f"Calling {func.__name__}({all_args_str})")
        else:
            handle.write(start_msg)

        try:
            result = func(*args, **kwargs)
            # Логируем успешное завершение
            success_msg = f"INFO: {func.__name__} returned {result!r}\n"
            if is_logging_obj:
                handle.info(f"{func.__name__} returned {result!r}")
            else:
                handle.write(success_msg)
            return result
        except Exception as e:
            # Логируем ошибку
            error_msg = f"ERROR: {func.__name__} raised {type(e).__name__}: {e}\n"
            if is_logging_obj:
                handle.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            else:
                handle.write(error_msg)
            # Повторно выбрасываем исключение
            raise

    return inner


# 2. Реализация функции get_currencies (только бизнес-логика, без handle)
def get_currencies(currency_codes: list, url="https://www.cbr-xml-daily.ru/daily_json.js") -> dict:
    """
    Получает курсы валют по кодам из API ЦБ РФ.
    Возвращает словарь {код_валюты: курс}.
    Выбрасывает исключения в случае ошибок.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Возбуждает исключение при HTTP ошибках (4xx, 5xx)
    except RequestException as e:
        # API недоступен
        raise ConnectionError(f"API недоступен: {e}")

    try:
        data = response.json()
    except json.JSONDecodeError:
        # Некорректный JSON
        raise ValueError("Ответ API содержит некорректный JSON")

    if "Valute" not in data:
        # Нет ключа “Valute”
        raise KeyError("В ответе API отсутствует ключ 'Valute'")

    valute_data = data["Valute"]
    result = {}

    for code in currency_codes:
        if code not in valute_data:
            # Валюта отсутствует в данных
            raise KeyError(f"Валюта '{code}' отсутствует в данных API")

        currency_info = valute_data[code]
        # Проверяем, что поле 'Value' существует и имеет числовой тип
        value = currency_info.get("Value")
        if value is None or not isinstance(value, (int, float)):
            # Курс валюты имеет неверный тип
            raise TypeError(f"Курс валюты '{code}' имеет неверный тип или отсутствует")

        result[code] = value

    return result


# 3. Оборачивание функции в декоратор
@logger(handle=sys.stdout)
def get_currencies_stdout(currency_codes: list, url="https://www.cbr-xml-daily.ru/daily_json.js") -> dict:
    return get_currencies(currency_codes, url)


# 4. Самостоятельная часть - файл-логирование
# Настройка логгера для записи в файл
file_logger = logging.getLogger("currency_file")
file_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("currency_requests.log", mode='w', encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
file_logger.addHandler(file_handler)

@logger(handle=file_logger)
def get_currencies_file_log(currency_codes: list, url="https://www.cbr-xml-daily.ru/daily_json.js") -> dict:
    return get_currencies(currency_codes, url)


# 5. Демонстрационный пример: квадратное уравнение
import math

def solve_quadratic_logger(func=None, *, handle=sys.stdout):
    """
    Специальный декоратор для квадратного уравнения, реализующий разные уровни логирования.
    """
    if func is None:
        return lambda f: solve_quadratic_logger(f, handle=handle)

    @functools.wraps(func)
    def inner(a, b, c):
        is_logging_obj = hasattr(handle, 'info') and hasattr(handle, 'error')

        start_msg = f"INFO: Calling solve_quadratic(a={a}, b={b}, c={c})\n"
        if is_logging_obj:
            handle.info(f"Calling solve_quadratic(a={a}, b={b}, c={c})")
        else:
            handle.write(start_msg)

        try:
            result = func(a, b, c)
            if result == ():
                # Нет решений
                msg = f"WARNING: solve_quadratic({a}, {b}, {c}) has no real solutions.\n"
                if is_logging_obj:
                    handle.warning(f"solve_quadratic({a}, {b}, {c}) has no real solutions.")
                else:
                    handle.write(msg)
            elif len(result) == 1:
                # Один корень
                msg = f"INFO: solve_quadratic({a}, {b}, {c}) has one solution: x = {result[0]:.2f}\n"
                if is_logging_obj:
                    handle.info(f"solve_quadratic({a}, {b}, {c}) has one solution: x = {result[0]:.2f}")
                else:
                    handle.write(msg)
            else: # len(result) == 2
                # Два корня
                msg = f"INFO: solve_quadratic({a}, {b}, {c}) has two solutions: x1 = {result[0]:.2f}, x2 = {result[1]:.2f}\n"
                if is_logging_obj:
                    handle.info(f"solve_quadratic({a}, {b}, {c}) has two solutions: x1 = {result[0]:.2f}, x2 = {result[1]:.2f}")
                else:
                    handle.write(msg)

            success_msg = f"INFO: solve_quadratic returned {result}\n"
            if is_logging_obj:
                handle.info(f"solve_quadratic returned {result}")
            else:
                handle.write(success_msg)
            return result
        except Exception as e:
            error_msg = f"ERROR: solve_quadratic raised {type(e).__name__}: {e}\n"
            if is_logging_obj:
                handle.error(f"solve_quadratic raised {type(e).__name__}: {e}")
            else:
                handle.write(error_msg)
            raise

    return inner

@solve_quadratic_logger
def solve_quadratic(a, b, c):
    """Решает квадратное уравнение ax^2 + bx + c = 0."""
    if not all(isinstance(i, (int, float)) for i in [a, b, c]):
        raise TypeError("Коэффициенты должны быть числами")
    if a == 0:
        if b == 0:
            if c == 0:
                # 0 = 0, все x подходят
                raise ValueError("Уравнение имеет бесконечно много решений")
            else:
                # c != 0, но 0 = c, нет решений
                return ()
        else:
            # bx + c = 0 -> x = -c/b
            return (-c / b,)
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return ()
    elif discriminant == 0:
        return (-b / (2*a),)
    else:
        sqrt_disc = math.sqrt(discriminant)
        x1 = (-b + sqrt_disc) / (2*a)
        x2 = (-b - sqrt_disc) / (2*a)
        return (x1, x2)


# 6. Тестирование
# class TestGetCurrencies(unittest.TestCase):
#     def test_valid_currencies(self):
#         """Проверка корректного возврата реальных курсов."""
#         # Тестируем с фиксированным URL, который всегда возвращает валидный JSON с USD и EUR
#         # Для демонстрации просто проверим, что при валидных кодах не возникает исключений
#         try:
#             result = get_currencies(['USD', 'EUR'])
#             self.assertIsInstance(result, dict)
#             self.assertIn('USD', result)
#             self.assertIn('EUR', result)
#             self.assertIsInstance(result['USD'], (int, float))
#             self.assertIsInstance(result['EUR'], (int, float))
#         except (ConnectionError, ValueError, KeyError, TypeError):
#             # API может быть недоступно, но тест не должен падать из-за этого
#             self.skipTest("API недоступно для теста корректных данных")
#
#     def test_nonexistent_currency(self):
#         """Проверка поведения при несуществующей валюте."""
#         with self.assertRaises(KeyError):
#             get_currencies(['INVALID123'])
#
#     def test_connection_error(self):
#         """Проверка выброса ConnectionError."""
#         with self.assertRaises(ConnectionError):
#             get_currencies(['USD'], url="https://thisurldoesnotexist12345.com")
#
#     def test_json_error(self):
#         """Проверка выброса ValueError при некорректном JSON."""
#         with self.assertRaises(ValueError):
#             get_currencies(['USD'], url="https://httpbin.org/html") # Возвращает HTML, не JSON
#
#     def test_missing_valute_key(self):
#         """Проверка выброса KeyError при отсутствии ключа Valute."""
#         # Используем URL, который возвращает JSON, но без ключа 'Valute'
#         with self.assertRaises(KeyError):
#             get_currencies(['USD'], url="https://httpbin.org/json") # Возвращает {"slideshow": ...}
#
#
# class TestLoggerDecorator(unittest.TestCase):
#     def setUp(self):
#         self.stream = io.StringIO()
#
#     def test_logging_success(self):
#         """Проверка логов при успешном выполнении."""
#         @logger(handle=self.stream)
#         def test_func(x):
#             return x * 2
#
#         result = test_func(5)
#         self.assertEqual(result, 10)
#
#         logs = self.stream.getvalue()
#         self.assertIn("INFO: Calling test_func(5)", logs)
#         self.assertIn("INFO: test_func returned 10", logs)
#
#     def test_logging_error(self):
#         """Проверка логов при ошибке."""
#         @logger(handle=self.stream)
#         def test_func_error():
#             raise ValueError("Test error")
#
#         with self.assertRaises(ValueError):
#             test_func_error()
#
#         logs = self.stream.getvalue()
#         self.assertIn("ERROR: test_func_error raised ValueError: Test error", logs)
#
#     def test_stream_write(self):
#         """Пример теста с контекстом из задания."""
#         self.stream = io.StringIO()
#         @logger(handle=self.stream)
#         def wrapped():
#             return get_currencies(['USD'], url="https://invalid")
#         self.wrapped = wrapped
#
#         with self.assertRaises(ConnectionError):
#             self.wrapped()
#         logs = self.stream.getvalue()
#         self.assertIn("ERROR", logs)
#         self.assertIn("ConnectionError", logs)


# Демонстрация работы
if __name__ == "__main__":
    print("--- Демонстрация get_currencies с stdout ---")
    try:
        # Этот вызов будет логировать в stdout
        # rates = get_currencies_stdout(['USD', 'EUR'])
        # print(f"Полученные курсы: {rates}\n")
        pass
    except Exception as e:
        print(f"Ошибка при получении курсов: {e}\n")

    print("--- Демонстрация solve_quadratic с разными уровнями ---")
    # INFO: Два корня
    solve_quadratic(1, -3, 2) # x^2 - 3x + 2 = 0 -> x=1, x=2
    # WARNING: Нет решений
    solve_quadratic(1, 0, 1) # x^2 + 1 = 0
    # ERROR: Некорректный тип
    try:
        solve_quadratic("abc", 1, 1)
    except TypeError:
        pass # Исключение проброшено, как и ожидалось
    except ValueError:
        pass # Исключение проброшено, как и ожидалось
        # CRITICAL: Бесконечно много решений (a=0, b=0, c=0)
    try:
        solve_quadratic(0, 0, 0)  # 0 = 0
    except TypeError:  # float('inf') не является кортежем, вызывает TypeError в логгере
        # Повторный вызов через обернутую функцию для демонстрации логирования CRITICAL
        solve_quadratic_logger(handle=sys.stdout)(lambda a, b, c: float('inf'))(0, 0, 0)
    print("\n--- Запуск тестов ---")
    unittest.main(argv=[''], exit=False, verbosity=2)

    print("\n--- Демонстрация get_currencies с файловым логированием ---")
    try:
        # Этот вызов будет логировать в файл currency_requests.log
        rates_file = get_currencies_file_log(['USD'])
        print(f"Курсы (файл): {rates_file}")
    except Exception as e:
        print(f"Ошибка при получении курсов (файл): {e}")
