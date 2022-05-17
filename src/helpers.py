import os

from typing import Callable, Any


def write_schedule(get_function: str, attend_function: str, class_schedule: str):
    return f'''
import os
import time
import logging
import schedule

from src import {get_function}, attend_class, job


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


def write_entry_point(
    get: Callable[[str], Any], mail: bool, verbose: bool, cloud: bool
):
    setup = ', '.join(map(str, [get.__name__, mail, verbose, cloud]))

    attend_function = f'attend_class({setup})'

    timetable = get('timetable')

    class_schedule = []

    for day in timetable:
        item = timetable[day]
        start_time, _ = item['time']

        if isinstance(start_time, list):
            for i, (start_time, _) in enumerate(item['time']):
                class_schedule.append(
                    f"schedule.every().{day}.at('{start_time}').do(job, '{day}', {i}, {setup})"
                )
        else:
            class_schedule.append(
                f"schedule.every().{day}.at('{start_time}').do(job, '{day}', None, {setup})"
            )

    with open('server.py', 'w') as f:
        f.write(write_schedule(get.__name__, attend_function, ';'.join(class_schedule)))

    if not cloud:
        os.system('server.py')
