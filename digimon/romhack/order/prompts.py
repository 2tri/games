"""그림 주문문 (gen_order.py 와 같은 문장). 롬 없이 쓸 수 있게 따로 둠 — build_order.py 가 씀.
gen_order.py 의 주문문을 고치면 여기도 같이 고친다."""
import specs
SERIES = {'qinglongmon': 'Digimon Adventure 02', 'imperialdramondragonmode': 'Digimon Adventure 02', 'lighdramon': 'Digimon Adventure 02', 'digmon': 'Digimon Adventure 02', 'archnemon': 'Digimon Adventure 02', 'diablomon': 'Digimon Adventure (movie)'}
LCD_OF = set()          # front_prompt 가 LCD 문장을 넣을 종 (build_order.py 가 채움)


def lst(xs): return '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(xs))

def dash(xs): return '\n'.join('- ' + x for x in xs)

def tones(e):
    t = e['tones']
    return (f"  - white = {t['white']}\n  - light gray = {t['light']}\n  - dark gray = {t['dark']}\n  - black = outline, {t['black']}")

def front_prompt(e):
    lcd = ("The second attached image is its original LCD sprite from the Digimon virtual pet toys. Follow that silhouette and those proportions "
           "(only the silhouette; the size and facing below still apply).\n") if e['id'] in LCD_OF else ''
    return (f"This is {e['ko']} ({e['en']}), a Digimon from {SERIES.get(e['id'], 'Digimon Adventure')}. It is NOT any other creature. "
            f"Keep this exact character: same species, same silhouette, same proportions, same parts.\n{lcd}\n"
            "Task: convert the attached picture into a late-1990s Game Boy Color monster RPG battle sprite (FRONT view). Change only the art style, never the design.\n\n"
            "Composition:\n- ONE square image, pure white background, nothing else.\n"
            "- The character faces slightly to the left (3/4 view), whole body visible, standing on the bottom edge, filling about 90% of the image height.\n\n"
            f"Style:\n- VERY low resolution: the character is only about {specs.px(e['grade'])} pixels tall. Use big chunky pixels; every pixel is a crisp square of the same size. "
            "No anti-aliasing, no blur, no gradients, no dithering, no ground shadow.\n"
            "- Simplify like a real 8-bit sprite: strong silhouette, thick black outline, big flat shapes. Drop small details.\n"
            "- Exactly 4 tones, GRAYSCALE only: white, light gray, dark gray, black. No colors.\n" + tones(e) + "\n\n"
            f"MUST KEEP (most important first):\n{lst(e['keep'])}\n\nMUST NOT:\n{dash(e['not_'])}\n\n"
            "No text, no frame, no grid lines, no background scenery.")

def back_prompt(e):
    return (f"Attached: (1) the official picture of {e['ko']} ({e['en']}), a Digimon, and (2) the FRONT sprite I already accepted. "
            "Draw the BACK sprite of the SAME character in the SAME pixel style and the SAME 4 gray tones.\n\n"
            "View: three-quarter REAR view, like a monster standing in front of the player in a Game Boy battle. The camera is behind and a little above it. "
            "The character faces AWAY toward the upper-right corner, so we see its back, its right shoulder and right arm, and a thin sliver of the right side of its head. "
            "NOT straight from behind, NOT symmetrical, NOT a mirror of the front.\n\n"
            "Composition: ONE square image, pure white background. Only the upper body and head; the lower body is cut off by the bottom edge. "
            "The character fills about 90% of the image width, about 45 pixels wide.\n\n"
            "Style: same as the front: big chunky pixels, crisp squares, thick black outline, no anti-aliasing, no gradients, no dithering. "
            "Exactly 4 tones (white, light gray, dark gray, black), same part-to-tone mapping as the front:\n" + tones(e) + "\n\n"
            f"MUST KEEP from behind:\n{lst(e['keep_back'])}\n\n"
            f"MUST NOT:\n- Do not show the face from the front.\n- Do not make it symmetrical.\n{dash(e.get('not_back', []) + e['not_'])}\n\n"
            "No text, no frame, no grid lines, no background.")

def flat_prompt(e):
    return (f"This is {e['ko']} ({e['en']}), a Digimon. It is NOT any other creature. Keep this exact character.\n"
            "Redraw the attached picture as a simple flat cartoon illustration: thick black outline, flat fills, no shading gradients, no texture, "
            "no background, pure white background.\n"
            "Use only 4 tones, GRAYSCALE: white, light gray, dark gray, black.\n" + tones(e) + "\n"
            "Front view, 3/4 facing left, whole body, standing on the bottom edge, filling 90% of a square image.\n"
            "Simplify small details away; keep the big shapes only.\n\n"
            f"MUST KEEP (most important first):\n{lst(e['keep'])}\n\nMUST NOT:\n{dash(e['not_'])}")

def sketch_prompt(e):
    """앞모습 주문문 (LCD 첨부판, 주말 그림 지시 3장의 「밑그림 주문문」). 첨부 1장 = LCD 원래 칸 ×8 (art/sketch/<id>_lcd_x8.png), 2장 = 공식 그림"""
    t = e['tones']
    return (f"Image 1 is the original low-resolution LCD pixel sprite (black dots on white) of {e['ko']} ({e['en']}), a Digimon from {SERIES.get(e['id'], 'Digimon Adventure')}. Image 2 is its official picture.\n"
            "Task: produce a cleaner 4-tone pixel sprite of the SAME character, keeping the exact silhouette, pose and proportions of Image 1. "
            "Use Image 2 only to decide what details go INSIDE that silhouette. Do not change the outline shape. Do not turn it into any other creature.\n"
            "- ONE square image, pure white background. The sprite fills about 90% of the image, standing on the bottom edge.\n"
            "- Same orientation as Image 1 (facing left). Whole body visible.\n"
            f"- VERY low resolution: about {specs.px(e['grade'])} pixels tall. Big chunky pixels, every pixel a crisp square of the same size. "
            "No anti-aliasing, no blur, no gradients, no dithering, no shadow.\n"
            "- Exactly 4 tones, GRAYSCALE only: white, light gray, dark gray, black.\n"
            f"  - white = {t['white']}\n  - light gray = {t['light']}\n  - dark gray = {t['dark']}\n  - black = outline, {t['black']}\n"
            f"MUST KEEP (most important first):\n{lst(e['keep'])}\n"
            f"MUST NOT:\n- Do not change the silhouette of Image 1.\n{dash(e['not_'])}\n"
            "No text, no frame, no grid lines, no background.")


def back_from_front(e):
    """뒷모습 주문문 (2026-10-04 방식: 앞모습은 게임 도트·받은 그림으로 확정 → 그 앞모습을 첨부 1장으로 붙여 뒷모습만 받음).
    첨부 1장 = 확정된 앞모습 크게(주문서의 「첨부용 앞모습」), 2장 = 공식 그림(있으면). e 에 keep_back 이 없으면 일반 문장"""
    name = f"{e['ko']} ({e['en']})" if e.get('en') else e['ko']
    keep = e.get('keep_back') or e.get('keep') or []
    keep_txt = f"MUST KEEP from behind:\n{lst(keep)}\n\n" if keep else ''
    return (f"Image 1 is the FRONT battle sprite of {name}, a Digimon, already finished for my Game Boy Color game. "
            "Image 2 (if attached) is its official picture, only to understand what the back looks like.\n\n"
            "Task: draw the BACK battle sprite of the SAME character, matching Image 1 exactly: same pixel size, same chunky pixels, same thick black outline, "
            "same 4 colors as Image 1 (white, its two body colors, black) used for the same body parts. Do not add new colors.\n\n"
            "View: three-quarter REAR view, like the player's own monster in a Game Boy battle. The camera is behind and a little above it. "
            "The character faces AWAY toward the upper-right corner, so we see its back, its right shoulder and right arm, and a thin sliver of the right side of its head. "
            "NOT straight from behind, NOT symmetrical, NOT a mirror of the front, NOT the face.\n\n"
            "Composition: ONE square image, pure white background. Only the upper body and head; the lower body is cut off by the bottom edge. "
            "The character fills about 90% of the image width.\n\n"
            "Style: big chunky pixels, every pixel a crisp square of the same size. No anti-aliasing, no gradients, no dithering, no shadow.\n\n"
            f"{keep_txt}MUST NOT:\n- Do not show the face from the front.\n- Do not make it symmetrical.\n- Do not change the colors of Image 1.\n\n"
            "No text, no frame, no grid lines, no background.")


def body_type(e):
    """PixelLab 캐릭터 유형 추천: 휴머노이드 / 네 발 걷기 / 관습(그 외)"""
    t = ' '.join([e.get('en', '')] + list(e.get('keep') or [])).lower()
    if any(w in t for w in ('four legs', 'four-legged', 'quadruped', 'on all fours', 'dragon mode', 'mammoth', 'wolf', 'dog', 'rhino', 'dinosaur on four')):
        return '네 발 걷기'
    if any(w in t for w in ('serpent', 'snake', 'whale', 'fish', 'blob', 'ball', 'larva', 'worm', 'egg', 'bag', 'shell', 'plant', 'flower', 'bird', 'insect', 'beetle', 'bee', 'wasp')):
        return '관습'
    return '휴머노이드'


def pixellab_prompt(e):
    """PixelLab 「등장인물 소개」(2000자 안). 롬 세션 「B형태」 조건: 56칸을 꽉 채우는 짧고 넓은 몸·큰 머리·특징 3~5개 굵게"""
    name = f"{e['en']} from Digimon" if e.get('en') else e['ko']
    keep = (e.get('keep') or [])[:5]
    t = e.get('tones') or {}
    col = ', '.join(x for x in (t.get('light') and 'light: ' + t['light'], t.get('dark') and 'dark: ' + t['dark']) if x)
    s = (f"{name}. Chunky retro monster RPG battle sprite (Game Boy Color era). "
         + ("Compact, bold shape that fills the whole square: big head about one third of the height, short wide body, short legs, arms close to the body; "
            if body_type(e) != '관습' else "Compact, bold shape that fills the whole square: big head and a short, wide, rounded body; ") +
         "wings, tail, horns or weapons spread out sideways so the sprite is almost as wide as it is tall. "
         "Keep only the most recognizable features, each drawn big and bold:\n" + '\n'.join('- ' + k for k in keep) + "\n"
         + (f"Colors: few flat colors, {col}. " if col else "Few flat colors. ")
         + "Thick black outline, no tiny details, no gradients, no background. Standing on the ground, three-quarter view facing left.")
    return s[:2000]


# ── 재미나이 대화 한 번에 깔아 두는 규칙 (2026-10-05 사용자: 매번 같은 말 반복하지 말고 서두에 한 번) ──
GEMINI_PRIMER = """From now on, in this chat, you are my pixel artist for a fan-made Game Boy Color monster RPG with Digimon. Every image you make must follow these rules:

ALWAYS
- ONE square image, pure white background, nothing else (no text, no frame, no grid lines, no ground shadow).
- Late-1990s Game Boy Color battle sprite style: big chunky pixels (every pixel a crisp square of the same size), thick black outline, flat shapes, no anti-aliasing, no gradients, no dithering.
- Exactly 4 tones, GRAYSCALE only: white, light gray, dark gray, black (black = outline, eyes).
- Never redesign the character. Same species, same parts, same proportions. Do not turn it into any other creature.

When I send a picture and write "FRONT: <name>"
- Convert THAT picture into the sprite exactly as it is: same pose, same facing direction, same proportions, same details. Change only the art style.
- Make it BIG: the whole character visible, standing on the bottom edge, filling the square as much as possible (about 95% of the height or width).

When I then write "BACK" (or "BACK: <name>" with a front sprite attached)
- Draw the BACK sprite of the same character, like the player's own monster in a classic Game Boy battle screen.
- Camera behind and a little above it; the character faces AWAY toward the upper-right, so we see its back, one shoulder and a thin sliver of the side of its head. Not a mirror of the front, no face.
- Show only the UPPER BODY big (head, shoulders, back, arms, the start of wings or tail); the lower body is cut off by the bottom edge. Fill the whole square; wing or tail tips may go outside the frame.
- Use the same 4 tones for the same body parts as the front.

Reply only with the image. Say "OK" now if you understand."""


def gemini_front(e): return 'FRONT: %s' % (e['en'] or e['ko'])
def gemini_back(e, has_front_in_chat=True): return 'BACK' if has_front_in_chat else 'BACK: %s (the attached image is its finished front sprite)' % (e['en'] or e['ko'])
