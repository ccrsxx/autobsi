import schedule

from src import (
    os,
    time,
    logging,
    get_from_config,
    attend_class,
)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(os.path.join('logs', 'temp.txt')),
            logging.StreamHandler(),
        ],
    )

    attend_class(get=get_from_config, mail=False, verbose=False, cloud=False)

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
