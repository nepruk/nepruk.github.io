#!/usr/bin/env python3
"""Build the static pages of nepruk.com from _src/index.template.html.

Run from the repo root:   python3 _src/build.py

Source of truth = _src/index.template.html (English text + data-es / data-ru
translations next to each text). The script writes:
  index.html          English  (/)
  es/index.html       Spanish  (/es/)
  sitemap.xml, robots.txt
Folders starting with "_" are NOT published by GitHub Pages (Jekyll), so this
file and the template stay out of the site.

To enable Russian later: set "enabled": True for "ru" below (and add the
strings), then rebuild. A page /ru/ + switcher link will be generated.
"""
import json, re, datetime, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://nepruk.com"

SOCIAL = [
    "https://open.spotify.com/artist/3IpsO4tlNUpLPzbOs1FY8d",
    "https://music.apple.com/us/artist/nepruk/1460472911",
    "https://www.deezer.com/artist/64061472",
    "https://music.yandex.ru/artist/7277469",
    "https://youtube.com/@katerina_nepruk",
    "https://www.instagram.com/katerina_nepruk",
    "https://vk.com/nepruk",
]

LANGS = {
    "en": dict(
        enabled=True, path="/", out="index.html", label="EN", html_lang="en", locale="en_US",
        title="NepruK (Katerina Nepruk) — Live Electronic Artist, Central Asia",
        desc="NepruK (Katerina Nepruk), live electronic artist from Central Asia: bass guitar, bowed textures, electronics, ethnic sounds. Sounds of Uzbekistan. Booking 2027.",
        ogt="NepruK — Live Electronic Artist from Central Asia",
        ogd="Live electronic music blending bass guitar, bowed textures and ethnic influences. Booking 2027.",
        img="og-share.jpg",
        imgalt="NepruK, live electronic artist from Central Asia, sitting on the floor playing a bass guitar with a bow",
        ld_desc="Live electronic artist from Central Asia blending bass guitar, bowed textures, electronics and ethnic influences. Creator of the audiovisual project Sounds of Uzbekistan.",
    ),
    "es": dict(
        enabled=True, path="/es/", out="es/index.html", label="ES", html_lang="es", locale="es_ES",
        title="NepruK (Katerina Nepruk) — Artista electrónica, Asia Central",
        desc="NepruK (Katerina Nepruk), artista electrónica en vivo de Asia Central: bajo eléctrico, texturas de arco, electrónica y sonidos étnicos. Contratación 2027.",
        ogt="NepruK — Artista electrónica en vivo de Asia Central",
        ogd="Música electrónica en vivo que fusiona bajo eléctrico, texturas de arco e influencias étnicas. Contratación 2027.",
        img="og-share-es.jpg",
        imgalt="NepruK, artista electrónica en vivo de Asia Central, sentada en el suelo tocando el bajo con arco",
        ld_desc="Artista electrónica en vivo de Asia Central que fusiona bajo eléctrico, texturas de arco, electrónica e influencias étnicas. Creadora del proyecto audiovisual Sounds of Uzbekistan.",
    ),
    # Russian is translated in the template (data-ru) but not published yet.
    "ru": dict(
        enabled=False, path="/ru/", out="ru/index.html", label="RU", html_lang="ru", locale="ru_RU",
        title="NepruK (Katerina Nepruk) — электронная live-артистка, Центральная Азия",
        desc="NepruK (Katerina Nepruk), живая электронная артистка из Центральной Азии: бас-гитара, смычковые текстуры, электроника, этнические влияния. Sounds of Uzbekistan. Букинг 2027.",
        ogt="NepruK — электронная live-артистка из Центральной Азии",
        ogd="Живая электронная музыка, объединяющая бас-гитару, смычковые текстуры и этнические влияния. Букинг 2027.",
        img="og-share.jpg",
        imgalt="NepruK сидит на полу и играет на бас-гитаре смычком",
        ld_desc="Живая электронная артистка из Центральной Азии: бас-гитара, смычковые текстуры, электроника и этнические влияния. Создательница аудиовизуального проекта Sounds of Uzbekistan.",
    ),
}
ENABLED = [k for k, v in LANGS.items() if v["enabled"]]

TAG = re.compile(r'<([a-zA-Z][\w-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>')
ATTR = re.compile(r'([\w:-]+)(?:="([^"]*)")?')
RAW = re.compile(r'(<script\b.*?</script>|<style\b.*?</style>)', re.S)


def rebuild_tag(name, attrs_s, lang):
    attrs = [(m.group(1), m.group(2)) for m in ATTR.finditer(attrs_s) if m.group(1)]
    d = dict((k, v) for k, v in attrs)
    inner = d.get("data-" + lang) if lang != "en" else None
    out = []
    for k, v in attrs:
        if re.match(r"data-(es|ru)(-|$)", k):
            continue
        if lang != "en" and k in ("alt", "title", "aria-label"):
            t = d.get("data-%s-%s" % (lang, k))
            if t is not None:
                v = t
        out.append(k if v is None else '%s="%s"' % (k, v))
    selfclose = attrs_s.rstrip().endswith("/")
    return "<%s%s%s>" % (name, (" " + " ".join(out)) if out else "", " /" if selfclose else ""), inner


def localize_fragment(html, lang):
    res, pos = [], 0
    while True:
        m = TAG.search(html, pos)
        if not m:
            res.append(html[pos:])
            break
        res.append(html[pos:m.start()])
        name = m.group(1)
        new_open, inner = rebuild_tag(name, m.group(2), lang)
        if inner is not None:
            close = html.index("</%s>" % name, m.end())
            res.append(new_open + inner + "</%s>" % name)
            pos = close + len("</%s>" % name)
        else:
            res.append(new_open)
            pos = m.end()
    return "".join(res)


def localize(html, lang):
    parts = RAW.split(html)
    return "".join(p if i % 2 else localize_fragment(p, lang) for i, p in enumerate(parts))


def lang_links(current):
    items = []
    for k in ENABLED:
        v = LANGS[k]
        cur = ' aria-current="true"' if k == current else ""
        items.append('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>' % (v["path"], k, k, cur, v["label"]))
    return '<i aria-hidden="true"></i>'.join(items)


def hreflangs():
    out = ['<link rel="alternate" hreflang="%s" href="%s%s">' % (k, SITE, LANGS[k]["path"]) for k in ENABLED]
    out.append('<link rel="alternate" hreflang="x-default" href="%s/">' % SITE)
    return "\n".join(out)


def jsonld(lang):
    v = LANGS[lang]
    url = SITE + v["path"]
    img = "%s/assets/%s" % (SITE, v["img"])
    group_id = SITE + "/#artist"
    graph = [
        {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "NepruK",
         "inLanguage": [LANGS[k]["html_lang"] for k in ENABLED], "publisher": {"@id": group_id}},
        {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": v["title"], "description": v["desc"],
         "inLanguage": v["html_lang"], "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": group_id},
         "primaryImageOfPage": {"@type": "ImageObject", "url": img, "width": 1200, "height": 630}},
        {"@type": "MusicGroup", "@id": group_id, "name": "NepruK",
         "alternateName": ["Katerina NepruK", "Katerina Nepruk", "Nepruk"],
         "url": SITE + "/", "image": img, "description": v["ld_desc"],
         "genre": ["Electronic", "Ethno", "Downtempo", "Electronica"],
         "sameAs": SOCIAL,
         "contactPoint": {"@type": "ContactPoint", "contactType": "booking", "email": "nepruk.booking@gmail.com",
                          "availableLanguage": ["English", "Spanish", "Russian"]},
         "album": [{"@type": "MusicAlbum", "name": "Sounds of Uzbekistan: Margilan - EP",
                    "url": "https://music.apple.com/us/album/sounds-of-uzbekistan-margilan-ep/1884335824",
                    "byArtist": {"@id": group_id}}],
         "track": [
             {"@type": "MusicRecording", "name": "Techno Mahalla", "url": "https://band.link/syTeT", "byArtist": {"@id": group_id}},
             {"@type": "MusicRecording", "name": "Call of the Universe", "url": "https://go.protonradio.com/r/rl3PMkz3DgzDI", "byArtist": {"@id": group_id}},
             {"@type": "MusicRecording", "name": "Tashkent Vibe", "url": "https://band.link/smyN0", "byArtist": {"@id": group_id}},
             {"@type": "MusicRecording", "name": "Kari-Navo", "url": "https://go.protonradio.com/r/rlcgv8zHjEOsQ", "byArtist": {"@id": group_id}},
         ]},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def render(template, lang):
    v = LANGS[lang]
    html = localize(template, lang)
    url = SITE + v["path"]
    alt = [LANGS[k]["locale"] for k in ENABLED if k != lang] or [v["locale"]]
    tokens = {
        "LANG": v["html_lang"], "TITLE": v["title"], "DESC": v["desc"], "OGT": v["ogt"], "OGD": v["ogd"],
        "URL": url, "IMG": "%s/assets/%s" % (SITE, v["img"]), "IMGALT": v["imgalt"], "LOCALE": v["locale"],
        "LOCALE_ALT": alt[0], "HREFLANG": hreflangs(), "JSONLD": jsonld(lang), "LANGLINKS": lang_links(lang),
    }
    for k, val in tokens.items():
        html = html.replace("{{%s}}" % k, val)
    assert "{{" not in html, re.findall(r"\{\{\w+\}\}", html)
    return html


def main():
    template = open(os.path.join(ROOT, "_src", "index.template.html"), encoding="utf-8").read()
    today = datetime.date.today().isoformat()
    for k in ENABLED:
        out = os.path.join(ROOT, LANGS[k]["out"])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(render(template, k))
        print("wrote", LANGS[k]["out"])
    # sitemap with hreflang alternates
    urls = []
    for k in ENABLED:
        alts = "".join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>' % (a, SITE, LANGS[a]["path"]) for a in ENABLED)
        alts += '\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s/"/>' % SITE
        urls.append("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>%s</priority>%s\n  </url>"
                    % (SITE, LANGS[k]["path"], today, "1.0" if k == "en" else "0.9", alts))
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s\n</urlset>\n' % "\n".join(urls))
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)
    print("wrote sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
