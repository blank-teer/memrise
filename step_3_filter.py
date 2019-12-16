from generic import io, conv

init_csv = {
    "location": "data/res/text/step_2_sorted.csv",
    "delimiter": "\t",
    "read_from": 0,
    "read_to": -1,
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
    "trans_column_to_use": "trans_v3_common_then_usual_then_unusual",
}

res_csv = {
    "location": "data/res/text/step_3_filtered.csv",
    "delimiter": "\t",
    "write_mode": "w",
    "header": [
        "pos",
        "word",
        "trans"
    ],
    "min_trans": 2,
    "max_trans": 4,
    "take_more_trans_if_lack": True
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


def filter():
    init_csv_content = read_csv()
    init_csv_header = init_csv["header"]

    res_csv_content = list()
    res_csv_content.append(res_csv["header"])

    for row in enumerate(init_csv_content):
        r_pos = row[0]
        r_content = row[1]

        req_trans_col_index = init_csv_header.index(init_csv["trans_column_to_use"])

        pos = r_content[0]
        word = r_content[1]
        trans = conv.to_list(r_content[req_trans_col_index])

        if not res_csv["take_more_trans_if_lack"]:
            res_csv_content.append([pos, word, trans])
            continue

        trans_largest = trans
        start_point = req_trans_col_index

        minimum = res_csv["min_trans"]
        maximum = res_csv["max_trans"]

        while True:
            if minimum <= len(trans_largest) <= maximum:
                break

            elif minimum <= len(trans_largest) > maximum:
                trans = trans[:maximum]
                break

            elif minimum > len(trans_largest):
                req_trans_col_index += 1

                if req_trans_col_index == start_point:
                    break

                if req_trans_col_index == len(init_csv_header):
                    req_trans_col_index = 0

                if "trans" not in init_csv_header[req_trans_col_index]:
                    continue

                new_trans = conv.to_list(r_content[req_trans_col_index])
                if len(trans_largest) < len(new_trans):
                    trans = new_trans
                    trans_largest = new_trans

        res_csv_content.append([pos, word, trans])

        if r_pos % 100 == 0:
            print("filtered:", r_pos)

    write_csv(res_csv_content)


filter()
