import redis
import json

# 连接Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# 获取文档信息
task_id = "bcf4f105-02e1-4761-9d06-58552bd75509"
key = f"paper_eval:doc:{task_id}"

doc_data = r.get(key)
if doc_data:
    doc_info = json.loads(doc_data)
    chapter_stats = doc_info.get('chapter_stats_result')

    if chapter_stats:
        print("章节统计信息:")
        print(json.dumps(chapter_stats, indent=2, ensure_ascii=False))
    else:
        print("章节统计信息尚未生成")
else:
    print("文档不存在")