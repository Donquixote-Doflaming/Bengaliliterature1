#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builds data/content.js for the বাংলা সাহিত্য study site.

Parses the source markdown (বাংলা সাহিত্য.html.md) into a structured payload:
sections -> subsections -> blocks, plus author cards, curated readings and
the 880-question answer sheet. Internal anchors are rewritten to stable,
latinised ids.
"""
import re, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The source markdown. It ships with the repo under content/ so the site can
# be rebuilt from a fresh clone; override with argv[1] if it lives elsewhere.
SRC = os.path.join(HERE, 'content', 'বাংলা সাহিত্য.html.md')
if len(sys.argv) > 1:
    SRC = sys.argv[1]
OUT = os.path.join(HERE, 'data', 'content.js')

# ----------------------------------------------------------------------------
# Bengali -> latin transliteration (for clean, shareable URL slugs)
# ----------------------------------------------------------------------------
CONS = {
    'ক': 'k', 'খ': 'kh', 'গ': 'g', 'ঘ': 'gh', 'ঙ': 'ng',
    'চ': 'ch', 'ছ': 'chh', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'ny',
    'ট': 't', 'ঠ': 'th', 'ড': 'd', 'ঢ': 'dh', 'ণ': 'n',
    'ত': 't', 'থ': 'th', 'দ': 'd', 'ধ': 'dh', 'ন': 'n',
    'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh', 'ম': 'm',
    'য': 'y', 'র': 'r', 'ল': 'l', 'শ': 'sh', 'ষ': 'sh', 'স': 's', 'হ': 'h',
    'ড়': 'r', 'ঢ়': 'rh', 'য়': 'y', 'ৎ': 't', '৳': 'r',
}
INDEP = {'অ': 'o', 'আ': 'a', 'ই': 'i', 'ঈ': 'i', 'উ': 'u', 'ঊ': 'u',
         'ঋ': 'ri', 'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou'}
SIGN = {'া': 'a', 'ি': 'i', 'ী': 'i', 'ু': 'u', 'ূ': 'u', 'ৃ': 'ri',
        'ে': 'e', 'ো': 'o', 'ৌ': 'ou'}
NASAL = {'ঁ': 'n', 'ং': 'ng', 'ঃ': 'h', 'ঁ': 'n'}


BENG_DIGITS = {'\u09E6': '0', '\u09E7': '1', '\u09E8': '2', '\u09E9': '3',
               '\u09EA': '4', '\u09EB': '5', '\u09EC': '6', '\u09ED': '7',
               '\u09EE': '8', '\u09EF': '9'}


def roman(text):
    text = ''.join(BENG_DIGITS.get(c, c) for c in text)
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '্':                      # virama
            i += 1
            continue
        if c in CONS:
            out.append(CONS[c])
            j = i + 1
            # ে + া  ->  o
            if j < n and text[j] == 'ে' and j + 1 < n and text[j + 1] == 'া':
                out.append('o')
                i = j + 2
                continue
            if j < n and text[j] in SIGN:
                out.append(SIGN[text[j]])
                i = j + 1
                continue
            if j < n and text[j] in INDEP:    # dead consonant followed by vowel
                out.append(CONS[c])
                i = j
                continue
            out.append('a')
            i = j
            continue
        if c in INDEP:
            out.append(INDEP[c])
            i += 1
            continue
        if c in NASAL:
            out.append(NASAL[c])
            i += 1
            continue
        if c in SIGN:
            out.append(SIGN[c])
            i += 1
            continue
        if c.isdigit():
            out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    s = ''.join(out).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'x'


def uniq(base, used):
    b = base or 'x'
    out = b
    k = 2
    while out in used:
        out = '%s-%d' % (b, k)
        k += 1
    used.add(out)
    return out


# ----------------------------------------------------------------------------
# inline markdown -> html
# ----------------------------------------------------------------------------

def match_bracket(text, i):
    depth = 0
    for j in range(i, len(text)):
        if text[j] == '[':
            depth += 1
        elif text[j] == ']':
            depth -= 1
            if depth == 0:
                return j
    return -1


def _link_at(text, i):
    if text[i] != '[':
        return None
    end = match_bracket(text, i)
    if end == -1 or text[end + 1:end + 2] != '(':
        return None
    k = text.find(')', end + 2)
    if k == -1:
        return None
    return text[i + 1:end], text[end + 2:k], k + 1


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline_html(text, resolver=None):
    out = []
    buf = []

    def flush():
        if buf:
            out.append(esc(''.join(buf)))
            del buf[:]

    i, n = 0, len(text)
    while i < n:
        if text.startswith('**', i):
            j = text.find('**', i + 2)
            if j != -1:
                flush()
                out.append('<strong>' + inline_html(text[i + 2:j], resolver) + '</strong>')
                i = j + 2
                continue
        if text[i] == '[':
            got = _link_at(text, i)
            if got:
                label, href, end = got
                flush()
                lab = inline_html(label, resolver)
                target = resolver(lab, href) if resolver else None
                out.append('<a href="%s"%s>%s</a>'
                           % (esc(target or href),
                              ' class="ext"' if href.startswith('http') else '',
                              lab))
                i = end
                continue
        buf.append(text[i])
        i += 1
    flush()
    return ''.join(out)


def plain(text):
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    return t.replace('**', '').strip()


# ----------------------------------------------------------------------------
# block parsing
# ----------------------------------------------------------------------------

RE_LINK = re.compile(r'\[([^\]]*)\]\(([^)]*)\)')
RE_H = re.compile(r'^(#{1,6})\s+(.*)$')
RE_OL = re.compile(r'^(\d+)\.\s+(.*)$')
RE_SEP_ROW = re.compile(r'^:?-{2,}:?$')


def split_parts(line):
    parts, buf, i, n = [], [], 0, len(line)
    while i < n:
        if line[i] == '[':
            got = _link_at(line, i)
            if got:
                label, href, end = got
                if buf:
                    parts.append({'t': 'text', 'v': ''.join(buf)})
                    buf = []
                parts.append({'t': 'link', 'label': label, 'href': href})
                i = end
                continue
        buf.append(line[i])
        i += 1
    if buf:
        parts.append({'t': 'text', 'v': ''.join(buf)})
    return parts


def is_link_row(line):
    parts = split_parts(line)
    if not any(p['t'] == 'link' for p in parts):
        return False
    for p in parts:
        if p['t'] == 'text' and p['v'].strip(' \t·,–—-'):
            return False
    return True


def parse_blocks(lines):
    blocks = []
    i, n = 0, len(lines)
    para = []

    def flush_para():
        if para:
            blocks.append({'t': 'p', 'text': ' '.join(para)})
            del para[:]

    while i < n:
        s = lines[i].strip()

        if not s:
            flush_para(); i += 1; continue

        m = RE_H.match(s)
        if m:
            flush_para()
            blocks.append({'t': 'h', 'level': len(m.group(1)), 'text': m.group(2).strip()})
            i += 1
            continue

        if s.startswith('|'):
            flush_para()
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            header, body = None, rows
            if len(rows) >= 2 and all(RE_SEP_ROW.match(c) for c in rows[1] if c):
                header, body = rows[0], rows[2:]
            blocks.append({'t': 'table', 'header': header, 'rows': body})
            continue

        if re.match(r'^:\s+\S', s):
            flush_para()
            items, term = [], None
            while i < n:
                ss = lines[i].strip()
                if not ss:
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and re.match(r'^:\s+\S', lines[j].strip()):
                        i = j
                        continue
                    break
                if re.match(r'^:\s+\S', ss):
                    items.append({'term': term or '', 'desc': re.sub(r'^:\s*', '', ss)})
                    term = None; i += 1; continue
                if RE_H.match(ss) or ss.startswith('| ') or ss.startswith('* '):
                    break
                if term is not None:
                    items.append({'term': term, 'desc': ''})
                term = ss; i += 1
            if term is not None:
                items.append({'term': term, 'desc': ''})
            if items:
                blocks.append({'t': 'dl', 'items': items})
            continue

        if RE_OL.match(s):
            flush_para()
            items = []
            prev_no = None
            while i < n:
                # a blank line between items does not end the list
                if not lines[i].strip():
                    j = i
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n:
                        m2 = RE_OL.match(lines[j].strip())
                        if m2 and (prev_no is None or int(m2.group(1)) == prev_no + 1):
                            i = j
                            continue
                    break
                ss = lines[i].strip()
                mm = RE_OL.match(ss)
                if not mm:
                    break
                prev_no = int(mm.group(1))
                txt = mm.group(2)
                i += 1
                cont = []
                while i < n:
                    l2 = lines[i]
                    if not l2.strip():
                        j = i
                        while j < n and not lines[j].strip():
                            j += 1
                        if j < n:
                            ind = len(lines[j]) - len(lines[j].lstrip())
                            s2 = lines[j].strip()
                            if (ind > 0 and not RE_OL.match(s2)
                                    and not s2.startswith(('* ', '- ', '+ ', '| '))
                                    and not RE_H.match(s2)):
                                i = j
                                continue
                        break
                    ind = len(l2) - len(l2.lstrip())
                    s2 = l2.strip()
                    if ind == 0:
                        break
                    if (RE_OL.match(s2) or s2.startswith(('* ', '- ', '+ ', '| '))
                            or RE_H.match(s2)):
                        break
                    cont.append(s2)
                    i += 1
                items.append({'text': txt, 'cont': cont})
            blocks.append({'t': 'ol', 'items': items})
            continue

        if s.startswith('* ') or s.startswith('- '):
            flush_para()
            items = []
            while i < n:
                l2 = lines[i]
                ss = l2.strip()
                if not (ss.startswith('* ') or ss.startswith('- ')):
                    break
                indent = len(l2) - len(l2.lstrip())
                txt = ss[2:]
                i += 1
                cont = []
                while i < n:
                    l3 = lines[i]
                    if not l3.strip():
                        break
                    ind3 = len(l3) - len(l3.lstrip())
                    ss3 = l3.strip()
                    if ss3.startswith(('* ', '- ', '+ ')):
                        break
                    if ind3 <= indent:
                        break
                    if RE_OL.match(ss3) or ss3.startswith('| ') or RE_H.match(ss3):
                        break
                    cont.append(ss3)
                    i += 1
                items.append({'text': txt, 'cont': cont})
            blocks.append({'t': 'ul', 'items': items})
            continue

        if s.startswith('+ '):
            flush_para()
            items = []
            while i < n:
                ss = lines[i].strip()
                if not ss.startswith('+ '):
                    break
                items.append({'text': ss[2:]})
                i += 1
            blocks.append({'t': 'ul2', 'items': items})
            continue

        if is_link_row(s):
            flush_para()
            links = [p for p in split_parts(s) if p['t'] == 'link']
            blocks.append({'t': 'chips',
                           'items': [{'label': p['label'], 'href': p['href']} for p in links]})
            i += 1
            continue

        if re.fullmatch(r'\(.*\)', s) and len(s) < 140:
            flush_para()
            blocks.append({'t': 'kicker', 'text': s[1:-1].strip()})
            i += 1
            continue

        para.append(s)
        i += 1

    flush_para()
    return blocks


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

SEC_IDS = [
    ('তিন যুগ এক নজরে', 'intro', 'সূচনা'),
    ('প্রাচীন যুগ', 'anc', 'প্রাচীন যুগ'),
    ('মধ্যযুগ', 'med', 'মধ্যযুগ'),
    ('আধুনিক যুগ', 'mod', 'আধুনিক যুগ'),
    ('রবীন্দ্র-পরবর্তী কবি ও সাহিত্যিক', 'post-rab', 'রবীন্দ্র-পরবর্তী'),
    ('কথাসাহিত্যিক', 'katha', 'কথাসাহিত্যিক'),
    ('পূর্ব বাংলা ও বাংলাদেশের লেখক', 'bd', 'বাংলাদেশের লেখক'),
    ('লেখক ও কবি', 'writers', 'লেখক ও কবি'),
    ('প্রাচীন যুগ', 'writers-anc', 'লেখক · প্রাচীন'),
    ('মধ্যযুগ', 'writers-med', 'লেখক · মধ্যযুগ'),
    ('আধুনিক যুগ · জন্মসালের ক্রমে', 'writers-mod', 'লেখক · আধুনিক'),
    ('অনুশীলনী ও প্রশ্ন', 'questions', 'অনুশীলনী'),
]

BIRTH_RANGES = ['১৭০০–১৭৯৯', '১৮০০–১৮৫৯', '১৮৬০–১৮৯৯', '১৯০০–১৯২৯', '১৯৩০ ও পরবর্তী']

CARD_SEC = {'writers-anc': 'প্রাচীন যুগ', 'writers-med': 'মধ্যযুগ',
            'writers-mod': 'আধুনিক যুগ'}


def main():
    raw = open(SRC, encoding='utf-8').read()
    lines = raw.split('\n')

    start = next(i for i, l in enumerate(lines) if l.strip().startswith('# '))
    end = next((i for i in range(len(lines) - 1, -1, -1)
                if 'সর্বস্বত্ব সংরক্ষিত' in lines[i]), len(lines))
    body = lines[start:end]

    # ---- heading tree ----------------------------------------------------
    heads = []
    for i, ln in enumerate(body):
        m = RE_H.match(ln.strip())
        if m:
            heads.append({'level': len(m.group(1)), 'title': m.group(2).strip(),
                          'start': i, 'children': []})
    for k, h in enumerate(heads):
        h['end'] = heads[k + 1]['start'] if k + 1 < len(heads) else len(body)

    roots, stack = [], []
    for h in heads:
        while stack and stack[-1]['level'] >= h['level']:
            stack.pop()
        if stack:
            stack[-1]['children'].append(h)
        else:
            roots.append(h)
        stack.append(h)

    for h in heads:
        stop = h['children'][0]['start'] if h['children'] else h['end']
        h['blocks'] = parse_blocks(body[h['start'] + 1:stop])

    h1 = roots[0]
    m = re.match(r'^(.*?সাহিত্য)\s*(তিন যুগ ধরে.*)$', h1['title'])
    site_title = m.group(1) if m else h1['title']
    site_tagline = m.group(2) if m else ''

    # ---- stable latin ids for every heading -------------------------------
    used_ids = set()
    for h in heads:
        h['sid'] = uniq(roman(h['title']), used_ids)

    # ---- sections --------------------------------------------------------
    sections = []
    for h2 in h1['children']:
        if h2['level'] != 2:
            continue
        sections.append({'id': '', 'title': h2['title'], 'label': '',
                         'blocks': h2['blocks'], 'subs': h2['children'], 'node': h2})

    title_counts = {}
    for sec in sections:
        title_counts[sec['title']] = title_counts.get(sec['title'], 0) + 1
        occ = title_counts[sec['title']]
        base = None
        for title, sid, label in SEC_IDS:
            if title != sec['title']:
                continue
            cand = [x for x in SEC_IDS if x[0] == title]
            base = cand[occ - 1][1] if occ <= len(cand) else cand[-1][1]
            break
        if base is None:
            base = roman(sec['title'])
        sec['id'] = uniq(base, used_ids)
        for title, s_id, label in SEC_IDS:
            if s_id == base:
                sec['label'] = label
        sec.setdefault('label', sec['title'])

    # ---- author cards ----------------------------------------------------
    authors = []
    seen_norm = {}
    for sec in sections:
        if sec['id'] not in CARD_SEC:
            continue
        era = CARD_SEC[sec['id']]
        for sub in sec['subs']:
            if sub['level'] != 3:
                continue
            if sub['title'] in ('আধুনিক যুগ', 'প্রাচীন যুগ', 'মধ্যযুগ') or \
               sub['title'].startswith('লেখক-সংশ্লিষ্ট'):
                continue
            key = re.sub(r'\s+', '', sub['title'])
            if key in seen_norm:
                continue
            seen_norm[key] = True
            bl = sub['blocks']
            tagline = bl[0]['text'] if bl and bl[0]['t'] == 'p' else ''
            authors.append({
                'id': 'a-' + sub['sid'],
                'name': sub['title'].replace('★', '').strip(),
                'era': era,
                'tagline': tagline,
                'blocks': bl[1:],
                'sid': sub['sid'],
            })

    # ---- curated readings ------------------------------------------------
    readings = []
    for sec in sections:
        if sec['id'] != 'bd':
            continue
        for sub in sec['subs']:
            if 'লেখক অনুযায়ী সম্পাদিত পাঠ' not in sub['title']:
                continue
            for card in sub['children']:
                if card['level'] != 4:
                    continue
                bl = card['blocks']
                tagline = bl[0]['text'] if bl and bl[0]['t'] == 'p' else ''
                readings.append({'title': card['title'], 'tagline': tagline,
                                 'blocks': bl[1:], 'sid': card['sid']})

    # ---- quiz ------------------------------------------------------------
    quiz = []
    for sec in sections:
        if sec['id'] != 'questions':
            continue
        for blk in sec['blocks']:
            if blk['t'] != 'ol':
                continue
            for it in blk['items']:
                q = it['text'].replace('**', '').strip()
                a = ' '.join(it.get('cont', [])).strip()
                a = re.sub(r'^\*\*উত্তর:\*\*\s*', '', a)
                a = a.replace('**', '').strip()
                if q:
                    quiz.append({'q': q, 'a': a})

    # ---- link resolution -------------------------------------------------
    def norm(s):
        return re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', s)).replace('★', '').strip()

    # ---- first pass: map anchor numbers -> author names -------------------
    FAM_RE = re.compile(r'^#(?:(original-scan|era|writer-new|literary-profile)-)?author-(\d+)$')

    def walk_blocks(blocks):
        for b in blocks:
            yield b
            if b['t'] == 'chips':
                for it in b['items']:
                    yield {'t': 'chip', 'label': it['label'], 'href': it['href']}

    num_to_norm = {}
    for h in heads:
        for b in walk_blocks(h['blocks']):
            if b['t'] != 'chip':
                continue
            m = FAM_RE.match(b['href'])
            if not m:
                continue
            fam = m.group(1) or 'author'
            key = (fam, m.group(2))
            lbl = b['label']
            lbl = re.sub(r'^[\u09E6-\u09EF0-9\s]*[·\u00B7]\s*', '', lbl)   # "1820 · "
            lbl = norm(lbl)
            if lbl:
                num_to_norm.setdefault(key, [])
                if lbl not in num_to_norm[key]:
                    num_to_norm[key].append(lbl)

    author_by_norm = {}
    for a in authors:
        author_by_norm.setdefault(norm(a['name']), a['id'])
    author_by_norm.setdefault(norm('দক্ষিণারঞ্জন মিত্র মজুমদার'),
                              author_by_norm.get(norm('দক্ষিণারঞ্জন মিত্রমজুমদার')))

    title_to_sid = {}
    for h in heads:
        title_to_sid.setdefault(norm(h['title']), h['sid'])
    sec_by_id = {s['id']: s for s in sections}

    # heading title -> section id (so "প্রাচীন যুগ" links to the prose section)
    SPECIAL = {
        '#anc': 'anc', '#med': 'med', '#mod': 'mod',
        '#writers': 'writers', '#questions': 'questions', '#top': None,
        '#modern-chronology': 'writers-mod', '#modern-themes': 'mod',
        '#ekushey-literature': 'bd', '#magazine-tables': 'mod',
        '#gitika-kabiyal': 'med',
    }
    for k, br in enumerate(BIRTH_RANGES):
        SPECIAL['#birthrange-%d' % k] = br

    num_to_author = {}
    for key, labels in num_to_norm.items():
        for lbl in labels:
            if lbl in author_by_norm:
                num_to_author[key] = author_by_norm[lbl]
                break

    def resolve(lab_html, href):
        if not href.startswith('#'):
            return None
        m = FAM_RE.match(href)
        if m:
            fam = m.group(1) or 'author'
            aid = num_to_author.get((fam, m.group(2)))
            if aid:
                return '#' + aid
        if href in SPECIAL:
            val = SPECIAL[href]
            if val is None:
                return '#'
            if val in sec_by_id:
                return '#' + val
            sid = title_to_sid.get(norm(val))
            return ('#' + sid) if sid else None
        if href.startswith('#a/') or href.startswith('#author-') or \
           href.startswith('#original-scan-author-') or href.startswith('#era-writer-') or \
           href.startswith('#writer-new-') or href.startswith('#literary-profile-'):
            key = norm(lab_html)
            if key in author_by_norm:
                return '#' + author_by_norm[key]
        key = norm(lab_html)
        if key in author_by_norm:
            return '#' + author_by_norm[key]
        if key in title_to_sid:
            return '#' + title_to_sid[key]
        return None

    # ---- rendering -------------------------------------------------------
    def render_blocks(blocks, qa=False):
        out = []
        for b in blocks:
            t = b['t']
            if t == 'p':
                out.append({'h': '<p>' + inline_html(b['text'], resolve) + '</p>',
                            'x': plain(b['text'])})
            elif t == 'kicker':
                out.append({'h': '<p class="kicker">' + esc(b['text']) + '</p>',
                            'x': b['text']})
            elif t == 'h':
                out.append({'h': '<h%d>%s</h%d>' % (b['level'], esc(b['text']), b['level']),
                            'x': b['text']})
            elif t == 'ul':
                items = ''.join(
                    '<li>' + inline_html(it['text'], resolve) +
                    (('<span class="cont">' + ' '.join(inline_html(c, resolve)
                                                        for c in it['cont']) + '</span>')
                     if it.get('cont') else '') + '</li>'
                    for it in b['items'])
                out.append({'h': '<ul>' + items + '</ul>',
                            'x': ' '.join(plain(i['text']) for i in b['items'])})
            elif t == 'ul2':
                items = ''.join('<li>' + inline_html(it['text'], resolve) + '</li>'
                                for it in b['items'])
                out.append({'h': '<ul class="sub">' + items + '</ul>',
                            'x': ' '.join(plain(i['text']) for i in b['items'])})
            elif t == 'ol':
                items = []
                for it in b['items']:
                    extra = ''
                    if it.get('cont'):
                        extra = ''.join('<span class="ans">' + inline_html(c, resolve) + '</span>'
                                        for c in it['cont'])
                    items.append('<li>' + inline_html(it['text'], resolve) + extra + '</li>')
                out.append({'h': '<ol' + (' class="qa"' if qa else '') + '>' + ''.join(items) + '</ol>',
                            'x': ' '.join(plain(i['text']) for i in b['items'])})
            elif t == 'dl':
                items = []
                for it in b['items']:
                    d = ('<dd>' + inline_html(it['desc'], resolve) + '</dd>') if it['desc'] else ''
                    items.append('<dt>' + inline_html(it['term'], resolve) + '</dt>' + d)
                out.append({'h': '<dl>' + ''.join(items) + '</dl>',
                            'x': ' '.join(plain(i['term']) + ' ' + plain(i['desc'])
                                          for i in b['items'])})
            elif t == 'table':
                head = ''
                if b['header']:
                    head = ('<thead><tr>' + ''.join(
                        '<th>' + inline_html(c, resolve) + '</th>' for c in b['header'])
                        + '</tr></thead>')
                rows = ''.join('<tr>' + ''.join('<td>' + inline_html(c, resolve) + '</td>'
                                                for c in r) + '</tr>' for r in b['rows'])
                out.append({'h': '<div class="tw"><table>' + head + '<tbody>' + rows +
                                 '</tbody></table></div>',
                            'x': ' '.join(' '.join(plain(c) for c in r) for r in b['rows'])})
            elif t == 'chips':
                items = ''.join(
                    '<a class="chip" href="%s">%s</a>'
                    % (esc(resolve(inline_html(it['label'], resolve), it['href']) or it['href']),
                       inline_html(it['label'], resolve))
                    for it in b['items'])
                out.append({'h': '<div class="chips">' + items + '</div>',
                            'x': ' '.join(plain(i['label']) for i in b['items'])})
            else:
                out.append({'h': '', 'x': ''})
        return out

    def render_node(node, level):
        nid = node['sid']
        if 'লেখক অনুযায়ী সম্পাদিত পাঠ' in node['title']:
            nid = 'readings'
        elif node['title'] == 'লেখক-সংশ্লিষ্ট সারণি ও প্রশ্নোত্তর':
            nid = 'tables'
        elif node['title'] == 'আধুনিক যুগ' and 'যুগ · জন্মসালের' in sections[-1]['title']:
            nid = 'writers-modern'
        elif node['title'] == 'মুক্তিযুদ্ধভিত্তিক সাহিত্য ও চলচ্চিত্র':
            nid = 'ekushey'
        elif node['title'] == 'গীতিকা, কবিয়াল ও পুঁথি':
            nid = 'gitika'
        elif node['title'] == 'পত্র-পত্রিকা':
            nid = 'magazines'
        else:
            aid = author_by_norm.get(norm(node['title']))
            if aid:
                nid = aid
        o = {'id': nid, 'title': node['title'], 'level': node['level'],
             'html': [], 'subs': []}
        rb = render_blocks(node['blocks'])
        o['html'] = [b['h'] for b in rb]
        for c in node['children']:
            o['subs'].append(render_node(c, level + 1))
        return o

    out_sections = []
    for sec in sections:
        o = {'id': sec['id'], 'title': sec['title'], 'label': sec['label'],
             'html': [], 'subs': []}
        lead = render_blocks(sec['blocks'], qa=(sec['id'] == 'questions'))
        o['html'] = [b['h'] for b in lead]
        for sub in sec['subs']:
            o['subs'].append(render_node(sub, 4))
        out_sections.append(o)

    authors_out = []
    for a in authors:
        rb = render_blocks(a['blocks'])
        authors_out.append({
            'id': a['id'], 'name': a['name'], 'era': a['era'],
            'tagline': plain(a['tagline']),
            'html': [b['h'] for b in rb],
        })

    readings_out = []
    for r in readings:
        rb = render_blocks(r['blocks'])
        readings_out.append({
            'id': 'r-' + r['sid'], 'title': r['title'],
            'tagline': plain(r['tagline']),
            'html': [b['h'] for b in rb],
        })

    eras = [
        {'id': 'anc', 'name': 'প্রাচীন যুগ', 'range': '৬৫০ – ১২০০',
         'topic': 'ধর্ম (বৌদ্ধ)', 'key': 'চর্যাপদ'},
        {'id': 'med', 'name': 'মধ্যযুগ', 'range': '১২০১ – ১৮০০',
         'topic': 'দেবদেবী', 'key': 'মঙ্গলকাব্য · বৈষ্ণব পদাবলি'},
        {'id': 'mod', 'name': 'আধুনিক যুগ', 'range': '১৮০১ – আজ',
         'topic': 'মানুষ', 'key': 'উপন্যাস · নাটক · প্রবন্ধ · কবিতা'},
    ]

    by_era = {'প্রাচীন যুগ': [], 'মধ্যযুগ': [], 'আধুনিক যুগ': []}
    for a in authors_out:
        by_era.setdefault(a['era'], []).append(a['id'])

    nav = [{'id': s['id'], 'label': s['label'], 'title': s['title'], 'subs': len(s['subs'])}
           for s in out_sections]

    site = {
        'meta': {
            'title': site_title,
            'tagline': site_tagline,
            'standfirst': 'এটা শুধু নোট নয়। চর্যাপদ থেকে মুক্তিযুদ্ধ পর্যন্ত, '
                           'তিন যুগের গল্প এক পাতায়, সহজ করে সাজানো।',
            'range': '৬৫০ – আজ',
            'no': '112026',
            'copyright': 'Copyright © 2026. All rights reserved. সর্বস্বত্ব সংরক্ষিত',
        },
        'eras': eras,
        'names': [{'id': a['id'], 'name': a['name'], 'era': a['era']} for a in authors_out],
        'stats': {
            'sections': len(out_sections),
            'authors': len(authors_out),
            'questions': len(quiz),
            'eras': len(eras),
            'readings': len(readings_out),
        },
    }

    read = {
        'sections': out_sections,
        'authors': authors_out,
        'readings': readings_out,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    def dump(path, var, obj):
        with open(path, 'w', encoding='utf-8') as f:
            f.write('window.%s = ' % var)
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
            f.write(';\n')
        return os.path.getsize(path)

    d = os.path.dirname(OUT)
    a = dump(os.path.join(d, 'site.js'), 'SITE', site)
    b = dump(os.path.join(d, 'read.js'), 'READ', read)
    c = dump(os.path.join(d, 'quiz.js'), 'QUIZ', quiz)

    print('sections=%d authors=%d readings=%d quiz=%d' %
          (len(out_sections), len(authors_out), len(readings_out), len(quiz)))
    print('  site.js %d KB | read.js %d KB | quiz.js %d KB' % (a // 1024, b // 1024, c // 1024))


if __name__ == '__main__':
    main()
