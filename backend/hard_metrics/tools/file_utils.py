import pickle

def read_txt(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        text_content = f.read()
    return text_content

def save_txt(filepath: str, content: str) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def read_pickle(filepath: str) -> dict:
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data

def save_pickle(filepath: str, data: dict) -> None:
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)


def read_md(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    return markdown_content