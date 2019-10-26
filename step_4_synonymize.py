from generic import io, conv

init_csv = {
    "location": "data/res/text/step_3_filtered.csv",
    "delimiter": "\t",
    "read_from": 0,
    "read_to": -1,
    "header": [
        "pos",
        "word",
        "trans"
    ]
}

res_csv = {
    "location": "data/res/text/step_4_synonymized.csv",
    "delimiter": "\t",
    "write_mode": "w",
    "synonym_columns": 5,
    "synonyms_per_column": 5,
    "header": lambda syn_col_num: [
                                      "pos",
                                      "word",
                                      "trans",
                                  ] + ["syn_%d" % (n + 1) for n in range(syn_col_num)],
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


def slice_evenly(l: list, per: int):
    for i in range(0, len(l), per):
        yield l[i:i + per]


def synonymize():
    init_csv_content_sorted = [[int(e[0]), e[1], e[2], sorted(conv.to_list(e[2]))] for e in read_csv()]
    init_csv_content_sorted.sort(key=lambda e: e[3])

    res_csv_content = list()
    res_csv_content.append(res_csv["header"](res_csv["synonym_columns"]))

    for csv_row in enumerate(init_csv_content_sorted):
        r_number = csv_row[0]
        r_content = csv_row[1]

        pos = r_content[0]
        wrd = r_content[1]
        trs = r_content[2]
        trs_srt = r_content[3]

        syns = list()
        blacklist = [pos]

        for tr in trs_srt:
            for sub_csv_row in init_csv_content_sorted:
                sub_pos = sub_csv_row[0]
                sub_wrd = sub_csv_row[1]
                sub_trs_srt = sub_csv_row[3]

                if sub_pos in blacklist:
                    continue

                for sub_tr in sub_trs_srt:
                    if sub_tr == tr:
                        syns.append([sub_pos, sub_wrd])
                        blacklist.append(sub_pos)
                        break

        syns = [e[1] for e in sorted(syns, key=lambda x: x[0])]

        res_csv_content.append([pos, wrd, trs])

        limit = res_csv["synonym_columns"]
        size = res_csv["synonyms_per_column"]
        if len(syns) >= limit:
            for l in slice_evenly(syns, size):
                if limit > 0:
                    res_csv_content[-1].append(l)
                    limit -= 1
        elif len(syns) > 0:
            res_csv_content[-1].append(syns)
            limit -= 1

        while limit > 0:
            res_csv_content[-1].append(list())
            limit -= 1

        if r_number % 100 == 0:
            print("synonymized:", r_number)

    write_csv(sorted(res_csv_content, key=lambda x: x[0] if isinstance(x[0], int) else 0))


synonymize()
