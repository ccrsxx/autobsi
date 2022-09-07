from src import get_from_heroku, write_entry_point, Setup


def main() -> None:
    setup: Setup = {
        'get': get_from_heroku,
        'mail': True,
        'verbose': False,
        'cloud': True,
    }

    write_entry_point(setup)


if __name__ == '__main__':
    main()
