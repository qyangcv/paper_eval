import pickle

in_path = 'data/processed/docx/<xxx>.pkl'

with open(in_path, 'rb') as f:
    data = pickle.load(f) # 'data' is a dict, with 4 keys: 'zh_abs', 'en_abs', 'ref' and 'chapters'.

c = list(data.keys())
cn_abs = data['zh_abs'] # cn_abs is str
eng_abs = data['en_abs'] # eng_abs is str
ref = data['ref'] # ref is str

# chapters is list, each element is a dict
# each dict has 3 keys: 'chapter_name', 'content', 'images'
# use data['chapters'][0]['content'] to get the text content of the 1st chapter
chapters = data['chapters'] 

pass