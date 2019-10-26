import ast


def to_list(data: str) -> list:
    return ast.literal_eval(data)
