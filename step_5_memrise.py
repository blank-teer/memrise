import os
import time

from selene.api import *
from selene.elements import *
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from driver import manage
from generic import io, conv

init_csv = {
    "location": "data/res/text/step_4_synonymized.csv",
    "delimiter": "\t",
    "read_from": 0,
    "read_to": -1,
    "header": [
        "pos",
        "word",
        "trans",
        "syn_1",
        "syn_2",
        "syn_3",
        "syn_4",
        "syn_5",
    ]
}

course = {
    "edit_page_url": "https://www.memrise.com/course/ID/NAME/edit",
    "words_per_level": 100,
    "start_level": 1,  # indexing starts from 1, not 0
    "audio": {
        "need": True,
        "get": lambda pos, word: os.path.abspath("data/init/audio/%s.%s.mp3" % (pos, word))
    },
    "header": [
        "English",
        "Russian",
        "Audio",
        "Syn1",
        "Syn2",
        "Syn3",
        "Syn4",
        "Syn5",
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

    def reformat():
        nonlocal rows
        rows = [
            [
                int(col[0]),
                col[1],
                ', '.join(conv.to_list(col[2])),
                ', '.join(conv.to_list(col[3])),
                ', '.join(conv.to_list(col[4])),
                ', '.join(conv.to_list(col[5])),
                ', '.join(conv.to_list(col[6])),
                ', '.join(conv.to_list(col[7]))
            ] for col in rows
        ]

    if not validate_header():
        exit()

    reslice()
    reformat()
    return rows


def slice_evenly(l: list, per: int):
    for i in range(0, len(l), per):
        yield l[i:i + per]


def collapse(level: SeleneElement):
    if "collapsed" in level.get_attribute("class"):
        # print("level %s: already collapsed" % level.get_attribute("id"))
        return

    show_hide_btn = level.s(".show-hide")
    scroll_to(show_hide_btn)

    if not show_hide_btn.is_displayed():
        print("level %s: no show/hide button" % level.get_attribute("id"))
        return

    show_hide_btn.click()


def expand(level: SeleneElement):
    if "collapsed" not in level.get_attribute("class"):
        # print("level %s: already expanded" % level.get_attribute("id"))
        return

    show_hide_btn = level.s(".show-hide")
    scroll_to(show_hide_btn)

    if not show_hide_btn.is_displayed():
        print("level %s: no show/hide button" % level.get_attribute("id"))
        return

    show_hide_btn.click()


def validate_course_header() -> bool:
    levels = ss("#levels>.level")
    level = levels.first()

    if levels.size() > 1:
        expand(level)

    level_container = level.s(".table-container")
    level_header = level_container.ss("table>thead>tr>th").filtered_by(have.not_(have.attribute("textContent", "")))

    actual = [c.text.strip() for c in level_header]
    expected = course["header"]

    if actual != expected:
        print("err: invalid course header\n"
              "act: %s\n"
              "exp: %s" % (actual, expected))
        return False
    return True


def scroll_to(element: SeleneElement):
    browser.execute_script("arguments[0].scrollIntoView(false)", element.get_actual_webelement())


def diff(elem: SeleneElement, text_to_correspond_with: str) -> bool:
    return elem.text != text_to_correspond_with


def paste_in(element: SeleneElement, string: str):
    def input() -> SeleneElement:
        while True:
            element.click()
            inputs = element.ss("input")
            if inputs.size() > 0:
                return inputs.first()

    if element.text == string:
        return

    scroll_to(element)

    inp = input()

    if string == "":
        inp.clear()
    else:
        os.system("echo %s| clip" % string)
        inp.send_keys(Keys.CONTROL, 'a').send_keys(Keys.DELETE).send_keys(Keys.CONTROL, 'v')


def add_audio(item: SeleneElement, csv_pos: str, csv_word: str):
    item_audio_btns = item.ss(".cell>.btn-group>.btn")
    item_upload_btn = item_audio_btns[0]
    item_record_btn = item_audio_btns[1]
    item_dropdown_btn = item_audio_btns[2]

    if item_dropdown_btn.text == "no audio file":
        print("sounding...")
        scroll_to(item)
        audio_location = course["audio"]["get"](csv_pos, csv_word)

        if not os.path.exists(audio_location):
            print("fail: file doesn't exist:", audio_location)
            return

        item_upload_btn.s("input").get_actual_webelement().send_keys(audio_location)
        while True:
            try:
                t = item_dropdown_btn.text
            except TimeoutException:
                continue
            else:
                if t != "no audio file":
                    break


def level_update(level: SeleneElement, csv_rows: list, start: int = 0, recursion: bool = False):
    container = level.s(".table-container")
    items = container.ss(".level-things>.things>.thing")
    adding = container.ss(".level-things>.adding>tr")[-1].ss("td")

    enumerated = [e for e in enumerate(csv_rows)][start:]
    for csv_row in enumerated:
        row_numb = csv_row[0]
        row_data = csv_row[1]

        print("\ncsv row:", row_data)
        csv_pos = row_data[0]
        csv_word = row_data[1]
        csv_tran = row_data[2]
        csv_syn1 = row_data[3]
        csv_syn2 = row_data[4]
        csv_syn3 = row_data[5]
        csv_syn4 = row_data[6]
        csv_syn5 = row_data[7]

        if items.size() > row_numb:
            print("exists, check if it need to be updated...")
            item = items[row_numb]
            item_cols = item.ss(".cell>.wrapper")
            item_text_cols = item.ss(".cell>.wrapper")

            item_word = item_text_cols[0]
            item_tran = item_text_cols[1]
            item_syn1 = item_text_cols[2]
            item_syn2 = item_text_cols[3]
            item_syn3 = item_text_cols[4]
            item_syn4 = item_text_cols[5]
            item_syn5 = item_text_cols[6]

            if diff(item_tran, csv_tran) or\
                    diff(item_tran, csv_tran) or\
                    diff(item_syn1, csv_syn1) or\
                    diff(item_syn2, csv_syn2) or\
                    diff(item_syn3, csv_syn3) or\
                    diff(item_syn4, csv_syn4) or\
                    diff(item_syn5, csv_syn5):
                print("updating...")
                paste_in(item_tran, csv_tran)
                paste_in(item_syn1, csv_syn1)
                paste_in(item_syn2, csv_syn2)
                paste_in(item_syn3, csv_syn3)
                paste_in(item_syn4, csv_syn4)
                paste_in(item_syn5, csv_syn5)
            else:
                print("actual")

            if course["audio"]["need"]:
                add_audio(item, csv_pos, csv_word)

            start += 1
            print("done")
        else:
            print("not exists, adding...")
            def last_item_word(): return items[-1].ss("td")[1].text

            add_btn = adding[0].s("i")
            area_word = adding[1]

            pasted = False
            added = False
            wait = False
            tries = 20
            while True:
                if not pasted and not added:
                    print("pasting...")
                    paste_in(area_word, csv_word)
                    if wait:
                        print("waiting...")
                        time.sleep(2)
                    pasted = True

                if pasted and not added:
                    print("clicking...")
                    if add_btn.is_displayed():
                        add_btn.click()
                        added = True
                    else:
                        pasted = False
                        wait = True

                if pasted and added:
                    print("checking...")
                    if csv_word == last_item_word():
                        break
                    elif tries == 0:
                        pasted = False
                        added = False
                        continue
                    tries -= 1
            print("done")

    if not recursion:
        return level_update(level, csv_rows, start, True)


def level_create():
    try:
        btn = s(".btn-group.pull-left")
        scroll_to(btn)
        btn.click()
    except (TimeoutException, NoSuchElementException):
        s(".pull-left").click()
        time.sleep(3)
        s(".btn-primary").click()
    else:
        btn.ss("ul>li").first().click()


def memrise():
    init_csv_content = read_csv()

    manage.run_configured(course["edit_page_url"])

    if not validate_course_header():
        browser.close()
        exit()

    sliced = slice_evenly(init_csv_content, course["words_per_level"])

    enumerated = [e for e in enumerate(sliced)][course["start_level"] - 1:]
    for next_slice in enumerated:
        set_numb = next_slice[0]
        csv_rows = next_slice[1]

        level_created = False
        level_updated = False

        while not level_updated:
            levels = ss("#levels>.level")

            print("set:", set_numb)
            print("levels:", levels.size())

            if levels.size() > set_numb:
                print("\nupdate existing course level...")
                level = levels[set_numb]

                expand(level)
                level_update(level, csv_rows)
                collapse(level)

                level_updated = True

            elif not level_created:
                print("\ncreate new course level...")
                level_create()
                level_created = True

        manage.restart(course["edit_page_url"])


memrise()
