from typing import Union

from dataclasses import dataclass, asdict


def get_elapsed_time(seconds: Union[int, float]):
    seconds = round(seconds)

    minutes = seconds // 60

    @dataclass
    class Time:
        hours: int
        minutes: int
        seconds: int

    time = Time(0, 0, 0)

    time.minutes = minutes

    if minutes >= 60:
        time.hours = minutes // 60
        time.minutes = minutes % 60

    time.seconds = seconds % 60

    output_time = [
        f'{value} {key[:-1] if value == 1 else key}'
        for key, value in asdict(time).items()
        if value
    ]

    if len(output_time) == 3:
        return f'{", ".join(output_time[:-1])}, and {output_time[-1]}'

    return ' and '.join(output_time)
