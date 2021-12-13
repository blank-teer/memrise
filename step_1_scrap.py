import re
import time

from bs4 import BeautifulSoup
from selene.api import *
from selenium.common.exceptions import StaleElementReferenceException

from browser import manage
from generic import io

translator = {
    "url": "https://translate.google.com"
}

init_csv = {
    "location": "data/init/text/raw.csv",
    "delimiter": ",",
    "read_from": 0,
    "read_to": 20001,
    "header": [
        "pos",
        "word"
    ]
}

res_csv = {
    "location": "data/res/text/step_1_scrapped.csv",
    "delimiter": "\t",
    "write_mode": "a",
    "header": [
        "pos",
        "word",
        "common_tran",
        "extra_trans"
    ]
}


def read_csv() -> list:
    rows = io.read_csv(init_csv["location"],
                       init_csv["delimiter"])

    def validate_header() -> bool:
        actual = rows[0]
        expected = init_csv["header"]

        if actual != expected:
            print("err: invalid initial file header\n"
                  "act: %s\n"
                  "exp: %s" % (actual, expected))
            return False
        return True

    def reslice():
        nonlocal rows
        read_from = init_csv["read_from"]
        read_to = init_csv["read_to"]

        if read_from == 0:
            read_from = 1

        if read_to == -1:
            read_to = len(rows)

        rows = rows[read_from:read_to]

    if not validate_header():
        exit()

    reslice()
    return rows


def write_csv(content: list, mode: str = ""):
    io.write_csv(content,
                 res_csv["location"],
                 res_csv["delimiter"],
                 res_csv["write_mode"] if mode == "" else mode)


def write_csv_header():
    if init_csv["read_from"] == 0:
        write_csv(res_csv["header"])


def does_contain_bad_symbols(string: str) -> bool:
    """
    Check if the passed string contains symbols
    that caused an untidy look of the row inserted into csv file.
    If contains, then the string should be skipped.
    """
    if string.find("'") > -1:
        return True
    return False


def do_and_ensure(do_func, ensure_func, ensure_inbetween_delay=0.0, recursion_max_depth=0) -> bool:
    if recursion_max_depth > 3:
        return False

    do_func()

    tries = 15
    delay = ensure_inbetween_delay
    while tries > 0:
        if ensure_func():
            return True
        tries -= 1
        time.sleep(delay)

    do_and_ensure(do_func, ensure_func, ensure_inbetween_delay, recursion_max_depth + 1)


def set_languages():
    # source language
    lang_box = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[3]/c-wiz/div[1]/div/div[3]/div/div[3]")

    do_and_ensure(
        lambda: browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[1]/c-wiz/div[2]/button").click(),
        lambda: lang_box.matching(be.visible))

    lang_box.all("div").element_by(have.attribute("data-language-code", "en")).click()

    # target language
    lang_box = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[3]/c-wiz/div[2]/div/div[3]/div/div[2]")

    do_and_ensure(
        lambda: browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[1]/c-wiz/div[5]/button").click(),
        lambda: lang_box.matching(be.visible))

    lang_box.all("div").element_by(have.attribute("data-language-code", "ru")).click()


def audio():
    """
    Playback audio of the word pronunciation for caching it.
    """
    time.sleep(1)
    playback_button = browser.element(by.xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div[5]/div[3]/div[2]"))
    playback_button.click()


def audio_assure_finished():
    """
    If it seems we will have passed to the next word very quickly,
    wait till the audio end for make sure it is cached.
    """
    playback_button = browser.element(by.xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div/div/div[5]/div[3]/div[2]"))
    playback_button.assure(have.attribute("aria-pressed", "false"))
    time.sleep(1)


def common() -> list:
    """
    Retrieve common translation of the pasted word.
    Returned value is the list of: common translation + verify mark.
    """
    # retrieve the common translation to the right from input area
    tran = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[2]/div[6]/div/div[1]/span[1]/span/span").get(query.text)

    # retrieve the common translation to the right from input area
    verified = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[2]/div[6]/div/div[1]/div").matching(be.existing)

    # validate and save the pair of common translation and verify mark
    if tran != "" and not does_contain_bad_symbols(tran):
        return [tran, verified]

    return list()


def extra() -> list:
    """
    Retrieve extra translations of the pasted word.
    Returned value is the list of lists of: extra translation + reverse translations + frequency rate.
    """
    extras = list()

    # set up beautiful soup html parser
    bs = BeautifulSoup(browser.driver().page_source, "html.parser")

    # retrieve extra translations from the table (tr>td)
    table = bs.find("table")
    if table is None:
        return extras

    tran_row_class = table.find("tbody").find("th", scope="row")["class"]
    syns_row_class = table.find("tbody").find("td")["class"]
    freq_row_class = table.find("tbody").find_all("td")[1]["class"]

    tran_rows = table.select("." + ".".join(tran_row_class))
    syns_rows = table.select("." + ".".join(syns_row_class))
    freq_rows = table.select("." + ".".join(freq_row_class))

    # rows = filter(lambda x: True if x.find("div", "gt-card-collapsed") is None else False, rows)

    # start iterating onto rows of the table
    for i in range(len(tran_rows)):

        # process the current translation
        translation = tran_rows[i].get_text(strip=True)
        if does_contain_bad_symbols(translation):
            continue

        # process synonyms
        synonyms_ = syns_rows[i].get_text(strip=True).split(", ")
        synonyms_ = filter(lambda x: True if not does_contain_bad_symbols(x) else False, synonyms_)
        synonyms_ = [syn for syn in synonyms_]

        # process the frequency rate of the current translation
        frequency = freq_rows[i].get_text(strip=True)

        # summarize contents
        extras.append([translation, synonyms_, frequency])

    return extras


def enter(word: str):
    pattern = re.compile(r"\W")

    # indicate the input area for pasting csv words
    input_area = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/span/span/div/textarea")

    def do():
        # clean up
        input_area.clear()

        # paste the next word and press enter in order to close the popup
        input_area.send_keys(word).press_enter()

    def ensure():
        page_word = browser.element("/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[2]/c-wiz/section/h2/span").get(query.attribute("innerText"))

        # if csv word and page word are the same, then google translator's ajax has worked out properly,
        # so we can scrap the content.
        return pattern.sub("", page_word).lower() == pattern.sub("", word).lower()

    do_and_ensure(do, ensure, 0.2)


def scrap():
    # extract csv words that need to be translated
    init_csv_content = read_csv()

    # temporary collector of the scrapped data.
    intermediate_result = list()

    # configure and open a browser
    manage.run_configured(translator["url"])

    # set proper languages
    set_languages()

    # set header in resulting csv if it is necessary
    write_csv_header()

    # start iterating onto csv word collection
    for csv_row in init_csv_content:
        # aliases
        pos = int(csv_row[0])
        print("pos:", pos)

        word = csv_row[1]
        print("wrd:", word)
        print()

        enter(word)

        intermediate_result.append([
            pos,
            word,
            common(),
            extra()
        ])

        # write resulting content into resulting csv file.
        # it makes lower hard disk pressure by the batch insert to the resulting csv.
        if pos % 10 == 0:
            write_csv(intermediate_result)
            intermediate_result.clear()

        # reboot the browser from time to time to free RAM and prevent scrapping speed degradation.
        if pos % 100 == 0:
            init_csv["read_from"] = pos + 1
            browser.close()
            time.sleep(3)
            return scrap()

        # audio_assure_finished()

    browser.close()


scrap()
