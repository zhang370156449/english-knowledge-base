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

AUTHOR_AVATARS = {
    '夏风英语': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&h=120&fit=crop&crop=faces',
    '阿深 Deep': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&h=120&fit=crop&crop=faces',
    'default': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&h=120&fit=crop&crop=faces'
}

def extract_thumbnail_if_missing(video_path, out_thumb_path):
    if os.path.exists(out_thumb_path) and os.path.getsize(out_thumb_path) > 1024:
        return True
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 1.2))
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

def parse_markdown_with_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    meta = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_meta = parts[1]
            body = parts[2].strip()
            for line in raw_meta.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip()
                    v = v.strip().strip('"\'')
                    if k == 'tags':
                        meta[k] = [t.strip() for t in re.split(r'[,，\s]+', v) if t.strip()]
                    else:
                        meta[k] = v
                        
    if 'title' not in meta:
        first_h = re.search(r'^#+\s+(.+)$', body, re.MULTILINE)
        if first_h:
            meta['title'] = first_h.group(1).strip()
        else:
            meta['title'] = os.path.splitext(os.path.basename(file_path))[0]
            
    return meta, body

def scan_all():
    print("=" * 60)
    print("LexiFragment 知识库全量自动扫描索引生成器 (v2.0 Claude Style)")
    print(f"扫描根目录: {BASE_DIR}")
    print("=" * 60)
    
    # Read existing curated data.js to preserve customized titles and keywords
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
        print(f"发现视频博主/目录: [{author_name}] (共 {len(v_files)} 个视频)")
        
        for idx, vf in enumerate(v_files, 1):
            rel_src = f"{author_name}/{vf}"
            v_path = os.path.join(full_p, vf)
            sz_mb = round(os.path.getsize(v_path) / (1024 * 1024), 2)
            
            # Extract / ensure thumbnail exists
            author_prefix = 'xf' if '夏风' in author_name else ('as' if '阿深' in author_name else re.sub(r'\W+', '', author_name)[:4].lower())
            thumb_name = f"{author_prefix}_{idx:02d}.jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_name)
            extract_thumbnail_if_missing(v_path, thumb_path)
            
            # Check if curated metadata exists
            if rel_src in existing_meta_map:
                item_data = existing_meta_map[rel_src]
                item_data['num'] = idx
                item_data['size_mb'] = sz_mb
                item_data['poster'] = f"thumbnails/{thumb_name}"
                all_items.append(item_data)
            else:
                # Newly added video: parse intelligently
                m = re.match(r'^(\d+)_(.+)\.\w+$', vf)
                raw_title = m.group(2) if m else os.path.splitext(vf)[0]
                parts = raw_title.split(' ', 1)
                title = parts[0]
                subtitle = parts[1] if len(parts) > 1 else ''
                
                # Extract clean keyword
                kw = title
                kw_m = re.search(r'(?:记住|搞懂|速通|吃透|分清|解析)\s*([a-zA-Z\s]+|[\u4e00-\u9fa5]+)', raw_title)
                if kw_m:
                    kw = kw_m.group(1).strip()
                    
                all_items.append({
                    'id': f"vid_{author_prefix}_{idx:02d}",
                    'num': idx,
                    'keyword': kw,
                    'title': raw_title,
                    'subtitle': subtitle or '点击立即沉浸播放与学习',
                    'author': author_name,
                    'author_desc': f'{author_name} 知识切片',
                    'author_avatar': AUTHOR_AVATARS.get(author_name, AUTHOR_AVATARS['default']),
                    'type': 'video',
                    'category': '短视频',
                    'tags': [author_name, '新添加视频'],
                    'poster': f"thumbnails/{thumb_name}",
                    'src': rel_src,
                    'size_mb': sz_mb,
                    'duration_est': '2~4 min'
                })
                
    # 2. 扫描 articles 目录 (跳过 _ 开头的模版文件)
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
                'author_desc': '深度语法与语感解析',
                'type': 'article',
                'category': '深度文章',
                'tags': meta.get('tags', ['深度文章']),
                'read_time': meta.get('read_time', '5 分钟精读'),
                'content': body,
                'filename': af
            })
            
    # 3. 扫描 books 目录 (跳过 _ 开头的模版文件)
    books_dir = os.path.join(BASE_DIR, 'books')
    if os.path.exists(books_dir):
        book_files = sorted([f for f in os.listdir(books_dir) if f.endswith(('.md', '.txt')) and not f.startswith('_')])
        print(f"发现书籍目录: [books] (共 {len(book_files)} 本用户书籍)")
        for idx, bf in enumerate(book_files, 1):
            fp = os.path.join(books_dir, bf)
            meta, body = parse_markdown_with_frontmatter(fp)
            all_items.append({
                'id': f"book_{idx:03d}",
                'keyword': meta.get('keyword', 'BOOK'),
                'title': meta.get('title', bf),
                'subtitle': meta.get('subtitle', ''),
                'author': meta.get('author', '经典名师'),
                'author_desc': '权威经典自学参考',
                'type': 'book',
                'category': '精选书籍',
                'tags': meta.get('tags', ['经典书籍']),
                'pages': meta.get('pages', '系统精读'),
                'summary': body,
                'filename': bf
            })
            
    v_count = len([i for i in all_items if i['type'] == 'video'])
    a_count = len([i for i in all_items if i['type'] == 'article'])
    b_count = len([i for i in all_items if i['type'] == 'book'])
    
    db = {
        'version': '2.0.0',
        'updated_at': 'auto',
        'stats': {
            'total_videos': v_count,
            'total_articles': a_count,
            'total_books': b_count,
            'total_items': len(all_items),
            'authors': sorted(list(author_set))
        },
        'items': all_items
    }
    
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write('// Auto-generated by sync_library.py - Do not edit directly\n')
        f.write('window.LEXI_DATA = ' + json.dumps(db, ensure_ascii=False, indent=2) + ';\n')
        
    print("\n" + "=" * 60)
    print("Claude Style 知识库索引更新完毕！")
    print(f"- 短视频: {v_count} 个")
    print(f"- 文章:   {a_count} 篇")
    print(f"- 书籍:   {b_count} 本")
    print(f"- 博主:   {', '.join(sorted(list(author_set)))}")
    print("=" * 60)

if __name__ == '__main__':
    scan_all()
