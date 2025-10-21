# backend/pipeline/code_generator.py
import json
import pandas as pd
from openai import OpenAI
import logging

client = OpenAI()
logger = logging.getLogger(f'excel_agent.{__name__}')

# Shared system prompt for code generation
SYSTEM_PROMPT = """核心原则
专注代码：模型应直接输出可执行的 Python 代码，无需添加任何解释性文字或 Markdown 标记（如 ```python）。
结果导向：所有最终的分析结果或数据展示，都必须使用 print() 函数输出到控制台。
使用指定文件路径：Excel metadata 中会提供具体的文件路径(file_path)，代码必须直接使用这个路径，不要使用占位符如'your_file_path.xlsx'或'your_file.xlsx'。
全面处理：如果 Excel 文件包含多个工作表（sheet），代码需要能遍历并处理所有符合条件的工作表。

代码规范与要求

1.标准库导入:
* Pandas: 必须使用 import pandas as pd。同时，为了完整显示数据，应设置 pd.set_option('display.max_columns', None) 和 pd.set_option('display.max_rows', None)。
目的：确保在打印 DataFrame 时，所有行和列都能完整显示，避免因输出内容被截断而丢失关键信息。
* Warnings: 必须使用 import warnings 并通过 warnings.simplefilter(action='ignore', category=Warning) 屏蔽不必要的警告信息。
目的：保持控制台输出的整洁性，让用户能专注于代码执行的核心结果，而不是被次要的警告信息干扰。

2. 编码风格：
* 命名规范: 变量和函数命名应避免使用中文或特殊符号（如 #），以防范语法错误。
目的：保证代码的兼容性和可移植性，避免因编码问题或特殊字符与语法冲突而导致的潜在错误。
* 保持列名: 在处理数据时，必须保持原始列名中的特殊字符（如下划线、多空格）不变。
目的：维持数据的原始结构和上下文，确保后续操作或用户在核对数据时，列名与源文件完全一致。

3. 稳健性：
* 异常处理: 生成的代码必须包含 try...except 等异常处理机制，确保程序的稳定性。
目的：防止程序因意外错误（如文件格式问题、数据类型不匹配）而中断执行，提高代码的容错能力。
* 数值转换: 在进行数值计算（如求和、排序）前，使用 pd.to_numeric(series, errors='coerce') 将数据列转换为数值类型，并忽略任何无法转换的错误。
目的：确保所有计算操作都在正确的数值类型上进行。errors='coerce' 会将无法转换的值设为 NaN（非数字），从而避免程序因个别脏数据而报错，保证了数据处理流程的顺畅。
* 弃用方法: 注意 DataFrame.fillna() 方法的 method 参数已不推荐使用，应采用其他方式填充。
目的：遵循库的最佳实践，确保代码在未来版本的 Pandas 中依然能够正常运行，提高代码的长期可维护性。"""


def generate_code(metadata_text, question):
    """
    Generate Python code based on Excel metadata and user question.

    Args:
        metadata_text (str): The metadata text from the searched Excel file
        question (str): The user's question about the Excel data

    Returns:
        str: Generated Python code for analyzing the Excel file
    """
    logger.info(f"Generating code for question: {question}")

    # Extract file path from metadata if available
    file_path = ""
    lines = metadata_text.split('\n')
    for line in lines:
        if line.startswith('File path:'):
            file_path = line.replace('File path:', '').strip()
            break

    enhanced_prompt = f"""Excel metadata:
{metadata_text}

User question: {question}

IMPORTANT: Use the file path '{file_path}' directly in your code. Do NOT use placeholders like 'your_file_path.xlsx' or any other generic names."""

    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": enhanced_prompt}
        ]
    )

    # Extract the generated code from the response
    generated_code = response.choices[0].message.content.strip()
    logger.info("Generated Python code for analysis")
    return generated_code