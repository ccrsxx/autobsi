import time
import logging
import schedule
from PIL import Image
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from environment import get_from_dotenv
from mail import send_mail


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S',
                    handlers=[
                        logging.FileHandler(f'logs\\{datetime.now().strftime("%d %b")}.txt', 'w'), 
                        logging.StreamHandler()
                    ]
)


class Base:

    def __init__(self, day, session, verbose, sch=get_from_dotenv('schedule')):
        options = Options()
        if not verbose: options.add_argument('headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options, service_log_path='NUL')
        self.name_class = sch[day]['name'][session] if session is not None else sch[day]['name']
        self.link_class = sch[day]['link'][session] if session is not None else sch[day]['link']
        self.data_log = f'{datetime.now().strftime("%d %b")} - {self.name_class}'

    def visit(self, url):
        self.driver.get(url)

    def input_keys(self, method, elem, keys):
        self.driver.find_element(method, elem).send_keys(keys)

    def click(self, method, elem):
        self.driver.find_element(method, elem).click()

    def save_screenshot(self):
        img_name = f'screenshots\\{self.data_log}.png'
        self.driver.set_window_size(1920, 1080)
        self.driver.find_element(By.TAG_NAME, 'body').screenshot(img_name) 
        self.driver.get_screenshot_as_file(img_name)
        Image.open(img_name).crop((80, 100, 1900, 330)).save(img_name)
        return img_name


class Attend(Base):

    def __init__(self, day, session, verbose):
        super().__init__(day, session, verbose)

        self.login_url = 'http://elearning.bsi.ac.id/login'

        self.login_locator = {
            'username_input': '#username',
            'password_input': '#password',
            'login_button': '/html/body/div/div/div/div[2]/div/div[2]/form/div[3]/button'
        }

        self.attend_locator = {
            'ready': '/html/body/div[1]/div/div[2]/div/div[5]/div/form/center/button',
            'not_ready': '/html/body/div[1]/div/div[2]/div/div[5]/div/center/button',
            'presence_tab': '#myTable > tbody'
        }

    def login(self, username=get_from_dotenv('username'), password=get_from_dotenv('password')):
        self.input_keys(By.CSS_SELECTOR, self.login_locator['username_input'], username)
        self.input_keys(By.CSS_SELECTOR, self.login_locator['password_input'], password)
        self.click(By.XPATH, self.login_locator['login_button'])

    def get_button_status(self):
        try:
            raw = self.driver.find_element(By.XPATH, self.attend_locator['ready'])
        except:
            raw = self.driver.find_element(By.XPATH, self.attend_locator['not_ready'])
        return raw.text

    def get_tab_status(self):
        raw = self.driver.find_element(By.CSS_SELECTOR, self.attend_locator['presence_tab'])
        status = [data.split()[1] for data in raw.text.split('\n')][-1]
        return status

def attend_class(sch=get_from_dotenv('schedule')):
    today = datetime.now().strftime('%A')

    if today not in sch:
        return logging.info('No class today.')

    class_schedule = sch[today]['time']

    if not any(isinstance(nest, list) for nest in class_schedule):
        start, end = class_schedule

    current_time = datetime.now().strftime('%H:%M')
    no_class = True

    if start:
        if start <= current_time < end:
            job(today)
            no_class = False
    else:
        for session in range(len(class_schedule)):
            start, end = class_schedule[session]
            if start <= current_time < end:
                job(today, session)
                no_class = False
                break

    if no_class:
        logging.info(f'Not in a class schedule now. Will start once class is open.')

def job(day, session=None, verbose=False):
    timer = time.time()
    obj = Attend(day, session, verbose)

    logging.info(f'Start of program - {obj.name_class}')
    logging.info('Attempting to login...')

    obj.visit(obj.login_url)
    obj.login()

    time.sleep(3)

    user = obj.driver.find_element(By.CLASS_NAME, 'user-name')
    name = obj.driver.find_element(By.ID, 'eMail').get_attribute('value')

    if user.text != get_from_dotenv('username'):
        logging.info('Either your username or password is wrong. Quitting...')
        quit()

    logging.info(f'Success. Logged in as {name.title()}!')
    logging.info(f'Attempting to attend {obj.name_class}')

    obj.visit(obj.link_class)

    time.sleep(3)

    attempt, retry, pending = 0, False, False
    while any(check in ('Absen Masuk', 'Belum Mulai', 'Tidak Hadir') for check in [obj.get_button_status(), obj.get_tab_status()]):
        if attempt == 100:
            pending = True
            break
        if retry:
            retry = False
            time.sleep(60)
            obj.driver.refresh()
            time.sleep(3)
            continue
        attempt += 1
        logging.info(f'Attempt {attempt}')
        logging.info(f'Button Status: {obj.get_button_status()}')
        logging.info('Attempting to push the attendance button...')
        if obj.get_button_status() == 'Belum Mulai':
            logging.info(f'Waiting 1 min. The class hasn\t stated yet.')
            retry = True
        else:
            obj.click(By.XPATH, obj.attend_locator['ready'])
            logging.info('Button pushed. Checking...')
            time.sleep(3)

    img_name = obj.save_screenshot()

    if obj.get_button_status() == 'Kirim' and obj.get_tab_status() == 'Hadir':
        logging.info('Automation sucess.')
    elif obj.get_button_status() == 'Sudah Selesai':
        logging.info('Already automated or attended.')
    elif pending:
        logging.info('No class today.')
    else:
        logging.info('Automation failed.')

    obj.driver.close()

    send_mail(f'Absen {obj.name_class}', f'logs\\{datetime.now().strftime("%d %b")}.txt', img_name)

    logging.info(f'Automation completed in {time.time() - timer:.0f} seconds')


def main():
    attend_class()

    '''
    schedule.every().monday.at('07:00').do(job, 'Monday')
    schedule.every().tuesday.at('07:00').do(job, 'Tuesday')
    schedule.every().wednesday.at('07:00').do(job, 'Wednesday')
    schedule.every().thursday.at('07:00').do(job, 'Thursday', 0)
    schedule.every().thursday.at('09:00').do(job, 'Thursday', 1)

    while True:
        schedule.run_pending()
        time.sleep(1)
    '''


if __name__ == '__main__':
    main()
