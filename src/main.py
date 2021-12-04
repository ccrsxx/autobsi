import time
import logging
import schedule
from PIL import Image
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from environment import get_from_config, get_from_dotenv
from mail import send_mail


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S',
                handlers=[
                    logging.FileHandler(f'logs\\{datetime.now().strftime("%d %b")}.txt', 'w'), 
                    logging.StreamHandler()
                ]
)


class Base:

    def __init__(self, day, session, mode, verbose):
        options = Options()
        if not verbose: options.add_argument('headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options, service_log_path='NUL')
        self.sch, self.username, self.password = mode('schedule'), mode('username'), mode('password')
        self.class_name = self.sch[day]['name'][session] if session is not None else self.sch[day]['name']
        self.class_link = self.sch[day]['link'][session] if session is not None else self.sch[day]['link']
        self.data_log = f'{datetime.now().strftime("%d %b")} - {self.class_name}'

    def visit(self, url):
        self.driver.get(url)

    def input_keys(self, method, elem, keys):
        self.driver.find_element(method, elem).send_keys(keys)

    def click(self, method, elem):
        self.driver.find_element(method, elem).click()

    def check_element(self, method, elem, error, wait=10, condition=EC.presence_of_element_located):
        try:
            element = WebDriverWait(self.driver, wait).until(condition((method, elem)))
        except TimeoutException:
            raise Exception(error)
        return element

    def check_exists(self, method, elem):
        try:
            element = self.driver.find_element(method, elem)
        except NoSuchElementException:
            return False
        return element

    def save_screenshot(self):
        img_name = f'screenshots\\{self.data_log}.png'
        self.driver.set_window_size(1920, 1080)
        self.driver.find_element(By.TAG_NAME, 'body').screenshot(img_name) 
        self.driver.get_screenshot_as_file(img_name)
        Image.open(img_name).crop((80, 100, 1900, 330)).save(img_name)
        return img_name


class Attend(Base):

    def __init__(self, day, session, mode, verbose):
        super().__init__(day, session, mode, verbose)

        self.login_url = 'http://elearning.bsi.ac.id/login'

        self.login_locator = {
            'username_input': '#username',
            'password_input': '#password',
            'login_button': '/html/body/div/div/div/div[2]/div/div[2]/form/div[3]/button'
        }

        self.attend_locator = {
            'ready': '/html/body/div[1]/div/div[2]/div/div[5]/div/form/center/button',
            'not_ready': '/html/body/div[1]/div/div[2]/div/div[5]/div/center/button',
        }

    def login(self):
        self.visit(self.login_url)
        self.check_element(By.XPATH, self.login_locator['login_button'], error='Login error.', condition=EC.element_to_be_clickable)
        self.input_keys(By.CSS_SELECTOR, self.login_locator['username_input'], self.username)
        self.input_keys(By.CSS_SELECTOR, self.login_locator['password_input'], self.password)
        self.click(By.XPATH, self.login_locator['login_button'])

    def get_button_status(self):
        self.check_element(By.CSS_SELECTOR, '#sidebar', error='Button checking error.')
        if ready := self.check_exists(By.XPATH, self.attend_locator['ready']): 
            return ready.text
        return self.driver.find_element(By.XPATH, self.attend_locator['not_ready']).text


def attend_class(mode=get_from_config, mail=False, verbose=False):
    sch = mode('schedule')
    today = datetime.now().strftime('%A').lower()

    if today not in sch:
        return logging.info('No class today.')

    no_class, next = True, False

    class_schedule = sch[today]['time']
    current_time = datetime.now().strftime('%H:%M')

    if any(isinstance(nest, list) for nest in class_schedule):
        for session, (start, end) in enumerate(class_schedule):
            if start <= current_time < end:
                job(today, session, mode, mail, verbose)
                no_class = False
                break
            elif current_time < start:
                next = start
                break
            else:
                pass
    else:
        start, end = class_schedule
        if start <= current_time < end:
            job(today, mode=mode, mail=mail, verbose=verbose)
            no_class = False
        elif current_time < start:
            next = start
        else: 
            pass

    if no_class:
        if next:
            hour, minute = str(datetime.strptime(next, '%H:%M') - datetime.strptime(current_time, '%H:%M')).split(':')[:-1]
            return logging.info(f'Not in a class schedule now. Next class starts in {hour} hours and {minute} minutes.')
        return logging.info('No more class today.')


def job(day, session=None, mode=get_from_config, mail=False, verbose=False):
    timer = time.perf_counter()

    obj = Attend(day, session, mode, verbose)

    logging.info(f'{datetime.now().strftime("%A")} - {obj.class_name}')
    logging.info('Attempting to login...')

    obj.login()
    
    name = obj.check_element(By.ID, 'eMail', error='Either your username or password is wrong', wait=5).get_attribute('value')

    logging.info(f'Success. Logged in as {name.title()}!')
    logging.info(f'Attempting to attend {obj.class_name}')

    obj.visit(obj.class_link)

    attempt, retry, pending = 0, False, False

    try:
        while obj.get_button_status() in ('Absen Masuk', 'Belum Mulai'):
            if attempt == 100:
                pending = True
                break
            if retry:
                retry = False
                time.sleep(60)
                obj.driver.refresh()
                continue
            attempt += 1
            logging.info(f'Attempt {attempt}')
            logging.info(f'Button Status: {obj.get_button_status()}')
            if obj.get_button_status() == 'Belum Mulai':
                logging.info(f'Waiting a minute. The class hasn\'t started yet.')
                retry = True
            else:
                logging.info('Attempting to push the attendance button...')
                obj.click(By.XPATH, obj.attend_locator['ready'])
                logging.info('Button pushed. Checking...')
    except Exception as e:
        logging.info(f'{e} - while attempting to attend the class')

    img_name = obj.save_screenshot()

    if obj.get_button_status() == 'Kirim':
        logging.info('Automation success.')
    elif obj.get_button_status() == 'Sudah Selesai':
        logging.info('Class is already over.')
    elif pending:
        logging.info('No class today.')
    else:
        logging.info('Automation failed.')

    obj.driver.close()

    logging.info(f'Automation completed in {time.perf_counter() - timer:.0f} seconds')

    if mail:
        send_mail(f'Attendance Report - {obj.class_name}', f'logs\\{datetime.now().strftime("%d %b")}.txt', img_name, mode)

    logging.info(f'Attendance report sent.')


def main():
    attend_class(mode=get_from_config, mail=False, verbose=False)

    '''
    schedule.every().monday.at('12:30').do(job, 'monday')
    schedule.every().tuesday.at('07:00').do(job, 'tuesday')
    schedule.every().wednesday.at('09:30').do(job, 'wednesday')
    schedule.every().thursday.at('15:00').do(job, 'thursday', 0)
    schedule.every().thursday.at('19:00').do(job, 'thursday', 1)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''


if __name__ == '__main__':
    main()
