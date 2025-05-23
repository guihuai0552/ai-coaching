#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AI命理教练网站后端

import os
import json
import logging
import traceback
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
from lunar_python import Lunar, Solar

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static', static_folder='static')

# 添加CORS头，解决跨域问题
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Flowith API配置
FLOWITH_ENDPOINT = "https://edge.flowith.net/external/use/seek-knowledge"
FLOWITH_KEY = "flo_916327f7e9c65188cb23550a5d25cff77ce997dccc7d888f3aeee5c1cf263da6"  # 使用提供的API密钥
# DeepSeek API配置
import os
DEEPSEEK_API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
# 使用环境变量存储API密钥，默认则使用这个值
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-0e4af51d9cc945e785e913d3fc685fe1")
DEEPSEEK_MODEL = "deepseek-chat"  # 使用DeepSeek模型

# 十二时辰对应表
SHICHEN_MAP = {
    "子时": (23, 0),  # 23:00-00:59
    "丑时": (1, 2),   # 01:00-02:59
    "寅时": (3, 4),   # 03:00-04:59
    "卯时": (5, 6),   # 05:00-06:59
    "辰时": (7, 8),   # 07:00-08:59
    "巳时": (9, 10),  # 09:00-10:59
    "午时": (11, 12), # 11:00-12:59
    "未时": (13, 14), # 13:00-14:59
    "申时": (15, 16), # 15:00-16:59
    "酉时": (17, 18), # 17:00-18:59
    "戌时": (19, 20), # 19:00-20:59
    "亥时": (21, 22)  # 21:00-22:59
}

# 根据小时获取对应的时辰
def get_shichen(hour):
    for shichen, (start, end) in SHICHEN_MAP.items():
        if hour >= start and hour <= end:
            return shichen
    return "子时"  # 默认返回子时

# 计算八字信息
def calculate_bazi(year, month, day, hour):
    try:
        # 将公历转换为农历
        solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
        lunar = solar.getLunar()
        
        # 获取八字信息
        ba = lunar.getEightChar()
        
        bazi_info = {
            "year_gan": ba.getYearGan(),
            "year_zhi": ba.getYearZhi(),
            "month_gan": ba.getMonthGan(),
            "month_zhi": ba.getMonthZhi(),
            "day_gan": ba.getDayGan(),
            "day_zhi": ba.getDayZhi(),
            "time_gan": ba.getTimeGan(),
            "time_zhi": ba.getTimeZhi(),
            "lunar_year": lunar.getYear(),
            "lunar_month": lunar.getMonth(),
            "lunar_day": lunar.getDay(),
            "solar_date": f"{year}年{month}月{day}日 {hour}时",
            "lunar_date": lunar.toString()
        }
        
        # 获取四柱干支
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan(), ba.getTimeGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi(), ba.getTimeZhi()]
        
        # 添加完整的八字
        bazi_info["bazi"] = " ".join([f"{g}{z}" for g, z in zip(gans, zhis)])
        
        # 计算十神
        day_gan = ba.getDayGan()  # 日主
        # 十神对应关系，基于日干
        ten_gods = calculate_ten_gods(day_gan, gans, zhis)
        bazi_info.update(ten_gods)
        
        return bazi_info
    except Exception as e:
        logger.error(f"计算八字出错: {e}")
        return None

# 计算十神
def calculate_ten_gods(day_gan, gans, zhis):
    """根据日干和其他天干地支计算十神信息"""
    # 天干五行属性
    gan_wuxing = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    
    # 五行生克关系：木→火→土→金→水→木
    # 五行生克关系定义十神
    ten_gods_map = {
        # 同性生我：正印
        'same_sheng': '正印',
        # 异性生我：偏印
        'diff_sheng': '偏印',
        # 同性克我：七杀
        'same_ke': '七杀',
        # 异性克我：正官
        'diff_ke': '正官',
        # 同性我克：正财
        'same_beke': '正财',
        # 异性我克：偏财
        'diff_beke': '偏财',
        # 同性我生：食神
        'same_besheng': '食神',
        # 异性我生：伴印
        'diff_besheng': '伴印',
        # 同性：比肩
        'same': '比肩',
        # 异性：劍颂
        'diff': '劍颂'
    }
    
    # 五行相生关系
    sheng_relation = {
        '木': '火',  # 木生火
        '火': '土',  # 火生土
        '土': '金',  # 土生金
        '金': '水',  # 金生水
        '水': '木'   # 水生木
    }
    
    # 五行相克关系
    ke_relation = {
        '木': '土',  # 木克土
        '土': '水',  # 土克水
        '水': '火',  # 水克火
        '火': '金',  # 火克金
        '金': '木'   # 金克木
    }
    
    # 天干阴阳属性
    gan_gender = {
        '甲': 'yang', '乙': 'yin',
        '丙': 'yang', '丁': 'yin',
        '戊': 'yang', '己': 'yin',
        '庚': 'yang', '辛': 'yin',
        '壬': 'yang', '癸': 'yin'
    }
    
    # 获取日主五行属性和阴阳
    day_wuxing = gan_wuxing.get(day_gan)
    day_gender = gan_gender.get(day_gan)
    
    # 初始化十神结果
    result = {
        'year_god': '',
        'month_god': '',
        'time_god': ''
    }
    
    # 处理年干十神
    year_gan = gans[0]
    year_wuxing = gan_wuxing.get(year_gan)
    year_gender = gan_gender.get(year_gan)
    
    # 判断年干与日干的关系
    if year_gan == day_gan:  # 同天干
        result['year_god'] = ten_gods_map['same']
    elif year_gender == day_gender:  # 同阴阳
        if sheng_relation.get(year_wuxing) == day_wuxing:  # 我生日主
            result['year_god'] = ten_gods_map['same_besheng']
        elif sheng_relation.get(day_wuxing) == year_wuxing:  # 日主生我
            result['year_god'] = ten_gods_map['same_sheng']
        elif ke_relation.get(year_wuxing) == day_wuxing:  # 我克日主
            result['year_god'] = ten_gods_map['same_beke']
        elif ke_relation.get(day_wuxing) == year_wuxing:  # 日主克我
            result['year_god'] = ten_gods_map['same_ke']
        else:
            result['year_god'] = ten_gods_map['same']
    else:  # 不同阴阳
        if sheng_relation.get(year_wuxing) == day_wuxing:  # 我生日主
            result['year_god'] = ten_gods_map['diff_besheng']
        elif sheng_relation.get(day_wuxing) == year_wuxing:  # 日主生我
            result['year_god'] = ten_gods_map['diff_sheng']
        elif ke_relation.get(year_wuxing) == day_wuxing:  # 我克日主
            result['year_god'] = ten_gods_map['diff_beke']
        elif ke_relation.get(day_wuxing) == year_wuxing:  # 日主克我
            result['year_god'] = ten_gods_map['diff_ke']
        else:
            result['year_god'] = ten_gods_map['diff']
    
    # 类似地处理月干十神
    month_gan = gans[1]
    month_wuxing = gan_wuxing.get(month_gan)
    month_gender = gan_gender.get(month_gan)
    
    if month_gan == day_gan:
        result['month_god'] = ten_gods_map['same']
    elif month_gender == day_gender:  # 同阴阳
        if sheng_relation.get(month_wuxing) == day_wuxing:  # 我生日主
            result['month_god'] = ten_gods_map['same_besheng']
        elif sheng_relation.get(day_wuxing) == month_wuxing:  # 日主生我
            result['month_god'] = ten_gods_map['same_sheng']
        elif ke_relation.get(month_wuxing) == day_wuxing:  # 我克日主
            result['month_god'] = ten_gods_map['same_beke']
        elif ke_relation.get(day_wuxing) == month_wuxing:  # 日主克我
            result['month_god'] = ten_gods_map['same_ke']
        else:
            result['month_god'] = ten_gods_map['same']
    else:  # 不同阴阳
        if sheng_relation.get(month_wuxing) == day_wuxing:  # 我生日主
            result['month_god'] = ten_gods_map['diff_besheng']
        elif sheng_relation.get(day_wuxing) == month_wuxing:  # 日主生我
            result['month_god'] = ten_gods_map['diff_sheng']
        elif ke_relation.get(month_wuxing) == day_wuxing:  # 我克日主
            result['month_god'] = ten_gods_map['diff_beke']
        elif ke_relation.get(day_wuxing) == month_wuxing:  # 日主克我
            result['month_god'] = ten_gods_map['diff_ke']
        else:
            result['month_god'] = ten_gods_map['diff']
    
    # 类似地处理时干十神
    time_gan = gans[3]
    time_wuxing = gan_wuxing.get(time_gan)
    time_gender = gan_gender.get(time_gan)
    
    if time_gan == day_gan:
        result['time_god'] = ten_gods_map['same']
    elif time_gender == day_gender:  # 同阴阳
        if sheng_relation.get(time_wuxing) == day_wuxing:  # 我生日主
            result['time_god'] = ten_gods_map['same_besheng']
        elif sheng_relation.get(day_wuxing) == time_wuxing:  # 日主生我
            result['time_god'] = ten_gods_map['same_sheng']
        elif ke_relation.get(time_wuxing) == day_wuxing:  # 我克日主
            result['time_god'] = ten_gods_map['same_beke']
        elif ke_relation.get(day_wuxing) == time_wuxing:  # 日主克我
            result['time_god'] = ten_gods_map['same_ke']
        else:
            result['time_god'] = ten_gods_map['same']
    else:  # 不同阴阳
        if sheng_relation.get(time_wuxing) == day_wuxing:  # 我生日主
            result['time_god'] = ten_gods_map['diff_besheng']
        elif sheng_relation.get(day_wuxing) == time_wuxing:  # 日主生我
            result['time_god'] = ten_gods_map['diff_sheng']
        elif ke_relation.get(time_wuxing) == day_wuxing:  # 我克日主
            result['time_god'] = ten_gods_map['diff_beke']
        elif ke_relation.get(day_wuxing) == time_wuxing:  # 日主克我
            result['time_god'] = ten_gods_map['diff_ke']
        else:
            result['time_god'] = ten_gods_map['diff']
    
    return result

# 调用AI生成命理报告
def generate_ai_report(bazi_info):
    try:
        # 构建三个部分的提示词
        prompts = {
            "overview": f"""八字信息：{bazi_info['bazi']}\n你是一位八字教练，请根据以下命盘数据，撰写“命盘概览”模块，包含以下四部分：
1. 【八字命盘展示】
* 简洁文本方式列出年、月、日、时柱（带天干地支），并清晰标注“日主”。
2. 【日主解读 · 我的内在之光】
* 开篇解释“日主”概念（如：日主是你命盘中代表自我的核心能量）；
* 分析日主五行属性、状态（得令/受制/得生等）及其在整张命盘中的互动；
* 引出日主所象征的性格核心、行动风格和情绪表达方式；
3. 【五行能量分布 · 我的内在气候】
* 分析五行结构，指出偏旺/偏弱的元素；
* 强调五行之间的互动关系（如：水火冲、木生火弱、土制水强等），并与情绪模式、身心体验或惯性反应相连结；
4. 【反思邀请 · 我的共鸣写作】
* 你在生活中，何时最感受到这种“日主”能量？
* 哪种五行能量在你身上最常浮现？你如何与它相处？
* 是否有经验让你意识到自己“失衡”了？你如何找回自己？
请自由写下你此刻的共鸣、记忆或直觉……


请以专业、客观的口吻撰写，避免使用过于玄学或迷信的表述，重点强调八字所反映的性格特点和潜能。
""",
            "ten_gods": f"""八字信息：{bazi_info['bazi']}\n你是一位具备心理学与古典命理素养的八字分析者，请针对命盘中的十神结构，撰写人格互动分析。每个十神模块包含以下结构：
【十神名称】（如：正财、偏印等）
1. 天赋之光 · 我如何闪耀？
    * 分析该十神的正向特质、具体展现方式（如“正印带来安全感与包容力”）；
2. 互动之舞 · 我与世界的关系
    * 阐述该十神在社会关系、亲密关系或创造模式中的作用（如“偏财常见于行动导向的关系风格”）；
3. 成长契机 · 我如何平衡？
    * 识别该十神在命盘中处于何种状态（透出/藏干/有根/受制），点出挑战、转化方向；
4. 反思邀请 · 与我对话
    * 你是否认得出这种天赋？你在哪些时刻看见它？
    * 你在互动中是否常常展现这种模式？它带来什么？
    * 在你的人生中，它是否也曾带来困扰？你如何调和它？
输入格式：
* 每个十神的命盘结构描述（藏干/透干/合化等）
""",
            "action_guide": f"""八字信息：{bazi_info['bazi']}\n你是一位温柔而清晰的自我教练，请撰写“自我赋能与成长计划”模块，引导用户将认知转化为可落地的实践。模块结构如下：
1. 【我的优势清单与运用策略】
* 总结命盘中明显的优势特质（来自日主、十神、组合等）；
* 提供如何具体运用这些特质的建议场景（如职场、人际、创作）；
2. 【我的成长课题与应对智慧】
* 点出用户当前命盘中可成长之处（五行失衡、过强或受克等）；
* 给出温和可行的转化建议（身心练习、习惯建立、表达方式）；
3. 【目标导航仪·自我书写】：
* 简要提示命盘中的某些倾向（如偏印、比肩、食神等）可能对应的发展领域；
* 提出 3 个开放式问题，帮助用户书写内心的答案；
* 最后一句鼓励语，引导用户把书写变成一种仪式感的行动。


"""
        }
        
        all_reports = {}
        
        # 由于Flowith API配额已过期，直接使用DeepSeek API
        for section, prompt in prompts.items():
            try:
                logger.info(f"使用DeepSeek API生成{section}报告")
                report = call_deepseek_api(prompt)
            except Exception as e:
                logger.error(f"DeepSeek API生成{section}报告出错: {e}")
                report = f"生成{section}报告时发生错误，请稍后再试。"
            
            all_reports[section] = report
            
        return all_reports
    except Exception as e:
        logger.error(f"生成AI报告出错: {e}")
        return {
            "overview": "生成报告时发生错误，请稍后再试。",
            "ten_gods": "生成报告时发生错误，请稍后再试。",
            "action_guide": "生成报告时发生错误，请稍后再试。"
        }

# 调用Flowith API
def call_flowith_api(prompt):
    """调用Flowith API生成命理分析报告，带有重试机制和超时设置"""
    max_retries = 3  # 最大重试次数
    retry_delay = 2  # 重试间隔（秒）
    timeout = 120    # 请求超时时间（秒）
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FLOWITH_KEY}",
        "Host": "edge.flowith.net",
        "User-Agent": "HTTPie"
    }
    
    # 根据Flowith API官方文档构建请求体
    payload = {
        "messages": [
            {"role": "system", "content": "请调用八字知识库内的知识。用细腻的文笔代入具体的场景，引发共鸣与思考。"},
            {"role": "user", "content": prompt}
        ],
        "model": "deepseek-chat",
        "stream": False,
        "kb_list": ["0ce99dca-a06e-404b-b4f0-38c53198b38a"] 
    }
    
    logger.info(f"调用Flowith API，请求数据: {json.dumps(payload, ensure_ascii=False)[:200]}...")
    
    # 实现重试机制
    for attempt in range(max_retries):
        try:
            # 发送请求，并指定超时时间
            response = requests.post(
                FLOWITH_ENDPOINT, 
                headers=headers, 
                json=payload,
                timeout=timeout  # 设置请求超时时间
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Flowith API响应成功: {json.dumps(result, ensure_ascii=False)[:200]}...")
                
                # Flowith API响应格式处理
                if 'content' in result:
                    return result['content']
                elif 'choices' in result and len(result['choices']) > 0 and 'message' in result['choices'][0]:
                    # 兼容OpenAI格式
                    return result['choices'][0]['message']['content']
                else:
                    logger.warning(f"Flowith API响应格式异常: {json.dumps(result, ensure_ascii=False)}")
                    # 如果响应格式异常，但有数据，尝试提取可能的内容
                    if isinstance(result, dict) and any(key for key in result.keys() if 'content' in key.lower()):
                        for key, value in result.items():
                            if 'content' in key.lower() and isinstance(value, str):
                                return value
                    # 如果完全无法提取，返回错误信息
                    return "生成报告时出现问题，响应格式异常。请稍后再试。"
            else:
                # 如果响应状态码不是200，记录错误并准备重试
                error_msg = f"Flowith API调用失败 (尝试 {attempt+1}/{max_retries}): {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))  # 每次重试的等待时间逐次增加
                    continue
                else:
                    # 如果所有重试都失败，返回错误信息
                    return f"抱歉，生成报告时出现问题(错误代码:{response.status_code})，请稍后再试。"
                
        except requests.exceptions.Timeout as e:
            # 超时异常处理
            logger.error(f"调用Flowith API超时 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return "抱歉，生成报告时连接超时，请稍后再试。"
        
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            # 连接错误或块编码错误处理
            logger.error(f"调用Flowith API连接错误 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return "抱歉，生成报告时网络连接出错，请稍后再试。"
                
        except Exception as e:
            # 其他异常处理
            logger.error(f"调用Flowith API未预期错误 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return f"抱歉，连接AI服务时出现问题: {str(e)[:100]}...，请稍后再试。"

def call_deepseek_api(prompt):
    """调用DeepSeek官方API生成命理分析报告"""
    max_retries = 3  # 最大重试次数
    retry_delay = 2  # 重试间隔（秒）
    timeout = 90     # 增加超时时间至90秒，给API足够响应时间
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # 构建请求体
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "请调用八字知识库内的知识，并会从来访者角度出发。用细腻的文笔代入具体的场景，引发共鸣与思考。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": False,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
    }
    
    logger.info(f"调用DeepSeek API，请求数据: {json.dumps(payload, ensure_ascii=False)[:200]}...")
    
    # 实现重试机制
    for attempt in range(max_retries):
        try:
            # 使用流式请求和分块传输，降低内存占用和超时风险
            logger.info(f"开始调用DeepSeek API，超时设置为{timeout}秒")
            response = requests.post(
                DEEPSEEK_API_ENDPOINT, 
                headers=headers, 
                json=payload,
                timeout=timeout,
                stream=True  # 启用流式传输
            )
            
            # 立即检查状态码
            logger.info(f"DeepSeek API状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 分块读取响应内容，并定期输出进度信息
                logger.info("开始分块读取响应内容...")
                content = ""
                chunk_count = 0
                total_bytes = 0
                
                try:
                    # 设置更小的块大小和进度报告
                    for chunk in response.iter_content(chunk_size=512):
                        if chunk:
                            chunk_text = chunk.decode('utf-8', errors='replace')  # 使用错误替换模式避免解码错误
                            content += chunk_text
                            chunk_count += 1
                            total_bytes += len(chunk)
                            
                            # 每接收几个块输出一次进度信息
                            if chunk_count % 5 == 0:
                                logger.info(f"正在读取数据: 已接收{chunk_count}个块，共{total_bytes}字节")
                except Exception as read_err:
                    # 捕获并记录读取过程中的错误
                    logger.error(f"读取响应内容时出错: {read_err}")
                    # 如果已经读取了一些内容，尝试继续JSON解析
                    if len(content) < 10:  # 如果内容太少，无法解析
                        raise Exception(f"响应内容读取失败，只收到{len(content)}字节数据")
                
                logger.info(f"完成响应内容读取，总共接收{total_bytes}字节数据")
                
                # 解析JSON结果
                logger.info(f"已成功读取响应内容，大小: {len(content)}字节")
                result = json.loads(content)
                logger.info(f"DeepSeek API响应成功: {json.dumps(result, ensure_ascii=False)[:200]}...")
                
                # DeepSeek API响应格式处理
                if 'choices' in result and len(result['choices']) > 0 and 'message' in result['choices'][0]:
                    # DeepSeek API使用OpenAI格式的响应
                    return result['choices'][0]['message']['content']
                else:
                    logger.warning(f"DeepSeek {DEEPSEEK_MODEL}模型响应格式异常: {json.dumps(result, ensure_ascii=False)}")
                    # 如果响应格式异常，但有数据，尝试提取可能的内容
                    if isinstance(result, dict) and any(key for key in result.keys() if 'content' in key.lower()):
                        for key, value in result.items():
                            if 'content' in key.lower() and isinstance(value, str):
                                return value
                    # 如果完全无法提取，返回错误信息
                    return "生成报告时出现问题，响应格式异常。请稍后再试。"
            else:
                # 如果响应状态码不是200，记录错误并准备重试
                error_msg = f"DeepSeek {DEEPSEEK_MODEL}模型调用失败 (尝试 {attempt+1}/{max_retries}): {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))  # 每次重试的等待时间逐次增加
                    continue
                else:
                    # 如果所有重试都失败，返回错误信息
                    return f"抱歉，生成报告时出现问题(错误代码:{response.status_code})，请稍后再试。"
                
        except requests.exceptions.Timeout as e:
            # 超时异常处理
            logger.error(f"调用DeepSeek {DEEPSEEK_MODEL}模型超时 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return "抱歉，生成报告时连接超时，请稍后再试。"
        
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            # 连接错误或块编码错误处理
            logger.error(f"调用DeepSeek {DEEPSEEK_MODEL}模型连接错误 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return "抱歉，生成报告时网络连接出错，请稍后再试。"
                
        except Exception as e:
            # 其他异常处理
            logger.error(f"调用DeepSeek {DEEPSEEK_MODEL}模型未预期错误 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                return f"抱歉，连接DeepSeek {DEEPSEEK_MODEL}模型时出现问题: {str(e)[:100]}...，请稍后再试。"
    




@app.route('/')
def index():
    current_year = datetime.now().year
    years = list(range(1950, current_year + 1))
    months = list(range(1, 13))
    days = list(range(1, 32))
    
    # 十二时辰列表，带时间范围
    shichens = [
        {"name": "子时", "range": "23:00-00:59"},
        {"name": "丑时", "range": "01:00-02:59"},
        {"name": "寅时", "range": "03:00-04:59"},
        {"name": "卯时", "range": "05:00-06:59"},
        {"name": "辰时", "range": "07:00-08:59"},
        {"name": "巳时", "range": "09:00-10:59"},
        {"name": "午时", "range": "11:00-12:59"},
        {"name": "未时", "range": "13:00-14:59"},
        {"name": "申时", "range": "15:00-16:59"},
        {"name": "酉时", "range": "17:00-18:59"},
        {"name": "戌时", "range": "19:00-20:59"},
        {"name": "亥时", "range": "21:00-22:59"}
    ]
    
    return render_template('index.html', years=years, months=months, days=days, shichens=shichens)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        shichen = data.get('shichen')
        
        # 记录请求详情
        logger.info(f"收到生成报告请求: 年={year}, 月={month}, 日={day}, 时辰={shichen}")
        
        # 根据时辰获取小时
        hour = SHICHEN_MAP.get(shichen, (0, 0))[0]
        
        # 计算八字
        bazi_info = calculate_bazi(year, month, day, hour)
        
        if not bazi_info:
            logger.error("计算八字信息失败")
            return jsonify({"error": "计算八字信息失败"}), 400
        
        logger.info(f"八字计算成功: {bazi_info['bazi']}")
        
        # 尝试使用generate_ai_report函数
        try:
            logger.info("尝试使用generate_ai_report函数生成报告...")
            reports = generate_ai_report(bazi_info)
            logger.info("使用generate_ai_report生成报告成功")
        except Exception as api_err:
            # 如果API调用出错，生成默认内容
            logger.error(f"API调用出错: {api_err}，使用预设模板")
            reports = {
                "overview": f"八字信息：{bazi_info['bazi']}\n\n在传统五行学说中，您的八字中包含了重要的信息。目前由于网络原因，我们无法生成详细分析。请稍后再试。",
                "ten_gods": "十神分析暂时无法生成，请稍后再试。",
                "action_guide": "行动指南暂时无法生成，请稍后再试。"
            }
        
        # 组合结果
        result = {
            "bazi_info": bazi_info,
            "reports": reports
        }
        
        logger.info("返回报告结果")
        return jsonify(result)
    except Exception as e:
        logger.error(f"生成报告请求处理出错: {e}")
        # 返回更详细的错误信息
        error_details = {"error": f"处理请求时出错: {str(e)}", "traceback": traceback.format_exc()}
        return jsonify(error_details), 500

# 添加直接返回静态文件内容的路由，解决Render.com部署问题
# 同时支持新旧两种路径
@app.route('/style.css')
@app.route('/static/style.css')
def serve_css():
    try:
        with open('static/style.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        logger.info(f"成功读取CSS文件，内容长度: {len(css_content)}")
        return css_content, 200, {'Content-Type': 'text/css', 'Cache-Control': 'no-cache'}
    except Exception as e:
        logger.error(f"读取CSS文件失败: {e}")
        return "", 500

@app.route('/script.js')
@app.route('/static/script.js')
def serve_js():
    try:
        with open('static/script.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        logger.info(f"成功读取JS文件，内容长度: {len(js_content)}")
        return js_content, 200, {'Content-Type': 'application/javascript', 'Cache-Control': 'no-cache'}
    except Exception as e:
        logger.error(f"读取JS文件失败: {e}")
        return "", 500

if __name__ == '__main__':
    # 本地开发环境
    app.run(debug=True, host='0.0.0.0', port=8090)
else:
    # 生产环境
    # 大多数托管平台会自动设置PORT环境变量
    import os
    port = int(os.environ.get("PORT", 8090))
    # 确保生产环境中不启用调试模式
    app.config['DEBUG'] = False
    # 禁用静态文件缓存，解决CSS/JS内容为空的问题
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
