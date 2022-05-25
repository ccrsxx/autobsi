import os
import time
import logging

from PIL import Image
from typing import Type, Union, Callable, Any
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .utils import get_elapsed_time
from .mail import send_mail


class Base:
    def __init__(self, verbose: bool, cloud: bool):
        options = webdriver.ChromeOptions()

        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        if not verbose:
            options.add_argument('headless')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')

        chromedriver_location = os.path.join('bin', 'chromedriver.exe')

        if cloud:
            options.binary_location = os.getenv('GOOGLE_CHROME_BIN')
            chromedriver_location = os.getenv('CHROMEDRIVER_PATH')  # type: ignore

        if not os.path.exists(chromedriver_location):
            raise Exception('chromedriver not found. Please install it first!')

        self.driver = webdriver.Chrome(
            executable_path=chromedriver_location,
            options=options,
            service_log_path='NUL',
        )

    def visit(self, url: str):
        self.driver.get(url)

    def input_keys(self, method: By, elem: str, keys: str):
        self.driver.find_element(method, elem).send_keys(keys)

    def click(self, method: By, elem: str):
        self.driver.find_element(method, elem).click()

    def rename_logger(self, data_log: str):
        old_name = os.path.join('logs', 'temp.txt')
        new_name = os.path.join('logs', f'{data_log}.txt')

        filehandler = logging.FileHandler(new_name, 'w')
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')

        filehandler.setFormatter(formatter)

        log = logging.getLogger()

        for handler in log.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                log.removeHandler(handler)

        log.addHandler(filehandler)

        if os.path.exists(old_name):
            os.remove(old_name)

    def check_element(
        self,
        method: By,
        elem: str,
        error: str,
        wait: int = 10,
        condition: Type = EC.presence_of_element_located,
    ):
        try:
            element = WebDriverWait(self.driver, wait).until(condition((method, elem)))
        except TimeoutException:
            raise Exception(error)
        return element

    def check_exists(self, method: By, elem: str):
        try:
            element = self.driver.find_element(method, elem)
        except NoSuchElementException:
            return False
        return element

    def save_screenshot(self, data_log: str, error: bool):
        img_name = os.path.join('screenshots', f'{data_log}.png')
        log_name = os.path.join('logs', f'{data_log}.txt')
        self.driver.set_window_size(1920, 1080)
        self.driver.find_element(By.TAG_NAME, 'body').screenshot(img_name)
        self.driver.get_screenshot_as_file(img_name)
        if not error:
            Image.open(img_name).crop((80, 100, 1900, 330)).save(img_name)
        return img_name, log_name


class Attend(Base):
    def __init__(
        self,
        day: str,
        session: Union[None, int],
        get: Callable[[str], Any],
        verbose: bool,
        cloud: bool,
    ):
        super().__init__(verbose, cloud)

        (
            self.timetable,
            self.username,
            self.password,
            self.login_url,
            self.login_locator,
            self.attend_locator,
        ) = [
            get(key)
            for key in (
                'timetable',
                'username',
                'password',
                'login_url',
                'login_locator',
                'attend_locator',
            )
        ]

        self.class_name, self.class_link = [
            self.timetable[day][key][session]
            if session is not None
            else self.timetable[day][key]
            for key in ('name', 'link')
        ]

        self.data_log = f'{datetime.now().strftime("%d %b")} - {self.class_name}'
        self.rename_logger(self.data_log)

    def login(self):
        try:
            self.visit(self.login_url)
            self.check_element(
                By.XPATH,
                self.login_locator['login_button'],
                error='Site Down',
                condition=EC.element_to_be_clickable,
            )
        except Exception as _:
            raise Exception('Site Down')

        for key in ('username', 'password'):
            self.input_keys(
                By.CSS_SELECTOR,
                self.login_locator[f'{key}_input'],
                getattr(self, key),
            )

        self.click(By.XPATH, self.login_locator['login_button'])

    def get_button_status(self):
        try:
            self.check_element(
                By.CSS_SELECTOR, '#sidebar', error='Attendance page error!'
            )
        except Exception as _:
            return 'Site Down'
        if ready := self.check_exists(By.XPATH, self.attend_locator['ready']):
            return ready.text
        return self.driver.find_element(By.XPATH, self.attend_locator['not_ready']).text

    def check_next_class(self):
        current_time, today = (
            datetime.now().strftime('%H:%M'),
            datetime.now().strftime('%A').lower(),
        )

        next_class = False
        class_schedule = self.timetable[today]['time']

        if any(isinstance(nest, list) for nest in class_schedule):
            for start, _ in class_schedule:
                if current_time < start:
                    next_class = start
                    break

        if next_class:
            elapsed_time = get_elapsed_time(
                (
                    datetime.strptime(next_class, '%H:%M')
                    - datetime.strptime(current_time, '%H:%M')
                ).seconds
            )
            return logging.info(f'Next class starts in {elapsed_time}')

        return logging.info('No more class today')


def attend_class(
    get: Callable[[str], Any],
    mail: bool,
    verbose: bool,
    cloud: bool,
):
    timetable = get('timetable')
    today = datetime.now().strftime('%A').lower()

    if today not in timetable:
        return logging.info('No class today')

    next_class, next_check = False, False

    class_schedule = timetable[today]['time']
    current_time = datetime.now().strftime('%H:%M')

    if any(isinstance(nest, list) for nest in class_schedule):
        for session, (start, end) in enumerate(class_schedule):
            if start <= current_time < end:
                job(today, session, get, mail, verbose, cloud)
                next_check = True
                break
            elif current_time < start:
                next_class = start
                break
    else:
        start, end = class_schedule
        if start <= current_time < end:
            job(today, None, get, mail, verbose, cloud)
            next_check = True
        elif current_time < start:
            next_class = start

    if next_class:
        elapsed_time = get_elapsed_time(
            (
                datetime.strptime(next_class, '%H:%M')  # type: ignore
                - datetime.strptime(current_time, '%H:%M')
            ).seconds
        )
        return logging.info(f'Next class starts in {elapsed_time}')

    if not next_check:
        return logging.info('No more class today')


def job(
    day: str,
    session: Union[None, int],
    get: Callable[[str], Any],
    mail: bool,
    verbose: bool,
    cloud: bool,
):
    timer = time.perf_counter()

    browser = Attend(day, session, get, verbose, cloud)

    logging.info(f'{datetime.now().strftime("%A")} - {browser.class_name}')
    logging.info('Logging in...')

    attempt, logged_in, pushed, retry, pending, error, error_msg = (
        0,
        False,
        False,
        False,
        False,
        False,
        None,
    )

    while not logged_in and attempt <= 3600:
        attempt += 1
        logging.info(f'Login Attempt {attempt}')

        try:
            browser.login()

            name = browser.check_element(
                By.ID, 'eMail', error='Either your username or password is wrong'
            ).get_attribute('value')

            attempt, logged_in, error, error_msg = 0, True, False, None
        except Exception as e:
            error = True
            error_msg = f'Login error: {e}'

        if error_msg == 'Login error: Site Down':
            logging.info('Site Down when logging in, retrying...')
            continue

        if error_msg == 'Login error: Either your username or password is wrong':
            logging.info(
                'Either your username or password is wrong, Please check your credentials'
            )
            break

    if not error:
        logging.info(f'Success. Logged in as {name.title()}!')
        logging.info(f'Attending {browser.class_name} class...')

        try:
            browser.visit(browser.class_link)

            while (status := browser.get_button_status()) and (
                status
                in (
                    'Absen Masuk',
                    'Belum Mulai',
                    'Site Down',
                )
                or (not pushed and attempt)
            ):
                if attempt == 3600:
                    pending = True
                    break
                if retry:
                    retry = False
                    browser.driver.refresh()
                    continue
                attempt += 1
                logging.info(f'Attend Attempt {attempt}')
                logging.info(f'Button Status: {status}')
                if status == 'Site Down':
                    logging.info('Site Down! Retrying now...')
                    retry = True
                elif status == 'Belum Mulai':
                    logging.info(f"It hasn't started yet. Retrying now...")
                    retry = True
                else:
                    logging.info('Pushing the button...')
                    browser.click(By.XPATH, browser.attend_locator['ready'])
                    logging.info('Button pushed. Checking...')
                    pushed = True
        except Exception as e:
            error = True
            error_msg = f'Attend error: {e}'

    img_name, log_name = browser.save_screenshot(browser.data_log, error)

    if error:
        logging.info(f'Error occurred. {error_msg}')
    elif pending:
        logging.info('No class today')
    elif status == 'Kirim':
        logging.info('Automation success' if attempt else 'Already attended')
    elif status == 'Sudah Selesai':
        logging.info('Class is already over')
    else:
        logging.info('Something went wrong')

    browser.driver.close()

    elapsed_time = get_elapsed_time(time.perf_counter() - timer)

    logging.info(f'Automation completed in {elapsed_time}')

    browser.check_next_class()

    if mail:
        send_mail(
            f'Automation {"Success" if not error else "Failed"} - {browser.class_name}',
            log_name,
            img_name,
            get,
        )
        logging.info(f'Attendance report sent')
