"""Regenerate native SVG cow portraits from the canonical expert roster.

Run from any directory: python scripts/generate-brand.py
The roster owns stable IDs and professional profiles; generated copies are
consumed by the browser, local API and Vercel API. No network or credentials.
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend/public/assets"

# Simple picturebook props, drawn in a 24px square. Professional skills remain
# in the roster; these props give small portraits recognizable silhouettes.
PROPS = {
    "crown": '<path d="m3 7 5 4 4-7 4 7 5-4-3 13H6Z" fill="#EAB955"/>',
    "search": '<circle cx="10" cy="10" r="6" fill="#CDE6EB"/><path d="m15 15 6 6"/>',
    "chart": '<path d="M3 3v18h19M7 16v-4m5 4V7m5 9V4"/>',
    "shield": '<path d="m12 2 9 4v7q-1 6-9 9Q4 19 3 13V6Z" fill="#C9DDA7"/><path d="m7 11 4 4 6-7"/>',
    "book": '<path d="M12 5Q7 1 2 4v16q5-3 10 0 5-3 10 0V4q-5-3-10 1v15" fill="#F4D58C"/>',
    "code": '<rect x="2" y="3" width="20" height="16" rx="3" fill="#CDE6EB"/><path d="m8 8-3 3 3 3m8-6 3 3-3 3M8 22h8"/>',
    "leaf": '<path d="M5 20Q0 5 21 3q0 20-16 17ZM5 20 16 9" fill="#B9D499"/>',
    "heart": '<path d="M12 21 3 12C-3 3 9-1 12 6c3-7 15-3 9 6Z" fill="#EDB09A"/>',
    "bolt": '<path d="m14 2-11 12h8l-1 9L22 9h-9Z" fill="#F4D58C"/>',
    "cloud": '<path d="M5 18C-2 17 0 8 7 9 9-1 21 3 19 10c7 2 4 9-2 8Z" fill="#CDE6EB"/>',
    "cup": '<path d="M4 8h13v8q-6 9-13 0Zm13 1c9-2 8 8 0 6M8 2v3m5-3v3" fill="#F4D58C"/>',
    "palette": '<path d="M22 12C22-2 0-1 2 13c1 9 18 13 14 4-2-5 6 0 6-5Z" fill="#F4D58C"/><circle cx="7" cy="8" r="1"/><circle cx="13" cy="6" r="1"/><circle cx="18" cy="10" r="1"/>',
    "chat": '<path d="M3 3h18v14H9l-6 5Z" fill="#CDE6EB"/><path d="M7 8h10M7 12h6"/>',
    "camera": '<path d="M3 7h4l2-4h6l2 4h4v14H3Z" fill="#CDE6EB"/><circle cx="12" cy="13" r="4"/>',
    "flask": '<path d="M8 2h8M9 2v8L3 20q9 4 18 0l-6-10V2M6 15h12" fill="#C9DDA7"/>',
    "plane": '<path d="m2 10 20-8-8 20-3-9Z" fill="#CDE6EB"/><path d="m11 13 6-6"/>',
    "box": '<path d="m2 7 10-5 10 5v11l-10 5-10-5Zm0 0 10 5 10-5M12 12v11M7 4l10 6" fill="#E5C39A"/>',
    "bulb": '<path d="M8 18c0-5-5-5-5-10 0-10 18-10 18 0 0 5-5 5-5 10ZM8 22h8" fill="#F4D58C"/>',
    "coin": '<circle cx="12" cy="12" r="10" fill="#F4D58C"/><path d="M8 7h8m-8 5h8m-4-7v14"/>',
    "network": '<path d="m5 5 14 14M5 19 19 5M5 5v14h14V5Z"/><circle cx="5" cy="5" r="3" fill="#F4D58C"/><circle cx="19" cy="5" r="3" fill="#EDB09A"/><circle cx="5" cy="19" r="3" fill="#CDE6EB"/><circle cx="19" cy="19" r="3" fill="#C9DDA7"/>',
}
PROFESSIONS = (
    "crown chart shield bulb coin heart search coin box chat chart shield "
    "coin code box code heart bolt cloud bulb box heart network camera box cup palette box "
    "book palette leaf plane shield leaf plane code "
    "search shield chat book chat chat chat bulb search coin palette book"
).split()


def portrait(expert, index):
    backgrounds = ["#F8DF9D", "#D6E8E9", "#DCE7C6", "#F2D2BB", "#E6DFF0", "#E6E1C7"]
    coats = ["#557552", "#668695", "#B37755", "#82985B", "#8E7991", "#437C73"]
    spots = ["#755342", "#455B4C", "#A27651", "#596779"]
    bg, coat, spot = backgrounds[index % 6], coats[(index // 3) % 6], spots[index % 4]
    patch = ('<path d="M65 50Q63 82 84 83Q100 72 92 45Z" fill="%s"/>' % spot if index % 2
             else '<path d="M120 47Q104 56 119 78Q144 86 148 62Z" fill="%s"/>' % spot)
    glasses = '<g fill="none" stroke="#483F34" stroke-width="3"><circle cx="82" cy="96" r="13"/><circle cx="124" cy="96" r="13"/><path d="M95 96h16"/></g>' if index % 4 == 1 else ''
    hat = ('<path d="m76 48-6-22 21 9 11-20 12 20 20-9-5 23Z" fill="#E6B553" stroke="#765B38" stroke-width="3"/>' if index == 0 else
           '<path d="M68 53q0-28 35-28t35 28" fill="%s"/><path d="M65 53h80" stroke="#483F34" stroke-width="4" stroke-linecap="round"/>' % coat if index % 3 == 0 else '')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-labelledby="title">
<title id="title">{escape(expert['name'])} · {escape(expert['nickname'])}</title>
<rect width="200" height="200" rx="40" fill="{bg}"/>
<path d="M0 162Q55 135 103 159t97-4v45H0" fill="{coat}" opacity=".13"/>
<path d="M47 205v-34q0-35 56-35t56 35v34" fill="{coat}"/>
<path d="m82 141 21 21 21-21M102 163v34" fill="#FFFAEB"/>
<g stroke="#634E3E" stroke-width="3" stroke-linejoin="round">
<path d="M70 63Q45 50 55 24q7 22 27 21M134 63q26-13 17-39-7 22-27 21" fill="#EAC789"/>
<path d="M65 71Q22 52 28 81q7 25 39 16M139 71q43-19 37 10-7 25-39 16" fill="#FFFAEB"/>
<path d="M59 79Q37 67 38 82q5 12 23 9M145 79q22-12 21 3-5 12-23 9" fill="#EFB49F" stroke="none"/>
<path d="M56 88q0-43 47-43t47 43v25q0 40-47 40t-47-40Z" fill="#FFFAEB"/>
</g>{patch}{hat}
<ellipse cx="73" cy="112" rx="9" ry="5" fill="#F0BBA5"/><ellipse cx="134" cy="112" rx="9" ry="5" fill="#F0BBA5"/>
<g fill="#483F34"><ellipse cx="82" cy="96" rx="3.5" ry="5"/><ellipse cx="124" cy="96" rx="3.5" ry="5"/></g>{glasses}
<rect x="67" y="112" width="73" height="39" rx="20" fill="#F0BBA5" stroke="#634E3E" stroke-width="3"/>
<ellipse cx="87" cy="127" rx="3" ry="4" fill="#8C5D4A"/><ellipse cx="120" cy="127" rx="3" ry="4" fill="#8C5D4A"/>
<path d="M97 137q6 5 12 0" fill="none" stroke="#8C5D4A" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="157" cy="163" r="28" fill="#FFFAEB" stroke="{coat}" stroke-width="3"/>
<g transform="translate(140 146) scale(1.4)" stroke="#634E3E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none">{PROPS[PROFESSIONS[index]]}</g>
</svg>'''


def main():
    experts = json.loads((ROOT / 'branding/experts.json').read_text(encoding='utf-8'))
    assert len(experts) == len(PROFESSIONS) == 48
    assert len({e['id'] for e in experts}) == len({e['name'] for e in experts}) == 48
    serialized = json.dumps(experts, ensure_ascii=False, indent=2) + '\n'
    for target in ['frontend/public/assets/experts.json', 'backend/app/data/experts.json', 'api/app/data/experts.json']:
        (ROOT / target).write_text(serialized, encoding='utf-8')
    for i, e in enumerate(experts):
        (ASSETS / 'avatars' / f"{e['id']}.svg").write_text(portrait(e, i), encoding='utf-8')
    (ASSETS / 'avatars.json').write_text(json.dumps([
        {'id': e['id'], 'name': e['name'], 'role': e['role_title'], 'avatar_url': e['avatar']} for e in experts
    ], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Generated 48 cow portraits and synchronized 3 expert catalogs.')


if __name__ == '__main__':
    main()
