"""
自动文章生成器
===========
从模板和数据生成 SEO 文章，支持联盟推广链接
"""
import os
import re
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "scripts" / "templates"
OUTPUT_DIR = ROOT / "_posts"

# ---------- 加载联盟推广链接 ----------
AFFILIATE_FILE = ROOT / "config" / "affiliate_links.json"
AFFILIATE_LINKS = {}
if AFFILIATE_FILE.exists():
    try:
        with open(AFFILIATE_FILE, "r", encoding="utf-8") as f:
            AFFILIATE_LINKS = json.load(f).get("products", {})
        print(f"  [推广] 已加载 {len(AFFILIATE_LINKS)} 个产品的推广链接")
    except Exception as e:
        print(f"  [推广] 加载失败: {e}")

def get_affiliate_url(product_name):
    """获取产品的推广链接，多条时随机选一条，没有则返回空字符串"""
    products = AFFILIATE_LINKS.get("products", [])
    if not isinstance(products, list):
        return ""
    for p in products:
        if p.get("name") == product_name:
            urls = p.get("urls", [])
            if not urls:
                return ""
            return random.choice(urls)
    return ""

# ---------- 产品数据 ----------
# 品类列表，每类包含多个产品
CATEGORIES = {
    "笔记工具": {
        "slug": "note-taking",
        "products": [
            {"name": "Notion", "desc": "全能工作台，集笔记、数据库、项目管理于一体", "tagline": "适合团队协作", "url_slug": "notion", "features": ["多平台同步", "模板丰富", "数据库功能强大", "团队协作"], "pros": ["功能全面", "免费版够用"], "cons": ["学习曲线较陡", "网络依赖强"]},
            {"name": "Obsidian", "desc": "本地优先的知识管理工具，支持双向链接", "tagline": "适合个人知识库", "url_slug": "obsidian", "features": ["本地存储", "双向链接", "插件生态丰富", "Markdown 原生"], "pros": ["数据完全本地", "免费", "性能好"], "cons": ["同步需付费", "没有协作功能"]},
            {"name": "飞书文档", "desc": "字节跳动出品，文档与协作深度整合", "tagline": "国内团队首选", "url_slug": "feishu", "features": ["在线协作", "AI 辅助写作", "多维表格", "集成日历"], "pros": ["国内访问快", "协作体验好", "AI 功能免费"], "cons": ["国际化一般", "部分功能收费"]},
        ]
    },
    "AI 工具": {
        "slug": "ai-tools",
        "products": [
            {"name": "DeepSeek", "desc": "国产大语言模型，性价比极高", "tagline": "高性价比 AI 助手", "url_slug": "deepseek", "features": ["超长上下文", "代码能力强", "价格低廉", "中英文优秀"], "pros": ["价格便宜", "性能强", "国产"], "cons": ["偶尔不稳定", "多模态支持有限"]},
            {"name": "Claude", "desc": "Anthropic 出品，以安全性和创造力著称", "tagline": "编码辅助首选", "url_slug": "claude", "features": ["超长上下文", "代码能力强", "安全对齐", "多语言支持"], "pros": ["代码能力顶级", "长上下文", "安全性好"], "cons": ["需要翻墙", "价格偏高"]},
            {"name": "ChatGPT", "desc": "OpenAI 旗舰产品，功能最全面", "tagline": "全能型 AI", "url_slug": "chatgpt", "features": ["多模态", "联网搜索", "插件系统", "语音对话"], "pros": ["功能最全", "生态最大", "多模态强"], "cons": ["需要付费", "需翻墙", "中国区受限"]},
        ]
    },
    "云存储": {
        "slug": "cloud-storage",
        "products": [
            {"name": "百度网盘", "desc": "国内最大的云存储服务", "tagline": "国内存储首选", "url_slug": "baidu-pan", "features": ["2TB 免费空间", "在线预览", "文件分享", "手机备份"], "pros": ["国内访问快", "用户基数大", "生态完善"], "cons": ["下载限速", "隐私堪忧"]},
            {"name": "Google Drive", "desc": "谷歌出品，与谷歌生态深度整合", "tagline": "海外用户首选", "url_slug": "google-drive", "features": ["15GB 免费", "Google 全家桶", "协作编辑", "版本历史"], "pros": ["稳定性好", "协作强", "集成度高"], "cons": ["需翻墙", "免费空间较小"]},
            {"name": "Dropbox", "desc": "老牌云存储，同步体验最佳", "tagline": "同步体验最佳", "url_slug": "dropbox", "features": ["文件同步", "智能同步", "版本恢复", "分享链接"], "pros": ["同步最快", "体验最好", "安全性高"], "cons": ["免费空间仅 2GB", "价格较贵"]},
        ]
    },
}

# ---------- SEO 模板 ----------
HEADLINE_TEMPLATES = [
    "2026 年必试的{category}：{count} 款精选工具推荐",
    "{category}横评对比：哪款最适合你？",
    "亲测｜{count} 款{category}深度体验报告",
    "别再乱选了！{count} 款{category}真实评测",
    "{category}选购指南：从入门到精通",
]

INTRO_TEMPLATES = [
    "在当今数字化时代，选择合适的{category}可以极大提升工作效率。本文将深入评测{count} 款主流产品，从功能、价格、体验等维度进行全方位对比。",
    "面对市面上五花八门的{category}，很多人都不知道该如何选择。这篇文章花了整整两周时间，实测了{count} 款热门产品，希望能帮你做出最适合自己的决定。",
    "好的{category}能让你事半功倍。作为一个重度用户，我整理了{count} 款经过长时间深度使用的工具，逐一分析它们的优缺点。",
]

SECTION_TEMPLATES = """
## {product_name} 评测

{product_desc}。{product_tagline}。

### 核心功能

{features_bullets}

### 优点

{pros_bullets}

### 缺点

{cons_bullets}

### 适合谁用？

{suitable_for}

### 价格参考

{price_info}

{affiliate_box}

[👉 访问 {product_name} 官网](https://www.google.com/search?q={product_name_url})
"""

COMPARISON_TEMPLATES = """
## 功能对比一览

| 产品 | 价格 | 核心优势 | 适合人群 |
|------|------|---------|---------|
{table_rows}
"""

OUTRO_TEMPLATES = [
    "以上就是本次{category}的全部评测内容。选择工具最重要的是符合自己的实际需求，没有最好的，只有最适合的。希望这篇文章能帮到你。",
    "看完这些{category}的对比，你有答案了吗？如果时间有限，建议从自己的核心需求出发，挑选一两个先试用一段时间。",
    "工具只是手段，效率才是目的。选一个顺手的{category}就开始行动吧！如果你有其他推荐，欢迎在评论区分享。",
]

CLOSING = """
---

## 💰 省钱推荐

如果你需要云存储空间，推荐使用 **百度网盘**（国内访问快，2TB 免费空间）。
通过下方链接注册，你还能获得额外福利👇

[👉 免费领取百度网盘福利](https://pan.baidu.com/)

---

*本文发布于 {date}，内容仅为个人体验，仅供参考。部分链接可能包含推广链接，但不影响你的购买价格。*
"""


def pick_random(items):
    return items[random.randint(0, len(items) - 1)]


def make_bullets(items):
    return "\n".join([f"- {item}" for item in items])


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def generate_post(category_name, category_data, products):
    """生成一篇完整的文章"""
    count = min(len(products), 5)
    title = pick_random(HEADLINE_TEMPLATES).format(category=category_name, count=count)
    intro = pick_random(INTRO_TEMPLATES).format(category=category_name, count=count)

    # 生成各产品章节
    sections = []
    table_rows = []
    for p in products:
        features = make_bullets(p["features"])
        pros = make_bullets(p["pros"])
        cons = make_bullets(p["cons"])

        suitable = pick_random([
            f"{p['name']} 特别适合{p['tagline']}的场景。",
            f"如果你需要{p['name'].split()[0]}，那么{p['name']}是个好选择。",
            f"推荐{p['tagline']}的用户优先考虑{p['name']}。",
        ])

        price = pick_random([
            f"{p['name']} 提供免费版和付费版，具体价格请查看官网。",
            f"{p['name']} 的基础功能免费，高级功能需要订阅。",
        ])

        # 推广链接 CTA
        aff_url = get_affiliate_url(p["name"])
        if aff_url:
            affiliate_box = f"""
> 💡 **省钱小贴士**：通过下方链接前往 {p['name']} 官网，享受专属优惠（本站可能有少量推广佣金，不影响你的购买价格）。
>
> [👉 前往 {p['name']} 官网获取优惠]({aff_url})
"""
        else:
            affiliate_box = ""

        section = SECTION_TEMPLATES.format(
            product_name=p["name"],
            product_desc=p["desc"],
            product_tagline=p["tagline"],
            features_bullets=features,
            pros_bullets=pros,
            cons_bullets=cons,
            suitable_for=suitable,
            price_info=price,
            product_name_url=p["url_slug"],
            affiliate_box=affiliate_box,
        )
        sections.append(section)

        table_rows.append(
            f"| {p['name']} | 免费+付费 | {p['tagline']} | {suitable[:20]}..."
        )

    # 对比表格
    comparison = COMPARISON_TEMPLATES.format(table_rows="\n".join(table_rows))

    # 结尾
    outro = pick_random(OUTRO_TEMPLATES).format(category=category_name)

    # 完整正文
    body = f"{intro}\n\n{comparison}\n" + "\n---\n".join(sections) + f"\n\n{outro}\n\n{CLOSING.format(date=datetime.now().strftime('%Y-%m-%d'))}"

    # SEO meta
    slug = f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(category_data['slug'])}-review"
    excerpt = intro[:150] + "..."

    return {
        "title": title,
        "slug": slug,
        "body": body,
        "excerpt": excerpt,
        "category": category_data["slug"],
        "category_name": category_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S +0800"),
    }


def write_jekyll_post(post):
    """写入 Jekyll 格式的 markdown 文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = OUTPUT_DIR / f"{post['slug']}.md"

    front_matter = f"""---
layout: post
title: "{post['title']}"
date: {post['date']}
categories: [{post['category']}]
excerpt: "{post['excerpt']}"
---

{post['body']}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter)

    print(f"  ✅ {filepath.name}")
    return filepath


def main():
    print(f"{'='*40}")
    print(f"文章生成器运行中...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*40}")

    total = 0
    # 随机选取几个分类
    cats = list(CATEGORIES.items())
    random.shuffle(cats)

    for cat_name, cat_data in cats[:3]:
        products = cat_data["products"]
        # 随机选 2-3 个产品对比
        selected = random.sample(products, min(len(products), random.randint(2, 3)))
        post = generate_post(cat_name, cat_data, selected)
        write_jekyll_post(post)
        total += 1
        print(f"  分类: {cat_name}")

    print(f"\n✅ 完成，共生成 {total} 篇文章")
    print(f"📁 输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
