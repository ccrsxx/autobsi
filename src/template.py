def write_cloud_function(get_function: str, attend_function: str, class_schedule: str):
    return f'''
import schedule

from src import os, time, logging, {get_function}, attend_class, job


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

    {attend_function}

    {class_schedule}

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
'''
