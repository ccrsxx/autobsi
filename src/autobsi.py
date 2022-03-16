import os
import time
import logging
from PIL import Image
from typing import Type, Callable
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from .environment import get_from_config, get_from_dotenv
from .mail import send_mail


class Base:
    def __init__(self, verbose: bool):
        options = Options()
        if not verbose:
            options.add_argument('headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options, service_log_path='NUL')

    def visit(self, url: str):
        self.driver.get(url)

    def input_keys(self, method: By, elem: str, keys: str):
        self.driver.find_element(method, elem).send_keys(keys)

    def click(self, method: By, elem: str):
        self.driver.find_element(method, elem).click()

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

    def save_screenshot(self):
        img_name = os.path.join('screenshots', f'{self.data_log}.png')
        self.driver.set_window_size(1920, 1080)
        self.driver.find_element(By.TAG_NAME, 'body').screenshot(img_name)
        self.driver.get_screenshot_as_file(img_name)
        Image.open(img_name).crop((80, 100, 1900, 330)).save(img_name)
        return img_name


class Attend(Base):
    def __init__(
        self,
        day: str,
        session: None | int,
        get: Callable,
        verbose: bool,
    ):
        super().__init__(verbose)
        (
            self.sch,
            self.username,
            self.password,
            self.login_url,
            self.login_locator,
            self.attend_locator,
        ) = [
            get(key)
            for key in [
                'schedule',
                'username',
                'password',
                'login_url',
                'login_locator',
                'attend_locator',
            ]
        ]
        self.class_name = (
            self.sch[day]['name'][session]
            if session is not None
            else self.sch[day]['name']
        )
        self.class_link = (
            self.sch[day]['link'][session]
            if session is not None
            else self.sch[day]['link']
        )
        self.data_log = f'{datetime.now().strftime("%d %b")} - {self.class_name}'

        log_name = f'{self.data_log.split(" - ")[0]}.txt'

        if log_name in os.listdir('logs'):
            open(os.path.join('logs', log_name), 'w').close()

    def login(self):
        self.visit(self.login_url)
        self.check_element(
            By.XPATH,
            self.login_locator['login_button'],
            error='Login error',
            condition=EC.element_to_be_clickable,
        )
        self.input_keys(
            By.CSS_SELECTOR, self.login_locator['username_input'], self.username
        )
        self.input_keys(
            By.CSS_SELECTOR, self.login_locator['password_input'], self.password
        )
        self.click(By.XPATH, self.login_locator['login_button'])

    def get_button_status(self):
        self.check_element(By.CSS_SELECTOR, '#sidebar', error='Button checking error')
        if ready := self.check_exists(By.XPATH, self.attend_locator['ready']):
            return ready.text
        return self.driver.find_element(By.XPATH, self.attend_locator['not_ready']).text

    def check_next_class(self):
        current_time, today = (
            datetime.now().strftime('%H:%M'),
            datetime.now().strftime('%A').lower(),
        )
        class_schedule = self.sch[today]['time']

        next_class = False

        if any(isinstance(nest, list) for nest in class_schedule):
            for start, _ in class_schedule:
                if current_time < start:
                    next_class = start
                    break

        if next_class:
            hour, minute = str(
                datetime.strptime(next_class, '%H:%M')
                - datetime.strptime(current_time, '%H:%M')
            ).split(':')[:-1]
            return logging.info(
                f'Not in a class schedule now. Next class starts in {hour} hours and {minute} minutes'
            )

        return logging.info('No more class today')


def attend_class(
    get: Callable = get_from_config,
    mail: bool = False,
    verbose: bool = False,
):
    sch = get('schedule')
    today = datetime.now().strftime('%A').lower()

    if today not in sch:
        return logging.info('No class today')

    next_class = False

    class_schedule = sch[today]['time']
    current_time = datetime.now().strftime('%H:%M')

    if any(isinstance(nest, list) for nest in class_schedule):
        for session, (start, end) in enumerate(class_schedule):
            if start <= current_time < end:
                job(today, session, get, mail, verbose)
                break
            elif current_time < start:
                next_class = start
                break
    else:
        start, end = class_schedule
        if start <= current_time < end:
            job(today, get=get, mail=mail, verbose=verbose)
        elif current_time < start:
            next_class = start

    if next_class:
        hour, minute = str(
            datetime.strptime(next_class, '%H:%M')  # type: ignore
            - datetime.strptime(current_time, '%H:%M')
        ).split(':')[:-1]
        return logging.info(
            f'Not in a class schedule now. Next class starts in {hour} hours and {minute} minutes'
        )


def job(
    day: str,
    session: None | int = None,
    get: Callable[[str], str] = get_from_dotenv,
    mail: bool = True,
    verbose: bool = False,
):
    timer = time.perf_counter()

    driver = Attend(day, session, get, verbose)

    logging.info(f'{datetime.now().strftime("%A")} - {driver.class_name}')
    logging.info('Attempting to login...')

    attempt, retry, pending, error = 0, False, False, False

    try:
        driver.login()
        name = driver.check_element(
            By.ID, 'eMail', error='Either your username or password is wrong', wait=5
        ).get_attribute('value')
    except Exception as e:
        error = True
        logging.error(f'{e} - while logging in')

    if not error:
        logging.info(f'Success. Logged in as {name.title()}!')
        logging.info(f'Attempting to attend {driver.class_name}')

        driver.visit(driver.class_link)

        try:
            while driver.get_button_status() in ['Absen Masuk', 'Belum Mulai']:
                if attempt == 100:
                    pending = True
                    break
                if retry:
                    retry = False
                    time.sleep(60)
                    driver.driver.refresh()
                    continue
                attempt += 1
                logging.info(f'Attempt {attempt}')
                logging.info(f'Button Status: {driver.get_button_status()}')
                if driver.get_button_status() == 'Belum Mulai':
                    logging.info(f'Waiting a minute. The class hasn\'t started yet')
                    retry = True
                else:
                    logging.info('Attempting to push the attendance button...')
                    driver.click(By.XPATH, driver.attend_locator['ready'])
                    logging.info('Button pushed. Checking...')
        except Exception as e:
            error = True
            logging.info(f'{e} - while attempting to attend the class')

    img_name = driver.save_screenshot()

    if error:
        logging.info('Error while attempting to attend the class')
    elif pending:
        logging.info('No class today')
    elif driver.get_button_status() == 'Kirim':
        logging.info('Automation success')
    elif driver.get_button_status() == 'Sudah Selesai':
        logging.info('Class is already over')
    else:
        logging.info('Something went wrong')

    driver.driver.close()

    logging.info(f'Automation completed in {time.perf_counter() - timer:.0f} seconds')

    driver.check_next_class()

    if mail:
        send_mail(
            f'Attendance Report - {driver.class_name}',
            os.path.join('logs', f'{driver.data_log.split(" - ")[0]}.txt'),
            img_name,
            get,
        )
        logging.info(f'Attendance report sent')
