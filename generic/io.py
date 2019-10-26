import csv


def build_file_location(directory: str, filename: str) -> str:
    if directory[-1] != "\\":
        directory += "\\"
    return directory + filename


def read_csv(location: str, delimiter: str, read_from: int = 0, read_to: int = -1) -> list:
    with open(location, encoding="utf-8", newline="") as f:
        content = csv.reader(f, delimiter=delimiter)
        listed = [c for c in content]

        if read_to == -1:
            read_to = len(listed) + 1
        return listed[read_from:read_to]


def write_csv(content: list, location: str, delimiter: str, mode: str):
    while True:
        try:
            with open(location, mode, encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=delimiter)
                if all(isinstance(el, list) for el in content):
                    writer.writerows(content)
                else:
                    writer.writerow(content)
        except PermissionError:
            input("Закройте файл " + location + " и нажмите Enter, чтобы продолжить", )
        else:
            break
