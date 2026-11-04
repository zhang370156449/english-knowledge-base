# -*- coding: utf-8 -*-
"""
LexiFragment - 个人英语知识库自动同步脚本 v2.2
支持自动扫描短视频（包含夏风英语、阿深 Deep、Ryan的英语笔记、晓试Ezam、英语兔、长安老张、瑞杰谈英语、每天蹲Tibo、曲木古也等）、
自动提取高清封面、智能解析核心高频动词（take/get/make/put/have等）与词根、解析 Markdown 文章与书籍，
并自动更新 data.js 数据库。
"""

import os
import re
import sys
import json
import cv2

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(BASE_DIR, 'thumbnails')
os.makedirs(THUMB_DIR, exist_ok=True)

IGNORE_FOLDERS = {'logs', 'articles', 'books', '.gemini', '.git', 'scratch', '_staging', '__pycache__', 'thumbnails', '瑞杰老师 30 天英语实战训练营(1)'}
VIDEO_EXTS = {'.mp4', '.mkv', '.mov', '.webm', '.avi'}

AUTHOR_CONFIGS = {
    '夏风英语': {
        'desc': '高考英语145 · 逻辑透视英语',
        'avatar': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'xf',
        'default_tag': '母语者视角'
    },
    '阿深 Deep': {
        'desc': '母语者语感 · 颠覆死记硬背',
        'avatar': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'as',
        'default_tag': '语感底层'
    },
    'Ryan的英语笔记': {
        'desc': '手绘图解 · 边画边写串记词根',
        'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'rn',
        'default_tag': '手绘词根'
    },
    '晓试Ezam': {
        'desc': '高频词根 · 无痛串记高频词',
        'avatar': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'ez',
        'default_tag': '词根串记'
    },
    '英语兔': {
        'desc': '全网语法标杆 · 语音与句型心法',
        'avatar': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'rb',
        'default_tag': '语法与发音'
    },
    '长安老张': {
        'desc': '万能词物理溯源 · 颠覆死记硬背',
        'avatar': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'lz',
        'default_tag': '核心动词'
    },
    '瑞杰谈英语': {
        'desc': '30个核心高频词 · 极简状态转换',
        'avatar': 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'rj',
        'default_tag': '高频动词'
    },
    '每天蹲Tibo': {
        'desc': '母语者通感 · 核心动词直觉',
        'avatar': 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'tb',
        'default_tag': '母语直觉'
    },
    '曲木古也': {
        'desc': '英语思维 · 5大万能词框架',
        'avatar': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'qm',
        'default_tag': '万能动词'
    },
    '英语文化与习俗': {
        'desc': '英美文化渊源 · 社交礼仪 · Small Talk与潜规则',
        'avatar': 'https://images.unsplash.com/photo-1513151233558-d860c5398176?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'cl',
        'default_tag': '英语文化'
    }
}

KEYWORD_MAP = {
    # 核心动词 (Core Verbs)
    "take": "take",
    "get": "get",
    "make": "make",
    "put": "put",
    "have": "have",
    "do": "do",
    "let": "let",
    "go": "go",
    "come": "come/go",
    "watch": "watch",
    "know": "know",
    "see": "see/look",
    "look": "see/look",
    "start": "start/begin",
    "begin": "start/begin",
    "can": "can",
    "would": "would/will",
    "will": "would/will",
    "want": "want",
    "万能动词": "万能动词",
    # 核心介词与功能词 (Prepositions & Particles)
    "on": "on",
    "off": "off",
    "to": "to",
    "for": "for",
    "in": "in",
    "at": "at",
    "of": "of",
    "by": "by",
    "with": "with",
    "from": "from",
    "over": "over",
    "ing": "ing",
    "as": "as",
    # 词根与其他
    "airport": "port",
    "before": "fore",
    "虚拟语气": "虚拟语气",
    "hospital": "hospit",
    "serve": "serve",
    "阿sir": "cip/ceiv",
    "science": "sci",
    "18万": "构词法",
    "易混淆": "易混词",
    "字幕秒懂": "听力心法",
    "语法错误": "高考语法",
    "shit": "口语俚语",
    "strengths": "发音技巧",
    "late": "late/latter",
    "expect": "expect/except",
    "con-": "con-",
    # 英语文化、英美习俗与礼仪潜规则
    "前世今生": "文化渊源",
    "soccer": "词源文化",
    "second": "词源文化",
    "normal university": "词源文化",
    "思维差异": "思维差异",
    "语言思维": "思维差异",
    "否定疑问句": "思维逻辑",
    "small talk": "Small Talk",
    "小费": "小费文化",
    "用餐礼仪": "就餐礼仪",
    "服务员": "就餐礼仪",
    "酒吧": "英美习俗",
    "送礼": "社交礼仪",
    "惹毛": "文化禁忌",
    "sir": "英美习俗"
}

CULTURE_CREATOR_MAP = {
    1: ("英语兔", "语言演化史"),
    2: ("英语兔", "足球与牛津俚语"),
    3: ("英语兔", "时间度量文化"),
    4: ("英语兔", "师范大学由来"),
    5: ("Real麦克老师", "中西思维图式"),
    6: ("大胡子老师Jesse", "母语否定疑问句"),
    7: ("JZ", "Small Talk艺术"),
    8: ("Keyvi", "精英社交破冰"),
    9: ("美丽大鸭梨", "北美公共安全感"),
    10: ("小姨Priscilla", "低成本社交法则"),
    11: ("侃哥侃英语", "就餐小费潜规则"),
    12: ("托哥", "北美餐厅小费内幕"),
    13: ("全球不知道", "小费制度历史渊源"),
    14: ("阿福的英语课堂", "服务费vs小费"),
    15: ("晓明哥DonLee", "中美用餐礼仪"),
    16: ("励博教育奥斯卡", "英式餐厅眼神礼仪"),
    17: ("老常带你看世界", "英国Pub点酒潜规则"),
    18: ("Keyvi", "跨文化送礼法则"),
    19: ("瑞得福全英播客", "5大交际隐私雷区"),
    20: ("土拨鼠老师说英语", "英美Sir称谓差异")
}

SUBTITLE_MAP = {
    "10分钟了解英语的前世今生：语言与历史文化演变": "英语兔：从古英语盎格鲁-撒克逊到现代全球通用语的千年演进史诗",
    "football 与 soccer 的文化渊源：到底是谁发明的？": "为什么美国叫 soccer 英国叫 football？揭秘牛津俚语与现代足球分流史",
    "为什么 second 既是“秒”又是“第二”？": "古巴比伦六十进制与中世纪拉丁天文文献的第二次细分秘密",
    "为什么“师范大学”叫 normal university？": "法国高等师范学院与西方规范化范式教育历史的精彩溯源",
    "什么是中西方语言思维的深层差异？": "Real麦克老师深度拆解：思维具象化 vs 结构化在日常表达中的冲突与融合",
    "英语母语者是怎么想的：否定疑问句背后的认知逻辑": "为什么老外不说‘对，我不去’？彻底搞懂 Yes/No 的绝对真实性原则",
    "Small Talk 艺术：英美社交最核心的破冰润滑剂": "打破社恐！掌握英美日常电梯、派对闲聊的底层安全感与破冰法门",
    "老钱与精英社交：为什么 Small Talk 如此重要？": "浅层闲聊背后的社会化试探与非侵入式社交边界礼仪",
    "在美国后我才懂：Small Talk 是陌生人最温柔的安全感": "北美公共空间礼貌习惯：用微笑与闲聊构筑人与人之间的防备卸载",
    "美国最低成本的日常社交法则：真实文化观察": "如何用几句话化解尴尬、得体回应并在恰当节点礼貌结束对话",
    "刚来美国吃饭看账单懵了：小费到底该怎么给？": "侃哥详解堂食、外带、服务费与 15%-20% 小费比例的计算潜规则",
    "北美餐厅潜规则：服务员亲述小费内幕与底层规则": "托哥纽约实地探访：底薪制度下的小费生存机制与不给小费的后果",
    "美国小费文化的历史起源与争议：到底该不该给？": "从欧洲贵族封建恩赐到美国内战后的商业转嫁：透视争议最大的制度",
    "国外小费文化：服务费 ≠ 小费的那些规矩": "阿福老师划重点：Service Charge 与 Tip 的关键区别，避免重复掏钱",
    "盘点中美用餐礼仪与餐桌潜规则差异": "刀叉摆放暗语、公共菜品分食习惯、大声招手与眼神示意的文化避坑",
    "在英国餐厅喊“服务员”大声招手为什么很不礼貌？": "英式就餐的克制与优雅：为什么大声呼唤是失礼，如何用眼神呼叫结账",
    "英国 Pub 酒吧潜规则：别踩点酒与品牌雷区": "酒吧没有服务生！吧台排队暗号、Round 轮流请酒文化与点单秘籍",
    "跨文化送礼指南：老钱与王室社交的送礼之道": "西方礼仪精髓：重在手写感谢信与心意卡，如何送礼不给对方施加负担",
    "一句话惹毛外国人：英美文化交际禁忌与个人边界": "薪资、年龄、婚姻、政治与宗教：不可逾越的 5 大个人隐私雷区",
    "英美文化差异之“Sir”的潜规则：荣誉还是距离感？": "英国贵族骑士爵位 vs 美国服务性称呼：脱口秀爆笑揭秘文化认知的反差",
    "英语万能词 take 的真实含义到底是什么？": "物理溯源：主动伸手、吞下、承受与心理搬运的母语者图式",
    "背5000个单词，不如学这30个核心词：take 篇": "随身带走、主动拿取与花销承担的核心规律",
    "母语者眼里的 take，到底是什么感觉？": "take a photo / medicine / bus / shower 的母语通感",
    "一次搞定英语中使用频率最高的词 get": "从无到有、磁铁吸纳与状态转换的核心画面",
    "背5000个单词，不如学这30个核心词：get 篇": "获赞37万爆款神作：用极简状态转换打通 get 全部用法",
    "万能词 make 的真实底层逻辑是什么？": "施加巨大压力、从无到有强行塑形的创造过程",
    "背5000个单词，不如学这30个核心词：put 篇": "把物体精准放置在特定维度的母语思维",
    "最重要的英文单词 have，90%的人都误解了": "摆脱死板拥有，理解贴标签与状态维系的真实本质",
    "最被错误解读的词 do，它真的不是“做”": "纯粹动作驱动力的释放与承接",
    "中文翻译最错误的词 Let：松手的逻辑真相": "放行、撤销阻力、顺其自然的母语者心智",
    "被误解最深的单词 go，它居然有45种含义": "从撤销阻力与远离原点的物理意象出发，打通全部短语",
    "“来是come去是go”这句顺口溜害惨了中国学生": "空间锚点与心理视角的双向运动图式",
    "See、Look、Watch：别再凭感觉乱用了": "从被动感官摄入到主动注视的精准辨析",
    "背5000个单词，不如学这30个核心词：watch 篇": "专注盯防与动态监视的深层图式",
    "90%中国人都误解的词 Know": "从认知浸润到胸有成竹的底层逻辑",
    "都是开始：为什么启动叫Start，看书叫Begin？": "突发性点火冲刺 vs 流程性渐进展开的深层区别",
    "说 can 以为是“能”，老外听到的却是“懂”": "从认知能力到掌握规律的物理词源",
    "Would 只是 Will 的过去式？它是英语里的缓冲带": "心理距离与社交礼貌的弹性开关",
    "两个“想要”want 与 would like 的真实区别": "原始饥渴冲动 vs 优雅心理偏好的分寸感",
    "英语里的万能动词，掌握这 5 个就够了": "动词框架与母语思维的降维打击",
    "ON 翻译成“在上面”，误导了亿万中国学生！": "物理原像不是上下，而是两个表面紧紧贴合与持续连接",
    "只用一个“脱”字，彻底搞懂 30 个 off 词组": "断开连接、脱离轨道与释放势能的物理画面",
    "学了10年不知道 to 的真实含义：灵魂驱动力": "一根强力指向终点的箭头，带来结果与必然归宿",
    "万能词 for 意思多到记不完？看懂这个物理画面": "心中所向、为之预留与价值交换的等价天平",
    "介词怎么用都错？彻底分清 to 和 for 的区别": "有明确终点的箭头 vs 有预留目的的朝向",
    "英语母语者的直觉：IN 的本质是万物皆可包": "三维空间包裹感与进入沉浸状态的底层画面",
    "At 真实含义拆解：At、On、In 是维度的降维打击": "点、线、面、立体的空间几何降维心法",
    "英语的灵魂 of：没人理解它的从属真相": "母体剥离、同源衍生与属性归属的深层纽带",
    "by 有38种翻译？这一个物理画面秒杀全场": "近在咫尺、借助途径与并肩前行的核心线索",
    "别再把 With 当成“和”，它是万物合一的力": "伴随共振、并肩携手与工具赋能的真实力学",
    "From：一根向你射来的动态射线": "源头喷涌与距离延伸的动态力量感",
    "OVER：从起跳、悬空到尘埃落地": "跨越障碍、完全覆盖与画圆闭合的完整轨迹",
    "搞懂 ing 的底层逻辑，瞬间秒杀 doing to do": "正在发生、浸润其中与动态画面的身临其境",
    "as 有七个意思？其实它只是一把木匠的尺子": "等长衡量、同步推演与如实映射的母语逻辑"
}

def extract_thumbnail_if_missing(video_path, out_thumb_path):
    if os.path.exists(out_thumb_path) and os.path.getsize(out_thumb_path) > 1024:
        return True
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 1.5))
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
            ret, frame = cap.read()
        cap.release()
        if ret:
            h, w = frame.shape[:2]
            scale = 640.0 / h
            new_w = int(w * scale)
            resized = cv2.resize(frame, (new_w, 640), interpolation=cv2.INTER_AREA)
            _, buf = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 88])
            with open(out_thumb_path, 'wb') as f:
                f.write(buf)
            return True
    except Exception as e:
        print(f"Error extracting thumbnail for {video_path}: {e}")
    return False

def get_video_duration_str(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        secs = int(frames / fps) if fps else 0
        mins = secs // 60
        rem_secs = secs % 60
        return f"{mins}:{rem_secs:02d}"
    except Exception:
        return "2:30"

def parse_markdown_with_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    meta = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.splitlines():
                line = line.strip()
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    meta[k] = v
                    
    return meta, body

def determine_smart_keyword(title, filename):
    lower_t = title.lower()
    lower_f = filename.lower()
    
    # Priority 1: Culture & Etiquette Topics
    culture_kw = [
        ("前世今生", "文化溯源"),
        ("soccer", "词源文化"),
        ("second", "词源文化"),
        ("normal university", "词源文化"),
        ("思维差异", "思维差异"),
        ("否定疑问句", "思维逻辑"),
        ("small talk", "Small Talk"),
        ("小费", "小费文化"),
        ("用餐礼仪", "就餐礼仪"),
        ("服务员", "就餐礼仪"),
        ("酒吧", "英美习俗"),
        ("送礼", "社交礼仪"),
        ("惹毛", "文化禁忌"),
        ("sir", "英美习俗")
    ]
    for k_trig, k_val in culture_kw:
        if k_trig in lower_t or k_trig in lower_f:
            return k_val
            
    # Priority 2: Verbs, Roots and Particles (avoiding substring false matches like 'on' in 'second')
    for k_trigger, k_word in KEYWORD_MAP.items():
        trig = k_trigger.lower()
        if len(trig) <= 3 and trig.isalpha():
            if re.search(r'(?i)(?:\b|[\u4e00-\u9fa5\s_-])' + re.escape(trig) + r'(?:\b|[\u4e00-\u9fa5\s_-])', title):
                return k_word
        else:
            if trig in lower_t or trig in lower_f:
                return k_word
            
    m_root = re.search(r'词根\s*([a-zA-Z]+)', title)
    if m_root:
        return m_root.group(1).lower()
        
    m_root2 = re.search(r'前缀\s*([a-zA-Z\-]+)', title)
    if m_root2:
        return m_root2.group(1).lower()
        
    m_eng = re.findall(r'[a-zA-Z]{2,12}', title)
    if m_eng:
        clean = [e.lower() for e in m_eng if e.lower() not in ['mp4', 'the', 'and', 'for', 'with', 'video', 'ryan', 'ezam']]
        if clean:
            return clean[0]
            
    for term in ['定语从句', '名词性从句', '时态', '被动语态', '从句', '发音', '听力']:
        if term in title:
            return term
            
    return 'Core'

def main():
    print("=" * 60)
    print("LexiFragment 知识库扫描与索引生成器 v2.2")
    print(f"扫描根目录: {BASE_DIR}")
    print("=" * 60)
    
    existing_meta_map = {}
    data_js_path = os.path.join(BASE_DIR, 'data.js')
    if os.path.exists(data_js_path):
        try:
            with open(data_js_path, 'r', encoding='utf-8') as f:
                content = f.read()
                m = re.search(r'window\.LEXI_DATA\s*=\s*(\{.*?\});', content, re.DOTALL)
                if m:
                    old_db = json.loads(m.group(1))
                    for item in old_db.get('items', []):
                        if 'src' in item:
                            existing_meta_map[item['src']] = item
        except Exception:
            pass

    all_items = []
    author_set = set()
    
    # 1. 扫描所有作者视频文件夹
    for entry in sorted(os.listdir(BASE_DIR)):
        full_p = os.path.join(BASE_DIR, entry)
        if not os.path.isdir(full_p) or entry in IGNORE_FOLDERS or entry.startswith('.'):
            continue
            
        author_name = entry
        v_files = sorted([f for f in os.listdir(full_p) if os.path.splitext(f)[1].lower() in VIDEO_EXTS])
        if not v_files:
            continue
            
        author_set.add(author_name)
        cfg = AUTHOR_CONFIGS.get(author_name, {
            'desc': f'{author_name} 知识切片',
            'avatar': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&h=120&fit=crop&crop=faces',
            'prefix': re.sub(r'\W+', '', author_name)[:2].lower() or 'vd',
            'default_tag': '英语切片'
        })
        author_prefix = cfg['prefix']
        print(f"发现视频博主/目录: [{author_name}] (共 {len(v_files)} 个视频)")
        
        for idx, vf in enumerate(v_files, 1):
            rel_src = f"{author_name}/{vf}"
            v_path = os.path.join(full_p, vf)
            sz_mb = round(os.path.getsize(v_path) / (1024 * 1024), 2)
            
            thumb_name = f"{author_prefix}_{idx:02d}.jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_name)
            extract_thumbnail_if_missing(v_path, thumb_path)
            dur_str = get_video_duration_str(v_path)
            
            # Extract clean title from filename
            m = re.match(r'^(\d+)_(.+)\.\w+$', vf)
            raw_title = m.group(2) if m else os.path.splitext(vf)[0]
            
            # Check custom subtitle map
            subtitle = SUBTITLE_MAP.get(raw_title, '')
            if not subtitle:
                parts = raw_title.split(' ', 1)
                subtitle = parts[1] if len(parts) > 1 else '点击立即在沉浸剧场中播放与深度拆解'
                
            kw = determine_smart_keyword(raw_title, vf)
            
            item_tags = [author_name, cfg['default_tag'], kw]
            if author_name == '英语文化与习俗' and idx in CULTURE_CREATOR_MAP:
                speaker, topic_tag = CULTURE_CREATOR_MAP[idx]
                item_tags.extend([speaker, topic_tag])
            
            all_items.append({
                'id': f"{author_prefix}_{idx:02d}",
                'num': idx,
                'keyword': kw,
                'title': raw_title,
                'subtitle': subtitle,
                'author': author_name,
                'author_desc': cfg['desc'],
                'author_avatar': cfg['avatar'],
                'type': 'video',
                'category': '短视频',
                'tags': item_tags,
                'poster': f"thumbnails/{thumb_name}",
                'src': rel_src,
                'size_mb': sz_mb,
                'duration_est': dur_str
            })
                
    # 2. 扫描 articles 目录
    articles_dir = os.path.join(BASE_DIR, 'articles')
    if os.path.exists(articles_dir):
        art_files = sorted([f for f in os.listdir(articles_dir) if f.endswith(('.md', '.txt')) and not f.startswith('_')])
        print(f"发现文章目录: [articles] (共 {len(art_files)} 篇用户文章)")
        for idx, af in enumerate(art_files, 1):
            fp = os.path.join(articles_dir, af)
            meta, body = parse_markdown_with_frontmatter(fp)
            all_items.append({
                'id': f"art_{idx:03d}",
                'keyword': meta.get('keyword', 'ESSAY'),
                'title': meta.get('title', af),
                'subtitle': meta.get('subtitle', ''),
                'author': meta.get('author', '知识库精选'),
                'author_desc': meta.get('author_desc', '精选短文研读'),
                'author_avatar': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&h=120&fit=crop&crop=faces',
                'type': 'article',
                'category': '精选文章',
                'tags': [t.strip() for t in meta.get('tags', '深度研读').split(',')],
                'poster': meta.get('poster', 'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=800&h=500&fit=crop'),
                'src': f"articles/{af}",
                'content': body,
                'read_time': meta.get('read_time', '5 min')
            })
            
    # 3. 扫描 books 目录
    books_dir = os.path.join(BASE_DIR, 'books')
    if os.path.exists(books_dir):
        book_files = sorted([f for f in os.listdir(books_dir) if f.endswith(('.md', '.txt')) and not f.startswith('_')])
        print(f"发现书籍目录: [books] (共 {len(book_files)} 本原版书籍)")
        for idx, bf in enumerate(book_files, 1):
            fp = os.path.join(books_dir, bf)
            meta, body = parse_markdown_with_frontmatter(fp)
            all_items.append({
                'id': f"bk_{idx:03d}",
                'keyword': meta.get('keyword', 'BOOK'),
                'title': meta.get('title', bf),
                'subtitle': meta.get('subtitle', ''),
                'author': meta.get('author', '经典原著'),
                'author_desc': meta.get('author_desc', '原版英文典藏'),
                'author_avatar': 'https://images.unsplash.com/photo-1544717305-2782549b5136?w=120&h=120&fit=crop&crop=faces',
                'type': 'book',
                'category': '原版书籍',
                'tags': [t.strip() for t in meta.get('tags', '原版名著').split(',')],
                'poster': meta.get('poster', 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&h=500&fit=crop'),
                'src': f"books/{bf}",
                'content': body,
                'read_time': meta.get('read_time', '章节研读')
            })

    total_v = sum(1 for it in all_items if it['type'] == 'video')
    total_a = sum(1 for it in all_items if it['type'] == 'article')
    total_b = sum(1 for it in all_items if it['type'] == 'book')
    
    js_content = f"""// Auto-generated by sync_library.py - Do not edit directly
window.LEXI_DATA = {{
  "version": "2.2.0",
  "updated_at": "auto",
  "stats": {{
    "total_videos": {total_v},
    "total_articles": {total_a},
    "total_books": {total_b},
    "total_items": {len(all_items)},
    "authors": {json.dumps(sorted(list(author_set)), ensure_ascii=False)}
  }},
  "items": {json.dumps(all_items, ensure_ascii=False, indent=2)}
}};
"""
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print("=" * 60)
    print(f"数据同步成功！共收录: {total_v} 个视频, {total_a} 篇文章, {total_b} 本书籍 (总计 {len(all_items)} 个项目)")
    print(f"视频作者 ({len(author_set)} 位): {', '.join(sorted(list(author_set)))}")
    print(f"已更新数据库: {data_js_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()
