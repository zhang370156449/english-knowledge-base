# -*- coding: utf-8 -*-
"""
LexiFragment - 个人英语知识库自动同步脚本 v2.1
支持自动扫描短视频（包含夏风英语、阿深 Deep、Ryan的英语笔记、晓试Ezam、英语兔等）、
自动提取高清封面、智能解析核心词根/词眼与副标题、解析 Markdown 文章与书籍，
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

IGNORE_FOLDERS = {'logs', 'articles', 'books', '.gemini', '.git', 'scratch', '_staging', '__pycache__', 'thumbnails'}
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
    }
}

KEYWORD_MAP = {
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
    "will": "will",
    "shit": "口语俚语",
    "strengths": "发音技巧",
    "late": "late/latter",
    "expect": "expect/except",
    "con-": "con-"
}

def extract_thumbnail_if_missing(video_path, out_thumb_path):
    if os.path.exists(out_thumb_path) and os.path.getsize(out_thumb_path) > 1024:
        return True
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        # Try capture at 1.5s
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
    for k_trigger, k_word in KEYWORD_MAP.items():
        if k_trigger in title or k_trigger in filename:
            return k_word
            
    # Check for "词根 xxx"
    m_root = re.search(r'词根\s*([a-zA-Z]+)', title)
    if m_root:
        return m_root.group(1).lower()
        
    m_root2 = re.search(r'前缀\s*([a-zA-Z\-]+)', title)
    if m_root2:
        return m_root2.group(1).lower()
        
    # Check for explicit english word in title
    m_eng = re.findall(r'[a-zA-Z]{2,12}', title)
    if m_eng:
        clean = [e.lower() for e in m_eng if e.lower() not in ['mp4', 'the', 'and', 'for', 'with', 'video', 'ryan', 'ezam']]
        if clean:
            return clean[0]
            
    # Chinese core terms
    for term in ['定语从句', '名词性从句', '时态', '被动语态', '从句', '发音', '听力']:
        if term in title:
            return term
            
    return 'Core'

def main():
    print("=" * 60)
    print("LexiFragment 知识库扫描与索引生成器 v2.1")
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
            
            if rel_src in existing_meta_map:
                item_data = existing_meta_map[rel_src]
                item_data['num'] = idx
                item_data['size_mb'] = sz_mb
                item_data['poster'] = f"thumbnails/{thumb_name}"
                item_data['duration_est'] = dur_str
                all_items.append(item_data)
            else:
                m = re.match(r'^(\d+)_(.+)\.\w+$', vf)
                raw_title = m.group(2) if m else os.path.splitext(vf)[0]
                parts = raw_title.split(' ', 1)
                title = parts[0]
                subtitle = parts[1] if len(parts) > 1 else '点击立即沉浸播放与深度拆解'
                
                kw = determine_smart_keyword(raw_title, vf)
                
                all_items.append({
                    'id': f"{author_prefix}_{idx:02d}",
                    'num': idx,
                    'keyword': kw,
                    'title': title,
                    'subtitle': subtitle,
                    'author': author_name,
                    'author_desc': cfg['desc'],
                    'author_avatar': cfg['avatar'],
                    'type': 'video',
                    'category': '短视频',
                    'tags': [author_name, cfg['default_tag'], kw],
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
  "version": "2.1.0",
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
