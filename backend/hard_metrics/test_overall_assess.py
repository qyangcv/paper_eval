"""
测试 overall_assess 模块的核心功能
不依赖外部AI模型，只测试数据处理逻辑
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from pipeline.overall_assess import (
    extract_toc_and_chapters,
    generate_selection_prompt,
    parse_selected_chapters,
    generate_final_assessment_prompt
)

def create_test_markdown():
    """创建测试用的markdown文件"""
    content = """
# 测试论文标题

## 目录
1. 绪论
2. 相关工作  
3. 研究方法
4. 实验结果
5. 结论

## 摘要
这是一篇测试论文的摘要，包含研究背景、方法和主要贡献。

# 绪论
本章介绍研究背景和意义。

## 研究背景
描述研究背景的详细内容。

# 相关工作
回顾相关领域的研究工作。

# 研究方法
详细介绍本文提出的研究方法。

## 算法设计
描述核心算法的设计思路。

# 实验结果
展示实验结果和分析。

# 结论
总结全文的主要贡献和未来工作。
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name

def test_extract_toc_and_chapters():
    """测试章节提取功能"""
    print("🧪 测试章节提取功能...")
    
    # 创建测试文件
    test_file = create_test_markdown()
    
    try:
        # 提取数据
        data = extract_toc_and_chapters(test_file)
        
        # 验证结果
        assert 'toc' in data, "缺少目录数据"
        assert 'abstract' in data, "缺少摘要数据"
        assert 'chapters' in data, "缺少章节数据"
        
        print(f"✅ 提取到目录: {len(data['toc'])} 字符")
        print(f"✅ 提取到摘要: {len(data['abstract'])} 字符")
        print(f"✅ 提取到章节: {len(data['chapters'])} 个")
        print(f"   章节标题: {list(data['chapters'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 章节提取测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        os.unlink(test_file)

def test_generate_selection_prompt():
    """测试选择提示词生成"""
    print("\n🧪 测试选择提示词生成...")
    
    try:
        toc = "1. 绪论\n2. 相关工作\n3. 研究方法\n4. 实验结果"
        abstract = "这是测试摘要内容"
        metric = "创新性"
        
        prompt = generate_selection_prompt(toc, abstract, metric)
        
        # 验证提示词包含必要信息
        assert metric in prompt, f"提示词中缺少评估维度: {metric}"
        assert toc in prompt, "提示词中缺少目录信息"
        assert abstract in prompt, "提示词中缺少摘要信息"
        assert "JSON" in prompt, "提示词中缺少输出格式说明"
        
        print(f"✅ 成功生成选择提示词，长度: {len(prompt)} 字符")
        return True
        
    except Exception as e:
        print(f"❌ 选择提示词生成测试失败: {e}")
        return False

def test_parse_selected_chapters():
    """测试章节解析功能"""
    print("\n🧪 测试章节解析功能...")
    
    try:
        # 测试正常JSON响应
        json_response = """
        ```json
        {
            "selected_chapters": ["绪论", "研究方法", "实验结果"],
            "reasoning": "这些章节最能体现创新性"
        }
        ```
        """
        
        chapters = parse_selected_chapters(json_response)
        expected = ["绪论", "研究方法", "实验结果"]
        
        assert chapters == expected, f"解析结果不匹配: {chapters} vs {expected}"
        print(f"✅ JSON解析成功: {chapters}")
        
        # 测试降级处理
        fallback_response = "我选择了'绪论章'和'方法章'进行评估"
        chapters = parse_selected_chapters(fallback_response)
        
        print(f"✅ 降级解析成功: {chapters}")
        return True
        
    except Exception as e:
        print(f"❌ 章节解析测试失败: {e}")
        return False

def test_generate_final_assessment_prompt():
    """测试最终评估提示词生成"""
    print("\n🧪 测试最终评估提示词生成...")
    
    try:
        content = "这是选中章节的内容，包含详细的技术描述和实验数据。"
        metric = "实验完成度"
        
        prompt = generate_final_assessment_prompt(content, metric)
        
        # 验证提示词包含必要信息
        assert metric in prompt, f"提示词中缺少评估维度: {metric}"
        assert content in prompt, "提示词中缺少章节内容"
        assert "summary" in prompt, "提示词中缺少输出格式说明"
        assert "strengths" in prompt, "提示词中缺少优势字段"
        assert "weaknesses" in prompt, "提示词中缺少不足字段"
        
        print(f"✅ 成功生成最终评估提示词，长度: {len(prompt)} 字符")
        return True
        
    except Exception as e:
        print(f"❌ 最终评估提示词生成测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("📋 开始测试 overall_assess 模块核心功能")
    print("=" * 60)
    
    tests = [
        test_extract_toc_and_chapters,
        test_generate_selection_prompt,
        test_parse_selected_chapters,
        test_generate_final_assessment_prompt
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！overall_assess 模块核心功能正常")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查代码")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 