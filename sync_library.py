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

IGNORE_FOLDERS = {
    'logs', 'articles', 'books', '.gemini', '.git', 'scratch', '_staging', '__pycache__', 'thumbnails',
    '瑞杰老师 30 天英语实战训练营(1)', '瑞杰老师 30 天英语实战训练营',
    '01.英语兔83节视频课（词汇.发音.音标.语法）', '2019版赖世雄经典英语语法视频课程'
}
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
        'desc': '全网语法标杆 · 83节系统语法/音标/发音全集',
        'avatar': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'rb',
        'default_tag': '系统语法'
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
    },
    '孙志立英语': {
        'desc': '国家级配音员 · 英语听力底层心法 · 200高频句型 · 经典原声精讲',
        'avatar': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'szl',
        'default_tag': '听力底层'
    },
    '英语Linlin老师': {
        'desc': '自然拼读体系 · 字母组合拼读实战 · 常见不发音口诀 · 零基础语法',
        'avatar': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&h=120&fit=crop&crop=faces',
        'prefix': 'll',
        'default_tag': '自然拼读'
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
    "最重要的英文单词 have，90人误解了": "摆脱死板拥有，理解贴标签与状态维系的真实本质",
    "最被错误解读的词 do，它真的不是“做”": "纯粹动作驱动力的释放与承接",
    "中文翻译最错误的词 Let：松手的逻辑真相": "放行、撤销阻力、顺其自然的母语者心智",
    "被误解最深的单词 go，它居然有45种含义": "从撤销阻力与远离原点的物理意象出发，打通全部短语",
    "“来是come去是go”这句顺口溜害惨了中国学生": "空间锚点与心理视角的双向运动图式",
    "See、Look、Watch：别再凭感觉乱用了": "从被动感官摄入到主动注视的精准辨析",
    "背5000个单词，不如学这30个核心词：watch 篇": "专注盯防与动态监视的深层图式",
    "90%中国人都误解的词 Know": "从认知浸润到胸有成竹的底层逻辑",
    "90中国人都误解的词 Know": "从认知浸润到胸有成竹的底层逻辑",
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

TITLE_DISPLAY_MAP = {
    "90中国人都误解的词 Know": "90%中国人都误解的词 Know",
    "最重要的英文单词 have，90人误解了": "最重要的英文单词 have，90%的人都误解了"
}

RABBIT_GRAMMAR_META = {
    1: ("冠词", "不定冠词 a/an、定冠词 the 与零冠词的底层指代逻辑与本质区别"),
    2: ("主谓一致", "单复数视角的本质真相，为什么 collective nouns 动词时单时复"),
    3: ("省略", "语言效率的极致追求：日常口语与书面语中的 7 种自然省略规律"),
    4: ("强调", "强调句 it is...that 与助动词 do 的高阶情感重音表达心法"),
    5: ("介词", "全网最通透介词图解：用三维几何降维打通全部核心介词原像"),
    6: ("独立主格", "分词作状语的终极进阶：逻辑主语独立并存的母语心智"),
    7: ("倒装句", "完全倒装与部分倒装的情绪推演：否定词前置与平衡句式的核心画面"),
    8: ("被动语态", "动作承受者锚点与客观叙事视角：何时必须用被动、何时万万不可用"),
    9: ("非谓语", "彻底理清不定式(未发/目的)、动名词(事实/抽象)、分词(进行/被动)"),
    10: ("状语从句", "让步状语从句：although/though/even if 的预期冲突与逻辑退让"),
    11: ("状语从句", "目的状语从句：so that/in order that 的心中指向与未来图景"),
    12: ("状语从句", "原因状语从句：because/since/as/for 认知层级与已知信息分布"),
    13: ("状语从句", "方式状语从句：as if/as though 的虚拟映射与如实临摹"),
    14: ("状语从句", "结果状语从句：so...that 与 such...that 的极端推演与尘埃落定"),
    15: ("状语从句", "条件状语从句：if/unless/provided 假设时空与主将从现真相"),
    16: ("状语从句", "比较状语从句：as...as 与 more...than 的标尺量度与等额缩减"),
    17: ("状语从句", "地点状语从句：where 与 wherever 的空间坐标与泛指场域"),
    18: ("状语从句", "时间状语从句：when/while/as 动作交叠与时间轴先后对齐心法"),
    19: ("宾语从句", "动作对象的完整展开：that/whether 与疑问词引导的名词性从句"),
    20: ("同位语从句", "抽象名词的等号解构：fact/idea/news 后面的深度事实补全"),
    21: ("表语从句", "系动词后的身份说明：主语本质属性与状态认知的全面延伸"),
    22: ("宾补从句", "主语+谓语+宾语+补语：让动作对象状态更加清晰的结构化心智"),
    23: ("主语从句", "形式主语 it 的偷懒心理：把沉重大头移到句尾的平衡美学"),
    24: ("定语从句", "形容词性关系从句：先行词与关系代词 which/who/that 的无缝拼接"),
    25: ("从句总纲", "主从复合句全景俯瞰：从名词从句、定语从句到状语从句的骨架结构"),
    26: ("虚拟语气", "时空拉远与心理距离：用过去时表达非真实愿望与假设的底层心理学"),
    27: ("16种时态", "1小时史诗级时态大课：4种时间 × 4种状态构建的完美时空矩阵"),
    28: ("语法体系", "封神之作：一个视频彻底说清整个英语语法认知框架与宏观蓝图")
}

RABBIT_PRON_META = {
    1: ("不送气音", "声带与气流的物理控制：sp/st/sk 后的轻微浊化真相与生理原理"),
    2: ("喉塞音", "声门闭锁产生的神秘停顿：母语者口语最地道的停顿标志音详解"),
    3: ("爆破音", "鼻爆破与舌爆破：气流改道鼻腔与舌侧释压的地道省力技巧"),
    4: ("失去爆破", "不完全爆破与无声除阻：相邻爆破音只成阻不发音的连读基本功"),
    5: ("英语语调", "26分钟母语腔调指南：升调、降调、平调与句子重音的音乐起伏"),
    6: ("等时性", "节奏与等时性规律：为什么中式字字均长会毁掉英语的律动感"),
    7: ("缩读", "口语中的紧缩音 Contraction：gonna/wanna/gotta 的物理缩合规律"),
    8: ("弱读", "Weak Forms 核心解密：介词、代词、助动词的虚化与中央元音化"),
    9: ("省音", "Elision 与吞音规律：H-dropping 与 G-dropping 的地道口语偷懒心法"),
    10: ("同化异化", "相邻音素相互影响的物理发音省力法则与地道语流变化"),
    11: ("连读加音", "元音与元音碰撞时的连接滑音 /j/ 与 /w/ 的自然过渡心法"),
    12: ("连音心法", "辅音+元音的狭义连读：像母语者一样如行云流水般平滑发音")
}

RABBIT_VOCAB_META = {
    1: ("古英语", "thou, thee, ye, you, thy, thine：英语第二人称代词的千年演化史"),
    2: ("词汇通识", "为什么中国人背了上万单词依然看不懂？打破中文逐字对应翻译"),
    3: ("词汇之最", "打破认知！究竟哪个才是英语里真正被词典承认的最长单词？"),
    4: ("词汇演进", "从化学大分子到长单词背后的构词野心与学术造词规则"),
    5: ("构词法", "派生、复合、转化、截短：英语词汇量从 1000 暴涨至 10000 的杠杆"),
    6: ("前世今生", "英语的前世今生：从日耳曼部落方言、诺曼法语侵略到全球通用语")
}

SUNZHILI_META = {
    1: ("听力心法", "听力练习根本不是听出来的问题，是记得住的问题", ["孙志立英语", "听力底层", "记忆底层", "听力心法"]),
    2: ("听力逻辑", "仔细听三分钟，搞懂听力底层逻辑与听觉通道", ["孙志立英语", "听力底层", "底层逻辑"]),
    3: ("听力心法", "听力总是听不清怎么办？揭秘大脑音频处理", ["孙志立英语", "听力底层", "听力障碍"]),
    4: ("听力口诀", "想练好听力，这个顺口溜你就不能不会！", ["孙志立英语", "听力口诀", "顺口溜", "发音技巧"]),
    5: ("听力心法", "抓关键词应该是练听力时的锦上添花，而不是无奈之举", ["孙志立英语", "听力底层", "关键词误区"]),
    6: ("听力逻辑", "听不是学习的对象，而是学习的方式与输入管道", ["孙志立英语", "听力底层", "输入心法"]),
    7: ("听力练习", "听力其实根本不用“听清”，来试试我的练习方法", ["孙志立英语", "听力底层", "模糊容错"]),
    8: ("听力误区", "“听清”每个文字是英语学习的陷阱，你的听力本就很好", ["孙志立英语", "听力底层", "去字面化"]),
    9: ("听力容错", "语言的容错很高，一定要大胆听与建立语感直觉", ["孙志立英语", "听力底层", "母语直觉"]),
    10: ("高频句型", "吃透 200 个常用句型，练到条件反射，口语自然流利", ["孙志立英语", "高频句型", "母语者思维", "脱口而出"]),
    11: ("口语心法", "学英语就是学说话，跟着我练习，口语自然流利", ["孙志立英语", "母语者思维", "口语流利"]),
    12: ("长句拆解", "带着你三分钟之内，搞定英语长难句意群切分", ["孙志立英语", "长难句拆解", "意群切分"]),
    13: ("学习心法", "方法不搞对，学什么教材都是哑巴英文", ["孙志立英语", "口语心法", "告别哑巴英语"]),
    14: ("句型教学", "手把手现场教学，从句型开始解决你的英文学习问题", ["孙志立英语", "高频句型", "现场教学"]),
    15: ("零基础指南", "零基础该怎么学英文，手把手带你学好句型骨架", ["孙志立英语", "零基础学习", "句型骨架"]),
    16: ("发音技巧", "掌握这个发音技巧，让你的发音立刻好十倍！", ["孙志立英语", "发音技巧", "纯正腔调"]),
    17: ("连读破局", "一条视频解决你在连读问题上的各种困惑与误区", ["孙志立英语", "发音技巧", "连读规则", "音变破局"]),
    18: ("长句朗读", "一条视频教会你掌握长难句的呼吸节拍与重音", ["孙志立英语", "长难句朗读", "节奏重音"]),
    19: ("场景口语", "用生活场景练口语，抓准语调重音，告别中式发音", ["孙志立英语", "语调重音", "告别中式发音"]),
    20: ("数字发音", "总是读不好数字？这条视频教你读顺十万百万", ["孙志立英语", "数字发音", "发音难点"]),
    21: ("流程心法", "按照正确的流程学英语：先听后说再读再写", ["孙志立英语", "学习流程", "母语习得顺序"]),
    22: ("纪录片配音", "试配一段纪录片原声的英文片段，感受真实母语腔调", ["孙志立英语", "纪录片原声", "配音精讲", "纯正腔调"]),
    23: ("原声精听", "手把手带你听懂英文原声，瞬间听懂真实语速", ["孙志立英语", "英文原声", "原声精听", "真实语速"]),
    24: ("电影配音", "分享一段配音《地球 劫后重生》，感受音色与情绪", ["孙志立英语", "纪录片原声", "经典配音"]),
    25: ("史诗原声", "分享一段配音《荷马史诗：从神话到科学》", ["孙志立英语", "纪录片原声", "西方经典"]),
    26: ("配音心法", "英文配音员带你了解英文发声与共鸣的秘密", ["孙志立英语", "发声共鸣", "配音员秘密"]),
    27: ("场景英语", "场景化美食英语教学，手把手教你地道介绍中国特色", ["孙志立英语", "美食英语", "地道表达", "文化传播"]),
    28: ("词汇心法", "背单词到底重要吗？听不懂和词汇量有多大关联", ["孙志立英语", "词汇底层", "词汇误区"]),
    29: ("构词底层", "靠词根词缀能背好单词吗？一条视频教你底层原理", ["孙志立英语", "词根词缀", "词汇逻辑"]),
    30: ("词汇逻辑", "词汇量和学好英语有什么关系？看完这条视频你就懂了", ["孙志立英语", "词汇底层", "词汇逻辑"]),
    31: ("记忆锚点", "增加记忆锚点，轻松记忆高频单词，告别遗忘曲线", ["孙志立英语", "记忆锚点", "高效记忆"])
}

LINLIN_META = {
    1: ("自然拼读", "零基础入门自然拼读的核心步骤与系统学习路径，建立见词能读底层认知", ["英语Linlin老师", "自然拼读", "速成指南", "Phonics"]),
    2: ("自然拼读", "打通单词认读与拼写双向通道，彻底告别死记硬背字母顺序", ["英语Linlin老师", "自然拼读", "单词认读", "Phonics"]),
    3: ("自然拼读", "掌握英语常见字母及字母组合音形对应规则，一秒解码常见高频词汇", ["英语Linlin老师", "自然拼读", "单词直读", "Phonics"]),
    4: ("自然拼读", "透彻解析自然拼读与国际音标的区别、适用场景与协同进阶技巧", ["英语Linlin老师", "自然拼读", "音标辨析", "Phonics"]),
    5: ("自然拼读", "高效拆分单词音节与拼读记忆底层逻辑，轻松实现长难词速记", ["英语Linlin老师", "自然拼读", "学霸心法", "Phonics"]),
    6: ("自然拼读", "通过听音辨音直击单词拼写结构，让英语单词默写百发百中", ["英语Linlin老师", "自然拼读", "默写心法", "Phonics"]),
    7: ("字母组合", "全景梳理英语常见元音组合拼读规则，攻克发音与拼读最易混淆关卡", ["英语Linlin老师", "字母组合", "元音组合", "Phonics"]),
    8: ("字母组合", "解析覆盖超50%词汇量的高频字母组合规律，拼读效率直线翻倍", ["英语Linlin老师", "字母组合", "高频组合", "Phonics"]),
    9: ("字母组合", "掌握常见辅音组合ch的清辅音拼读规则与发音口型定位", ["英语Linlin老师", "字母组合", "ch组合", "Phonics"]),
    10: ("字母组合", "透析wh与wr等w相关字母组合的纯正拼读与静音辨析", ["英语Linlin老师", "字母组合", "w组合", "Phonics"]),
    11: ("字母组合", "攻破gh在词首、词中、词尾的发音变化与不发音特例", ["英语Linlin老师", "字母组合", "gh组合", "Phonics"]),
    12: ("字母组合", "掌握gu组合在不同词汇中的辅音拼读要领，纠正常见中式误读", ["英语Linlin老师", "字母组合", "gu组合", "Phonics"]),
    13: ("字母组合", "系统讲解or在重读音节及w后的特殊发音规律，彻底分清长短元音", ["英语Linlin老师", "字母组合", "or组合", "Phonics"]),
    14: ("字母组合", "通过节奏感律动带读掌握er组合不同位置的发音轻重弱化", ["英语Linlin老师", "字母组合", "er组合", "Phonics"]),
    15: ("字母组合", "一网打尽ea长音/iː/、短音/e/及特殊音/eɪ/，告别拼读陷阱", ["英语Linlin老师", "字母组合", "ea组合", "Phonics"]),
    16: ("字母组合", "以顺口溜口诀秒分双元音ai与短元音a的口型开合与发音时长", ["英语Linlin老师", "字母组合", "ai与a", "Phonics"]),
    17: ("字母组合", "掌握爆破辅音c与流音l的快速舌位转换，拼读单词流畅无阻", ["英语Linlin老师", "字母组合", "cl组合", "Phonics"]),
    18: ("字母组合", "核心名词词尾tion的一步到位发音规律，背一组搞定一串大词", ["英语Linlin老师", "字母组合", "tion词缀", "Phonics"]),
    19: ("字母组合", "一次厘清字母c、k与组合ck在词首词尾的选词拼写规律", ["英语Linlin老师", "字母组合", "ck辨析", "Phonics"]),
    20: ("字母组合", "结合自然语境与音形联想，快速内化复杂字母组合的拼读模式", ["英语Linlin老师", "字母组合", "联想速记", "Phonics"]),
    21: ("发音规律", "26个英文字母Letter Name与Letter Sound的标准纯正示范精讲", ["英语Linlin老师", "发音规律", "26个字母", "Pronunciation"]),
    22: ("发音规律", "总结英语单词中b、k、w、l等字母不发音的黄金规律与经典例词", ["英语Linlin老师", "发音规律", "不发音规则", "Pronunciation"]),
    23: ("发音规律", "顺口溜神技归纳常见辅音静音现象，见词自知何时不发音", ["英语Linlin老师", "发音规律", "辅音静音", "Pronunciation"]),
    24: ("高频语法", "以生动直观的生活空间与时间维度，秒懂介词on与in的核心差异", ["英语Linlin老师", "高频语法", "介词on与in", "Grammar"]),
    25: ("高频语法", "30秒厘清方向目标指向to与受益目的for的语法逻辑与考点", ["英语Linlin老师", "高频语法", "介词to与for", "Grammar"]),
    26: ("高频语法", "将易混语法考点化为朗朗上口的口诀，零基础也能轻松掌握", ["英语Linlin老师", "高频语法", "语法顺口溜", "Grammar"])
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
            
            if author_name == '英语兔':
                m_rb = re.match(r'^(语法|发音|词汇|音标|精选)_(\d+)_(.+)\.mp4$', vf)
                if m_rb:
                    mod_type = m_rb.group(1)
                    ep_num = int(m_rb.group(2))
                    raw_title = m_rb.group(3)
                    if mod_type == '语法':
                        kw, subtitle = RABBIT_GRAMMAR_META.get(ep_num, ('系统语法', f'英语兔系统语法：第 {ep_num} 讲'))
                        item_tags = ['英语兔', '系统语法', kw]
                    elif mod_type == '发音':
                        kw, subtitle = RABBIT_PRON_META.get(ep_num, ('发音技巧', f'英语兔发音指南：第 {ep_num} 讲'))
                        item_tags = ['英语兔', '发音技巧', kw]
                    elif mod_type == '词汇':
                        kw, subtitle = RABBIT_VOCAB_META.get(ep_num, ('词汇构词', f'英语兔词汇探秘：第 {ep_num} 讲'))
                        item_tags = ['英语兔', '词汇构词', kw]
                    elif mod_type == '音标':
                        kw = '国际音标'
                        subtitle = f'英语兔48个国际音标全解：第 {ep_num} 讲 · {raw_title}'
                        item_tags = ['英语兔', '国际音标', '音标发音']
                    else:
                        kw = '精选短片'
                        subtitle = SUBTITLE_MAP.get(raw_title, f'英语兔经典碎片趣析：第 {ep_num} 讲')
                        item_tags = ['英语兔', '精选短片', '趣味剖析']
                    display_title = raw_title
                else:
                    raw_title = os.path.splitext(vf)[0]
                    display_title = raw_title
                    kw = '英语兔'
                    subtitle = '英语兔经典解析'
                    item_tags = ['英语兔', '系统语法']
            elif author_name == '孙志立英语':
                m_szl = re.match(r'^(\d+)_(.+)\.mp4$', vf)
                if m_szl:
                    szl_idx = int(m_szl.group(1))
                    clean_title = m_szl.group(2).replace('_', ' ')
                    if szl_idx in SUNZHILI_META:
                        kw, subtitle, item_tags = SUNZHILI_META[szl_idx]
                    else:
                        kw = '听力底层'
                        subtitle = clean_title
                        item_tags = ['孙志立英语', '听力底层']
                    display_title = clean_title
                else:
                    raw_title = os.path.splitext(vf)[0]
                    display_title = raw_title
                    kw = '听力底层'
                    subtitle = raw_title
                    item_tags = ['孙志立英语', '听力底层']
            elif author_name == '英语Linlin老师':
                m_ll = re.match(r'^(\d+)_(.+)\.mp4$', vf)
                if m_ll:
                    ll_idx = int(m_ll.group(1))
                    clean_title = m_ll.group(2).replace('_', ' ')
                    if ll_idx in LINLIN_META:
                        kw, subtitle, item_tags = LINLIN_META[ll_idx]
                    else:
                        kw = '自然拼读'
                        subtitle = clean_title
                        item_tags = ['英语Linlin老师', '自然拼读']
                    display_title = clean_title
                else:
                    raw_title = os.path.splitext(vf)[0]
                    display_title = raw_title
                    kw = '自然拼读'
                    subtitle = raw_title
                    item_tags = ['英语Linlin老师', '自然拼读']
            else:
                # Extract clean title from filename
                m = re.match(r'^(\d+)_(.+)\.\w+$', vf)
                raw_title = m.group(2) if m else os.path.splitext(vf)[0]
                display_title = TITLE_DISPLAY_MAP.get(raw_title, raw_title)
                
                # Check custom subtitle map
                subtitle = SUBTITLE_MAP.get(raw_title, '') or SUBTITLE_MAP.get(display_title, '')
                if not subtitle:
                    parts = display_title.split(' ', 1)
                    subtitle = parts[1] if len(parts) > 1 else '点击立即在沉浸剧场中播放与深度拆解'
                    
                kw = determine_smart_keyword(display_title, vf)
                
                item_tags = [author_name, cfg['default_tag'], kw]
                if author_name == '英语文化与习俗' and idx in CULTURE_CREATOR_MAP:
                    speaker, topic_tag = CULTURE_CREATOR_MAP[idx]
                    item_tags.extend([speaker, topic_tag])
            
            all_items.append({
                'id': f"{author_prefix}_{idx:02d}",
                'num': idx,
                'keyword': kw,
                'title': display_title,
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
