"""
DALL-E 3를 사용한 뉴스 썸네일 이미지 생성 + OG 이미지 스크래핑
Claude API로 뉴스 제목에 맞는 맞춤 프롬프트 생성
"""
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

STYLE_SUFFIX = (
    " Cute flat 2D cartoon illustration, Korean clipart style. "
    "Bright cheerful colors on a soft white background. "
    "2-3 simple rounded cartoon objects that clearly represent the topic. "
    "Friendly, colorful, Korean mobile app sticker aesthetic — playful personality, clean composition. "
    "No text, no letters, no people, no faces."
)


# ── Claude로 맞춤 프롬프트 생성 ─────────────────────────────────────────────

def generate_prompts_batch(titles: list, anthropic_api_key: str) -> list:
    """
    Claude Haiku로 한국어 뉴스 제목들에 대한 DALL-E 프롬프트 일괄 생성.
    Returns: prompt 문자열 리스트 (titles와 동일한 순서)
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_api_key)

        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": (
                    "다음 한국어 뉴스 제목 각각에 대해 DALL-E 3 이미지 생성용 영어 프롬프트를 만들어주세요.\n\n"
                    "스타일 규칙:\n"
                    "- 뉴스 내용을 직관적으로 나타내는 귀여운 카툰 오브젝트 2-3개\n"
                    "- 클립아트코리아 스타일: 밝고 친근한 색상, 둥근 모서리, 귀여운 한국 모바일 앱 스티커 느낌\n"
                    "- 예: '유튜브 쇼핑 수익화' → 'a cute cartoon play button with a small shopping bag and coins'\n"
                    "- 예: 'AI 기업 인수합병' → 'a friendly robot and a handshake icon with a small gear'\n"
                    "- 예: '브랜드 SNS 마케팅 트렌드' → 'a cute megaphone with colorful heart and like icons floating around'\n"
                    "- 예: '쿠팡 물류센터 확장' → 'a cartoon delivery box with wings and a location pin'\n"
                    "- 25단어 이내 영어, 오브젝트 종류와 배치만 묘사\n"
                    "- 사람 없음, 텍스트 없음, 배경 별도 묘사 불필요\n\n"
                    f"제목들:\n{numbered}\n\n"
                    "JSON 배열로만 응답 (다른 텍스트 없이):\n"
                    '["prompt1", "prompt2", ...]'
                ),
            }],
        )

        text = message.content[0].text.strip()
        start, end = text.find("["), text.rfind("]") + 1
        if start >= 0 and end > start:
            prompts = json.loads(text[start:end])
            if len(prompts) == len(titles):
                return [p + STYLE_SUFFIX for p in prompts]
    except Exception as e:
        print(f"  [WARN] Claude 프롬프트 생성 실패: {e}")

    # fallback: 키워드 매핑
    return [_build_fallback_prompt(t) for t in titles]


KEYWORD_MAP = {
    "AI": "artificial intelligence neural network concept",
    "인공지능": "artificial intelligence data visualization",
    "스타트업": "startup growth rocket launch business",
    "네이버": "Korean search engine portal interface",
    "카카오": "Korean messaging app mobile platform",
    "유튜브": "video streaming play button content creator",
    "인스타그램": "social media photo grid smartphone",
    "쿠팡": "e-commerce delivery package Korean retail",
    "광고": "digital advertising creative campaign display",
    "마케팅": "marketing strategy brand growth chart",
    "SNS": "social media network engagement icons",
    "커머스": "e-commerce shopping cart online retail",
    "OTT": "streaming service screen content entertainment",
    "메타": "social media advertising platform data",
    "구글": "search engine technology innovation",
    "애플": "premium technology product design minimal",
    "콘텐츠": "digital content creation media production",
    "브랜드": "brand identity logo design visual",
    "소비자": "consumer shopping behavior trend",
    "트렌드": "trend analysis data chart market",
    "MZ": "young generation lifestyle digital culture",
    "패션": "fashion style clothing industry trend",
    "뷰티": "beauty cosmetics skincare product",
    "게임": "gaming controller screen entertainment",
    "핀테크": "fintech digital payment mobile banking",
    "규제": "legal regulation compliance document shield",
    "ESG": "sustainability environment green energy",
    "웹툰": "webtoon comics digital illustration",
    "롱블랙": "premium business magazine article reading",
}


def _build_fallback_prompt(title: str) -> str:
    for kr, en in KEYWORD_MAP.items():
        if kr in title:
            return en + STYLE_SUFFIX
    return "business news concept abstract geometric shapes" + STYLE_SUFFIX


# ── DALL-E 3 이미지 생성 ────────────────────────────────────────────────────

def _generate_with_prompt(prompt: str, openai_api_key: str, save_path: Path) -> bool:
    """
    주어진 프롬프트로 DALL-E 3 이미지 생성 후 저장.
    Returns: True (성공 또는 기존 파일 존재), False (실패)
    """
    if save_path.exists():
        return True

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",   # 16:9 landscape — YouTube 썸네일 비율
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url, timeout=30).content
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(img_data)
        return True
    except Exception as e:
        print(f"  [WARN] 이미지 생성 실패: {e}")
        return False


def generate_iboss_images(
    iboss_items,
    openai_api_key: str,
    docs_dir: Path,
    date_iso: str,
    anthropic_api_key: str = "",
) -> dict:
    """
    아이보스 뉴스 항목별 AI 이미지 생성.
    Returns: {1-based index: relative_path_from_docs/v2/}
    """
    images_dir = docs_dir / "v2" / "images" / date_iso
    titles = [item.title for item in iboss_items]

    # Claude로 맞춤 프롬프트 생성
    if anthropic_api_key:
        prompts = generate_prompts_batch(titles, anthropic_api_key)
    else:
        prompts = [_build_fallback_prompt(t) for t in titles]

    result = {}
    for i, (item, prompt) in enumerate(zip(iboss_items, prompts), 1):
        filename = f"iboss-{i}.png"
        save_path = images_dir / filename
        print(f"     아이보스 [{i}/{len(iboss_items)}] {item.title[:30]}...")
        if _generate_with_prompt(prompt, openai_api_key, save_path):
            result[i] = f"images/{date_iso}/{filename}"
    return result


def generate_neusral_images(
    neusral_categories,
    openai_api_key: str,
    docs_dir: Path,
    date_iso: str,
    anthropic_api_key: str = "",
) -> dict:
    """
    뉴스럴 카테고리별 AI 이미지 생성.
    Returns: {category_name: relative_path_from_docs/v2/}
    """
    images_dir = docs_dir / "v2" / "images" / date_iso
    # 카테고리명 + 첫 번째 헤드라인을 함께 넘겨서 더 정확한 프롬프트 생성
    titles = [
        f"{cat.category}: {cat.headlines[0]}" if cat.headlines else cat.category
        for cat in neusral_categories
    ]

    if anthropic_api_key:
        prompts = generate_prompts_batch(titles, anthropic_api_key)
    else:
        prompts = [_build_fallback_prompt(t) for t in titles]

    result = {}
    for i, (cat, prompt) in enumerate(zip(neusral_categories, prompts)):
        filename = f"neusral-{i}.png"
        save_path = images_dir / filename
        print(f"     뉴스럴 [{i+1}/{len(neusral_categories)}] {cat.category}...")
        if _generate_with_prompt(prompt, openai_api_key, save_path):
            result[cat.category] = f"images/{date_iso}/{filename}"
    return result


# ── OG 이미지 스크래핑 ────────────────────────────────────────────────────

def fetch_og_image(url: str, save_path: Path) -> bool:
    """
    URL에서 이미지 스크래핑 후 저장.
    1순위: og:image 메타 태그
    2순위: 본문 첫 번째 http 이미지 (og:image가 없거나 비어있을 때)
    Returns: True (성공 또는 기존 파일 존재), False (실패)
    """
    if save_path.exists():
        return True

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        # 1순위: og:image
        og_tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        img_url = (og_tag.get("content", "") or "").strip() if og_tag else ""

        # 2순위: 본문 첫 번째 실제 이미지
        if not img_url:
            for img in soup.find_all("img", src=True):
                src = img.get("src", "")
                if src.startswith("http") and any(ext in src for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    img_url = src
                    break

        if not img_url:
            return False

        img_data = requests.get(img_url, headers=HEADERS, timeout=30).content
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(img_data)
        return True
    except Exception as e:
        print(f"  [WARN] OG 이미지 스크래핑 실패 ({url[:40]}...): {e}")
        return False


def fetch_longblack_image(longblack_item, docs_dir: Path, date_iso: str) -> str:
    if not longblack_item or not longblack_item.url:
        return ""
    save_path = docs_dir / "v2" / "images" / date_iso / "longblack.jpg"
    print("     롱블랙 OG 이미지 스크래핑...")
    if fetch_og_image(longblack_item.url, save_path):
        return f"images/{date_iso}/longblack.jpg"
    return ""


def fetch_stibee_images(stibee_items, docs_dir: Path, date_iso: str) -> dict:
    result = {}
    for i, item in enumerate(stibee_items or []):
        if not item.url:
            continue
        filename = f"stibee-{i}.jpg"
        save_path = docs_dir / "v2" / "images" / date_iso / filename
        print(f"     {item.source} OG 이미지 스크래핑...")
        if fetch_og_image(item.url, save_path):
            result[item.source] = f"images/{date_iso}/{filename}"
    return result
