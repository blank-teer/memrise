import re

from generic import io, conv

init_csv = {
    "location": "data/res/text/step_1_scrapped.csv",
    "delimiter": "\t",
    "read_from": 0,
    "read_to": -1,
    "header": [
        "pos",
        "word",
        "common_tran",
        "extra_trans"
    ]
}

res_csv = {
    "location": "data/res/text/step_2_sorted.csv",
    "delimiter": "\t",
    "write_mode": "w",
    "header": [
        "pos",
        "word",
        "trans_v1_common",
        "trans_v2_common_then_usual",
        "trans_v3_common_then_usual_then_unusual",
        "trans_v4_common_then_usual_then_unusual_then_rare",
        "trans_v5_usual",
        "trans_v6_usual_then_unusual",
        "trans_v7_usual_then_unusual_then_rare",
    ],
    "only_verified_common": False,
}


def read_csv() -> list:
    content = io.read_csv(init_csv["location"],
                          init_csv["delimiter"])

    def validate_header() -> bool:
        actual = content[0]
        expected = init_csv["header"]

        if actual != expected:
            print("err: invalid initial file header\n"
                  "act: %s\n"
                  "exp: %s" % (actual, expected))
            return False
        return True

    def reslice():
        nonlocal content
        read_from = init_csv["read_from"]
        read_to = init_csv["read_to"]

        if read_from == 0:
            read_from = 1

        if read_to == -1:
            read_to = len(content)

        content = content[read_from:read_to]

    if not validate_header():
        exit()

    reslice()
    return content


def write_csv(content: list, mode: str = ""):
    io.write_csv(content,
                 res_csv["location"],
                 res_csv["delimiter"],
                 res_csv["write_mode"] if mode == "" else mode)


def prettify(income: list) -> list:
    income = lower_case(income)
    income = remove_duplicates(income)
    income = remove_non_cyrillic(income)
    return income


def lower_case(income: list) -> list:
    return [i.lower() for i in income]


def remove_duplicates(income: list) -> list:
    return list(dict.fromkeys(income))


def remove_non_cyrillic(income: list) -> list:
    outcome = list()
    pattern = re.compile(r'[A-Za-z\d]')
    for i in income:
        if pattern.search(i) is None:
            outcome.append(i)
    return outcome


def get_common(common: list) -> list:
    outcome = list()

    if len(common) != 2:
        return outcome

    tran = common[0]
    vrf = common[1]

    if res_csv["only_verified_common"]:
        if vrf:
            outcome.append(tran)
    else:
        outcome.append(tran)

    return outcome


def get_extra(freq_mark: str, extra: list) -> list:
    outcome = list()

    for e in extra:
        e_tran = e[0]
        freq = e[2]

        if freq == freq_mark:
            outcome.append(e_tran)

    return outcome


def get_extra_usual(extra: list) -> list:
    return get_extra("Обычный перевод", extra)


def get_extra_unusual(extra: list) -> list:
    return get_extra("Необычный перевод", extra)


def get_extra_rare(extra: list) -> list:
    return get_extra("Редкий перевод", extra)


def v1_common(common: list) -> list:
    out_common = get_common(common)
    return prettify(out_common)


def v2_common_then_usual(common: list, extra: list) -> list:
    out_common = get_common(common)
    out_usual = get_extra_usual(extra)

    out = out_common + out_usual
    return prettify(out)


def v3_common_then_usual_then_unusual(common: list, extra: list) -> list:
    out_common = get_common(common)
    out_usual = get_extra_usual(extra)
    out_unusual = get_extra_unusual(extra)

    out = out_common + out_usual + out_unusual
    return prettify(out)


def v4_common_then_usual_then_unusual_then_rare(common: list, extra: list) -> list:
    out_common = get_common(common)
    out_usual = get_extra_usual(extra)
    out_unusual = get_extra_unusual(extra)
    out_rare = get_extra_rare(extra)

    out = out_common + out_usual + out_unusual + out_rare
    return prettify(out)


def v5_usual(extra: list) -> list:
    out_usual = get_extra_usual(extra)

    out = out_usual
    return prettify(out)


def v6_usual_then_unusual(extra: list) -> list:
    out_usual = get_extra_usual(extra)
    out_unusual = get_extra_unusual(extra)

    out = out_usual + out_unusual
    return prettify(out)


def v7_usual_then_unusual_then_rare(extra: list) -> list:
    out_usual = get_extra_usual(extra)
    out_unusual = get_extra_unusual(extra)
    out_rare = get_extra_rare(extra)

    out = out_usual + out_unusual + out_rare
    return prettify(out)


def sort():
    init_csv_content = read_csv()
    res_csv_content = list()

    res_csv_content.append(res_csv["header"])

    for csv_row in init_csv_content:
        pos = int(csv_row[0])
        word = csv_row[1]

        common_tran = conv.to_list(csv_row[2])
        extra_trans = conv.to_list(csv_row[3])

        v1 = v1_common(common_tran)
        v2 = v2_common_then_usual(common_tran, extra_trans)
        v3 = v3_common_then_usual_then_unusual(common_tran, extra_trans)
        v4 = v4_common_then_usual_then_unusual_then_rare(common_tran, extra_trans)
        v5 = v5_usual(extra_trans)
        v6 = v6_usual_then_unusual(extra_trans)
        v7 = v7_usual_then_unusual_then_rare(extra_trans)

        csv_row_processed = [
            pos,
            word,
            v1,
            v2,
            v3,
            v4,
            v5,
            v6,
            v7
        ]

        res_csv_content.append(csv_row_processed)

        if pos % 100 == 0:
            print("sorted:", pos)

    write_csv(res_csv_content)


sort()
