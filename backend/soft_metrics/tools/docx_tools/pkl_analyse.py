import pickle

f_path = '/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_metrics/data/processed/docx/龚礼盛-本科毕业论文.pkl'

with open(f_path, 'rb') as f:
    data = pickle.load(f) # data 是一个字典，包含4个键：'zh_abs', 'en_abs', 'ref' 和 'chapters'

c = list(data.keys())
cn_abs = data['zh_abs'] # cn_abs 是字符串类型，存储中文摘要
eng_abs = data['en_abs'] # eng_abs 是字符串类型，存储英文摘要
ref = data['ref'] # ref 是字符串类型，存储参考文献

# chapters 是列表，每个元素都是一个字典
# 每个字典有3个键：'chapter_name'（章节名称）, 'content'（内容）, 'images'（图片）
# 使用 data['chapters'][0]['content'] 可以获取第1章的文本内容
chapters = data['chapters'] 

pass