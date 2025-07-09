# 结合多模态大模型分析图表
## 模块架构
```text
multimodal/
├── prompt/                        # 提示词模板
│   ├── classification.txt         # 图表类型分类
│   ├── chart_standard.txt         # 判断统计图表的规范问题
│   ├── image_similarity.txt       # 判断两张图片是否相似
│   ├── method_context.txt         # 判断方法图/流程图是否和描述一致
│   └── ocr.txt                    # 识别图表中的文字
├── call_gpt.py                    # 调用大模型 API
├── image_match.py                 # 调用 Bing 以图搜图
├── image_similarity.py            # 特征点计算两张图片的相似度
└── three_lines.py                 # 霍夫变换检测直线
```
## 文件参数说明
```text
call_gpt.py 

变量：
text_path：prompt文件路径  
base64_image：图片路径

输出格式：
字符串形式
```
```text
image_match.py

变量：
SAVE_DIR：保存相似图片的文件夹
SAVE_TXT：保存图片链接的文本文件
file：需要检索的图片路径

参数：
max_images：下载的图片最大数量

输出格式：
将相似图片下载到SAVE_DIR中，并将图片链接保存到SAVE_TXT中
```
```text
image_similarity.py

变量：
image1_path：比较相似度的图片路径
image2_path：比较相似度的图片路径

参数：
threshold：判断两张图片是否相似的阈值

输出格式：
字符串形式输出相似度比较结果
```
```text
three_lines.py

变量：
img_path：需要检测的表格路径

参数：
min_len_ratio：长度阈值占图宽/高的比例，检测大于阈值的直线
canny_lo, canny_hi：canny检测相关参数
coord_tol, gap_tol：去重相关参数

输出格式：
字符串形式输出直线数量，并输出线条高亮后的表格图片