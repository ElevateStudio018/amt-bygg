#!/usr/bin/env python3
"""Bygger AMT Byggs webbplats till statisk HTML.

    python3 src/build.py              # skriver sidorna till repots rot (rena URL:er: /om-oss/)
    python3 src/build.py --explicit   # länkar till .../index.html (för förhandsvisning via file://)

Sidinnehåll ligger i src/pages/*.html. Varje fil börjar med en metadata-kommentar:
    <!--meta {"title": "...", "description": "...", "path": "om-oss/", "nav": "om-oss"} -->
Följande taggar kan användas i sidorna:
    {{pic namn|alt|sizes|klass|eager}}   responsiv bild från assets/img
    {{> partial arg}}                    gemensamma block, se PARTIALS
    {{url sida/}}                        relativ länk till en annan sida
    {{asset sökväg}}                     relativ länk till en fil i assets/
"""
import json
import os
import posixpath
import re
import sys
from datetime import date
from html import escape

# Elevate Studio's credit under every footer: the mark and the name, the whole of it one link to elevatestudio.nu.
ELEVATE_CREDIT = '''<!-- elevate-credit -->
<style>.elevate-credit{max-width:1240px;margin:24px auto 0;padding:20px 16px 0;border-top:1px solid rgba(128,128,128,.25);display:flex;justify-content:center;box-sizing:border-box}.elevate-credit a{display:inline-flex;align-items:center;gap:10px;padding:8px 0;font:inherit;font-size:15px;line-height:1;color:inherit;opacity:.55;text-decoration:none;transition:opacity .2s}.elevate-credit a:hover,.elevate-credit a:focus-visible{opacity:1}.elevate-credit svg{width:20px;height:20px;flex:none;display:block}@media(min-width:1024px){.elevate-credit a{font-size:16px}}</style>
<div class="elevate-credit"><a href="https://elevatestudio.nu" target="_blank" rel="noopener"><svg viewBox="0 0 1884.3 1353.9" aria-hidden="true"><path d="M0.0 1353.9 L1218.7 0.0 L1218.7 329.1 L479.7 1136.4 L786.7 1132.4 L1215.5 687.4 L1884.3 1349.9 L1590.1 1349.9 L1218.6 994.7 L865.4 1349.9Z" fill="currentColor"/></svg>Byggd av Elevate Studio</a></div>
'''


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
EXPLICIT = '--explicit' in sys.argv
SITE_URL = 'https://www.amtgroup.se'

# Sätt till en URL (t.ex. https://formspree.io/f/xxxx) för att skicka formulär via en tjänst.
# Tom sträng = formulären öppnar ett förifyllt mejl.
FORM_ENDPOINT_CONTACT = ''
FORM_ENDPOINT_DAMAGE = ''

COMPANY = {
    'name': 'AMT Bygg',
    'legal': 'AMT Byggentreprenad AB',
    'orgnr': '559212-4555',
    'phone': '031-45 40 45',
    'phone_href': '+4631454045',
    'email': 'amtbygg@amtgroup.se',
    'invoice_email': 'faktura@amtgroup.se',
    'street': 'Marieholmsgatan 54',
    'zip': '415 02',
    'city': 'Göteborg',
    'region': 'Västra Götalands län',
    'maps': 'https://www.google.com/maps/search/?api=1&query=Marieholmsgatan+54,+415+02+G%C3%B6teborg',
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
AREAS = [
    {
        'slug': 'affarsomraden/skadereparationer/', 'num': '01', 'title': 'Skadereparationer',
        'short': 'Återställning efter vatten-, brand- och inbrottsskador – med ärendet hanterat i Meps.',
        'text': 'Vi har mångårig erfarenhet av försäkringsuppdrag. Oavsett om det är en vattenläcka, en brand eller ett inbrott så ger vi oss inte förrän kunden är helt nöjd. Vi hanterar våra skadeärenden i Meps så att du som skadehandläggare kan känna dig trygg i att det blir en effektiv och proffsig process från besiktning till färdigställande.',
        'img': 'forsakringsskada', 'alt': 'Ett par går igenom papper efter en skada i hemmet',
        'pattern': 'parquet', 'material': 'Fiskbensparkett',
    },
    {
        'slug': 'affarsomraden/lokalanpassningar/', 'num': '02', 'title': 'Lokalanpassningar',
        'short': 'Attraktiva lokaler tillsammans med fastighetsägare och deras hyresgäster.',
        'text': 'AMT Bygg har lång erfarenhet av att skapa attraktiva lokaler tillsammans med fastighetsägare och dess hyresgäster. Vårt arbete genomsyras av ansvarstagande och en strävan att alltid hitta bästa möjliga lösning för varje given situation. Tillsammans bygger vi framtidens lokaler.',
        'img': 'renovering', 'alt': 'Snickare sågar en skiva med cirkelsåg',
        'pattern': 'studs', 'material': 'Regelverk',
    },
    {
        'slug': 'affarsomraden/entreprenad/', 'num': '03', 'title': 'Entreprenad',
        'short': 'Del- och totalentreprenader som håller både budget och tidsplan.',
        'text': 'Vi kan entreprenad. Oavsett om det är en delentreprenad eller en totalentreprenad så ser vi till att hålla både budget och tidsplan. Vårt mål är att vara den självklara samarbetspartnern till större byggföretag som behöver pålitliga underentreprenörer såväl som till beställaren som kräver en stabil och professionell totalentreprenör.',
        'img': 'team-ritning', 'alt': 'Byggarbetare studerar ritningar på arbetsplatsen',
        'pattern': 'brick', 'material': 'Löpförband',
    },
]

CLIENTS = [
    {'id': 'ncc', 'name': 'NCC', 'url': 'https://www.ncc.se', 'sector': 'Bygg & fastighetsutveckling',
     'desc': 'Ett av Nordens ledande bygg- och fastighetsutvecklingsföretag.'},
    {'id': 'castellum', 'name': 'Castellum', 'url': 'https://www.castellum.se/', 'sector': 'Fastighetsbolag',
     'desc': 'Ett av Nordens största börsnoterade fastighetsbolag, med kontor, logistik och samhällsfastigheter.'},
    {'id': 'hsb', 'name': 'HSB', 'url': 'https://www.hsb.se/', 'sector': 'Bostäder',
     'desc': 'Kooperativ bostadsorganisation som bygger, förvaltar och utvecklar bostäder – där möjligheterna bor.'},
    {'id': 'bra', 'name': 'BRA – Billström Riemer Andersson', 'url': 'https://bragroup.se/', 'sector': 'Bygg & fastighet',
     'desc': 'Bygg- och fastighetskoncern med rötter i Västsverige, verksam sedan 2007.'},
    {'id': 'nyb', 'name': 'NYB', 'url': 'https://ytskiktsbolaget.se', 'sector': 'Ytskikt',
     'desc': 'Göteborgsbaserat ytskiktsbolag – en naturlig samarbetspartner när golv, väggar och finish ska bli rätt.'},
    {'id': 'sustend', 'name': 'Sustend', 'url': 'https://sustend.se', 'sector': 'Fastighetskonsult',
     'desc': 'Konsulter inom underhållsplanering, besiktningar och projektledning för fastighetsägare och bostadsrättsföreningar.'},
    {'id': 'sivers', 'name': 'Sivers Semiconductors', 'url': 'https://www.sivers-semiconductors.com', 'sector': 'Teknik & industri',
     'desc': 'Svenskt teknikbolag inom halvledare för trådlös kommunikation och fotonik.'},
    {'id': 'flodens', 'name': 'Flodéns', 'url': 'https://flodens.se', 'sector': 'Byggentreprenör',
     'desc': 'Etablerad byggentreprenör med stark position i Göteborgsregionen.'},
    {'id': 'obos', 'name': 'OBOS', 'url': 'https://obos.se/', 'sector': 'Bostäder',
     'desc': 'Nordiskt bostadskooperativ som utvecklar, bygger och förvaltar bostäder.'},
]

INSURERS = [
    {'id': 'dina', 'name': 'Dina Försäkringar', 'url': 'https://www.dina.se/', 'note': 'Sedan 1768'},
    {'id': 'lansforsakringar', 'name': 'Länsförsäkringar Göteborg och Bohuslän',
     'url': 'https://www.lansforsakringar.se/goteborg-och-bohuslan/privat/', 'note': 'Göteborg och Bohuslän'},
]

PARTNERS = [
    {'id': 'ifk-2026', 'name': 'IFK Göteborg', 'url': 'https://ifkgoteborg.se/', 'tier': 'Officiell partner',
     'sport': 'Fotboll', 'desc': 'Officiell partner till IFK Göteborg – 2025 och 2026.', 'featured': True},
    {'id': 'frolunda', 'name': 'Frölunda Hockey Club', 'url': 'https://www.frolundahockey.com/', 'tier': 'Stolt partner',
     'sport': 'Ishockey', 'desc': 'Stolt partner till Frölunda Hockey Club.', 'featured': True},
    {'id': 'ois', 'name': 'Örgryte IS', 'url': 'https://oisfotboll.se/', 'tier': 'Partner',
     'sport': 'Fotboll', 'desc': 'Partner till Örgryte IS – en av Sveriges äldsta idrottsföreningar, grundad 1887.', 'featured': True},
    {'id': 'torslanda', 'name': 'Torslanda IK', 'url': 'https://www.svenskalag.se/torslandaik', 'tier': 'Föreningspartner',
     'sport': 'Sedan 1944', 'desc': 'Breddidrott på Hisingen.'},
    {'id': 'sorhaga', 'name': 'Sörhaga/Alingsås HK', 'url': 'https://www.svenskalag.se/sorhagaalingsashk', 'tier': 'Föreningspartner',
     'sport': 'Sedan 1932', 'desc': 'Hockey i Alingsås.'},
    {'id': 'kallered', 'name': 'Kållered SK', 'url': 'https://www.svenskalag.se/ksk', 'tier': 'Föreningspartner',
     'sport': 'Sportklubb', 'desc': 'Idrott för barn, unga och vuxna i Kållered.'},
    {'id': 'surte', 'name': 'Surte IS', 'url': 'https://www.laget.se/Surteis', 'tier': 'Föreningspartner',
     'sport': 'Idrottssällskap', 'desc': 'Föreningsliv i Surte, Ale kommun.'},
]

NAV = [
    {'id': 'start', 'label': 'Start', 'href': ''},
    {'id': 'affarsomraden', 'label': 'Affärsområden', 'href': 'affarsomraden/', 'mega': 'areas'},
    {'id': 'om-oss', 'label': 'Om oss', 'href': 'om-oss/', 'mega': 'company'},
    {'id': 'klienter', 'label': 'Klienter', 'href': 'klienter/'},
    {'id': 'partners', 'label': 'Partners', 'href': 'partners/'},
    {'id': 'kontakt', 'label': 'Kontakt', 'href': 'kontakt/'},
]

COMPANY_LINKS = [
    {'href': 'om-oss/', 'title': 'Om AMT Bygg', 'text': 'Ett modernt byggbolag med starka traditioner – grundat i Göteborg 2019.', 'pattern': 'wood'},
    {'href': 'om-oss/ledningssystem/', 'title': 'Ledningssystem', 'text': 'Certifierade i Povel – kvalitet, miljö och arbetsmiljö i ett system.', 'pattern': 'grid'},
    {'href': 'karriar/', 'title': 'Karriär', 'text': 'Vi söker servicesnickare. Bli en del av ett framgångsrikt team.', 'pattern': 'hatch'},
]


# ---------------------------------------------------------------------------
# Hjälpfunktioner
# ---------------------------------------------------------------------------
class Ctx:
    def __init__(self, path, absolute=False):
        self.path = path  # t.ex. 'om-oss/' eller '' för start
        self.absolute = absolute  # rotrelativa länkar (404-sidan kan visas på valfri URL)

    def url(self, target):
        """Relativ länk från aktuell sida till target ('' = start, 'om-oss/', 'kontakt/#form')."""
        target, _, frag = target.partition('#')
        if self.absolute:
            rel = '/' + target
        else:
            rel = posixpath.relpath(target or '.', self.path or '.')
            rel = './' if rel == '.' else rel + '/'
        if EXPLICIT:
            rel += 'index.html'
        return rel + ('#' + frag if frag else '')

    def asset(self, p):
        if self.absolute:
            return '/assets/' + p
        return posixpath.relpath('assets/' + p, self.path or '.')


def img_widths(name):
    ws = []
    for f in os.listdir(os.path.join(ROOT, 'assets', 'img')):
        m = re.fullmatch(re.escape(name) + r'-(\d+)\.webp', f)
        if m:
            ws.append(int(m.group(1)))
    return sorted(ws)


def img_dims(name, w):
    try:
        from PIL import Image
        with Image.open(os.path.join(ROOT, 'assets', 'img', f'{name}-{w}.jpg')) as im:
            return im.size
    except Exception:
        return (w, round(w * .66))


def pic(ctx, name, alt='', sizes='100vw', cls='', eager=False):
    ws = img_widths(name)
    if not ws:
        raise SystemExit(f'Bild saknas: {name}')
    webp = ', '.join(f"{ctx.asset(f'img/{name}-{w}.webp')} {w}w" for w in ws)
    jpg = ', '.join(f"{ctx.asset(f'img/{name}-{w}.jpg')} {w}w" for w in ws)
    fallback = ws[1] if len(ws) > 1 else ws[0]
    w, h = img_dims(name, fallback)
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ''
    return (f'<picture><source type="image/webp" srcset="{webp}" sizes="{sizes}">'
            f'<img src="{ctx.asset(f"img/{name}-{fallback}.jpg")}" srcset="{jpg}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{escape(alt)}"{c} {load}></picture>')


def arrow_link(href, text, cls='arrow', extra=''):
    return f'<a class="{cls}" href="{href}"{extra}>{text}</a>'


# ---------------------------------------------------------------------------
# Gemensamma block (partials)
# ---------------------------------------------------------------------------
AUDIENCES = [
    {'who': 'För försäkringsbolag och privatpersoner', 'area': 0,
     'text': 'Återställning efter vattenskada, brand eller inbrott – från besiktning till färdigställande.'},
    {'who': 'För fastighetsägare och hyresgäster', 'area': 1,
     'text': 'Hyresgästanpassningar och ombyggnader som skapar attraktiva lokaler.'},
    {'who': 'För byggföretag och beställare', 'area': 2,
     'text': 'Del-, under- och totalentreprenader som håller budget och tidsplan.'},
]

NEWS = [
    {'tag': 'Utmärkelse', 'when': '2025', 'title': 'AMT Bygg utsedda till Di Gasell 2025',
     'text': 'Dagens industri lyfter fram AMT Bygg som ett av Sveriges snabbväxande företag med sunda finanser.',
     'href': 'om-oss/', 'brand': 'gasell-2025', 'brand_bg': 'white'},
    {'tag': 'Karriär', 'when': 'Vi söker nu', 'title': 'Vi söker servicesnickare i Göteborg',
     'text': 'Vill du vara en del av ett framgångsrikt team? Erfarenhet av skadeärenden är ett stort plus.',
     'href': 'karriar/', 'img': 'hero-goteborg', 'alt': 'Hantverkare framför Göteborgs hamn'},
    {'tag': 'Partnerskap', 'when': '2026', 'title': 'Officiell partner till IFK Göteborg',
     'text': 'AMT Bygg fortsätter som officiell partner till IFK Göteborg – och stöttar idrotten i regionen.',
     'href': 'partners/', 'brand': 'ifk-2026', 'brand_bg': 'navy'},
]


def p_paths(ctx, arg=''):
    out = ['<div class="paths">']
    for a in AUDIENCES:
        area = AREAS[a['area']]
        out.append(f'''
      <a class="path" href="{ctx.url(area['slug'])}">
        <small>{a['who']}</small>
        <h3>{area['title']}</h3>
        <p>{a['text']}</p>
        <span class="arrow">Läs mer</span>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_areas(ctx, arg=''):
    out = ['<div class="cards">']
    for a in AREAS:
        out.append(f'''
      <article class="card">
        <div class="card__img">{pic(ctx, a['img'], a['alt'], '(max-width: 620px) 100vw, (max-width: 980px) 50vw, 33vw')}</div>
        <div class="card__body">
          <h3>{a['title']}</h3>
          <p>{a['short']}</p>
          <a class="arrow card__link" href="{ctx.url(a['slug'])}">Läs mer<span class="visually-hidden"> om {a['title'].lower()}</span></a>
        </div>
      </article>''')
    out.append('</div>')
    return ''.join(out)


def p_logowall(ctx, arg=''):
    ids = arg.split(',') if arg else [c['id'] for c in CLIENTS]
    n = 5 if len(ids) >= 9 else min(len(ids), 5)
    items = [f'<a href="{c["url"]}" target="_blank" rel="noopener" title="{escape(c["name"])}">'
             f'<img src="{ctx.asset("logos/" + c["id"] + ".png")}" alt="{escape(c["name"])}" loading="lazy"></a>'
             for c in CLIENTS if c['id'] in ids]
    items += ['<span class="logos__fill" aria-hidden="true"></span>'] * ((-len(items)) % n)
    return f'<div class="logos" style="--n:{n}">' + ''.join(items) + '</div>'


def p_crestwall(ctx, arg=''):
    items = [f'<a href="{p["url"]}" target="_blank" rel="noopener" title="{escape(p["name"])}">'
             f'<img src="{ctx.asset("logos/" + p["id"] + ".png")}" alt="{escape(p["name"])}" loading="lazy"></a>'
             for p in PARTNERS]
    return '<div class="logos logos--crests" style="--n:7">' + ''.join(items) + '</div>'


def p_agreements(ctx, arg=''):
    out = ['<div class="agreements">']
    for x in INSURERS:
        out.append(f'<a class="agreement" href="{x["url"]}" target="_blank" rel="noopener">'
                   f'<img src="{ctx.asset("logos/" + x["id"] + ".png")}" alt="{escape(x["name"])}" loading="lazy">'
                   f'<span>Ramavtal skadereparationer · {escape(x["name"])}</span></a>')
    out.append('</div>')
    return ''.join(out)


def p_clients(ctx, arg=''):
    out = ['<div class="clients">']
    for c in CLIENTS:
        host = re.sub(r'^https?://(www\.)?', '', c['url']).rstrip('/')
        out.append(f'''
      <a class="client" href="{c['url']}" target="_blank" rel="noopener">
        <div class="client__logo"><img src="{ctx.asset('logos/' + c['id'] + '.png')}" alt="" loading="lazy"></div>
        <span class="client__sector">{escape(c['sector'])}</span>
        <h3>{escape(c['name'])}</h3>
        <p>{escape(c['desc'])}</p>
        <span class="arrow">{host}<span class="visually-hidden"> (öppnas i ny flik)</span></span>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_partners(ctx, arg=''):
    featured = arg == 'featured'
    sel = [p for p in PARTNERS if bool(p.get('featured')) == featured]
    out = [f'<div class="partners" style="--n:{3 if featured else 4}">']
    for p in sel:
        out.append(f'''
      <a class="partner" href="{p['url']}" target="_blank" rel="noopener">
        <div class="partner__crest"><img src="{ctx.asset('logos/' + p['id'] + '.png')}" alt="" loading="lazy"></div>
        <small>{escape(p['tier'])} · {escape(p['sport'])}</small>
        <h3>{escape(p['name'])}</h3>
        <p>{escape(p['desc'])}</p>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_areanav(ctx, arg=''):
    others = [a for a in AREAS if a['slug'] != arg]
    out = ['<div class="cards" style="--n:2">']
    for a in others:
        out.append(f'''
      <article class="card">
        <div class="card__img">{pic(ctx, a['img'], a['alt'], '(max-width: 620px) 100vw, 50vw')}</div>
        <div class="card__body">
          <h3>{a['title']}</h3>
          <p>{a['short']}</p>
          <a class="arrow card__link" href="{ctx.url(a['slug'])}">Läs mer</a>
        </div>
      </article>''')
    out.append('</div>')
    return ''.join(out)


def _consent(ctx):
    return (f'<label class="consent"><input type="checkbox" name="samtycke" required> <span>Jag har tagit del av hur AMT Bygg '
            f'behandlar mina <a class="inline" href="{ctx.url("integritetspolicy/")}">personuppgifter</a>.</span></label>')


def p_contactform(ctx, arg=''):
    ep = f' data-endpoint="{FORM_ENDPOINT_CONTACT}"' if FORM_ENDPOINT_CONTACT else ''
    return f'''
<form class="form" id="formular" data-form{ep} data-mailto="{COMPANY['email']}" data-subject="Kontakt via amtgroup.se"
      data-success="Tack! Vi återkommer så fort som möjligt."
      data-mailto-note="Ditt mejlprogram öppnas med meddelandet ifyllt. Tryck skicka där så återkommer vi så fort som möjligt."
      action="mailto:{COMPANY['email']}" method="post" enctype="text/plain">
  <div class="form__head">
    <h2>Skicka ett meddelande</h2>
    <p>Fyll i formuläret så återkommer vi så fort som möjligt, normalt inom en arbetsdag.</p>
  </div>
  <div class="fields">
    <div class="field"><label for="k-fornamn">Förnamn <span class="req">*</span></label><input id="k-fornamn" name="fornamn" autocomplete="given-name" required></div>
    <div class="field"><label for="k-efternamn">Efternamn <span class="req">*</span></label><input id="k-efternamn" name="efternamn" autocomplete="family-name" required></div>
    <div class="field"><label for="k-mejl">Mejladress <span class="req">*</span></label><input id="k-mejl" name="mejl" type="email" autocomplete="email" required></div>
    <div class="field"><label for="k-telefon">Telefon</label><input id="k-telefon" name="telefon" type="tel" autocomplete="tel"></div>
    <div class="field field--full"><label for="k-amne">Ämne</label>
      <select id="k-amne" name="amne">
        <option value="">Välj ämne</option><option>Skadereparation</option><option>Lokalanpassning</option><option>Entreprenad</option>
        <option>Samarbete och partnerskap</option><option>Jobb och karriär</option><option>Övrigt</option>
      </select>
    </div>
    <div class="field field--full"><label for="k-meddelande">Meddelande <span class="req">*</span></label><textarea id="k-meddelande" name="meddelande" required></textarea></div>
    {_consent(ctx)}
  </div>
  <div class="form__foot">
    <p>Fält markerade med * är obligatoriska.</p>
    <button class="btn" type="submit">Skicka</button>
  </div>
  <div class="form__status" role="status" tabindex="-1"></div>
</form>'''


def p_damageform(ctx, arg=''):
    ep = f' data-endpoint="{FORM_ENDPOINT_DAMAGE}"' if FORM_ENDPOINT_DAMAGE else ''
    return f'''
<form class="form" id="formular" data-form{ep} data-mailto="{COMPANY['email']}" data-subject="Skadeanmälan via amtgroup.se"
      data-success="Ditt meddelande är skickat. Vi kontaktar dig så snart som möjligt."
      data-mailto-note="Ditt mejlprogram öppnas med skadeanmälan ifylld. Bifoga gärna PDF:en från försäkringsbolaget och tryck skicka."
      action="mailto:{COMPANY['email']}" method="post" enctype="text/plain">
  <div class="form__head">
    <h2>Kontakta oss för gratis rådgivning och offert</h2>
    <p>Fyll i formuläret så återkommer vi så snart som möjligt.</p>
  </div>
  <div class="fields">
    <div class="field field--full"><label for="s-namn">Namn <span class="req">*</span></label><input id="s-namn" name="namn" autocomplete="name" required></div>
    <div class="field"><label for="s-mejl">E-post <span class="req">*</span></label><input id="s-mejl" name="epost" type="email" autocomplete="email" required></div>
    <div class="field"><label for="s-telefon">Telefon <span class="req">*</span></label><input id="s-telefon" name="telefon" type="tel" autocomplete="tel" required></div>
    <div class="field field--full"><label for="s-adress">Adress</label><input id="s-adress" name="adress" autocomplete="street-address"></div>
    <div class="field"><label for="s-bolag">Försäkringsbolag</label><input id="s-bolag" name="forsakringsbolag" list="forsakringsbolag"></div>
    <div class="field"><label for="s-nummer">Skadenummer</label><input id="s-nummer" name="skadenummer"></div>
    <datalist id="forsakringsbolag"><option value="Dina Försäkringar"><option value="Länsförsäkringar Göteborg och Bohuslän"></datalist>
    <div class="field field--full"><label for="s-meddelande">Meddelande <span class="req">*</span></label><textarea id="s-meddelande" name="meddelande" placeholder="Beskriv kort vad som har hänt och var skadan finns." required></textarea></div>
    <div class="field field--full"><label for="s-fil">Bifoga fil (valfritt)</label><div class="file-pick"><input id="s-fil" name="fil" type="file" accept=".pdf,image/*" data-file><span class="file-pick__btn" aria-hidden="true">Välj fil</span><span class="file-pick__name" data-file-name>Ingen fil vald</span></div><small>PDF från försäkringsbolaget.</small></div>
    {_consent(ctx)}
  </div>
  <div class="form__foot">
    <p>Du kan kontakta oss även om vi inte har ramavtal med ditt försäkringsbolag.</p>
    <button class="btn" type="submit">Skicka meddelande</button>
  </div>
  <div class="form__status" role="status" tabindex="-1"></div>
</form>'''


def p_stick(ctx, arg=''):
    media = ''.join(pic(ctx, a['img'], '', '50vw', '', False).replace('<picture>', f'<picture data-stick="{i}"' + (' class="is-active"' if i == 0 else '') + '>', 1)
                    for i, a in enumerate(AREAS))
    panels = []
    for i, a in enumerate(AREAS):
        who = AUDIENCES[i]['who']
        panels.append(f'''
      <article class="stick__panel" data-stick-panel="{i}">
        <div class="stick__img-m">{pic(ctx, a['img'], a['alt'], '100vw')}</div>
        <small>{who}</small>
        <h3>{a['title']}</h3>
        <p>{a['text']}</p>
        <a class="arrow" href="{ctx.url(a['slug'])}">Läs mer om {a['title'].lower()}</a>
      </article>''')
    return f'<div class="stick"><div class="stick__media" aria-hidden="true">{media}</div><div class="stick__panels">{"".join(panels)}</div></div>'


def p_news(ctx, arg=''):
    out = []
    for n in NEWS:
        if n.get('img'):
            media = f'<div class="card__img">{pic(ctx, n["img"], n["alt"], "(max-width: 760px) 84vw, 30vw")}</div>'
        else:
            cls = 'card__brand card__brand--white' if n['brand_bg'] == 'white' else 'card__brand'
            media = f'<div class="{cls}"><img src="{ctx.asset("logos/" + n["brand"] + ".png")}" alt="" loading="lazy"></div>'
        out.append(f'''
      <article class="card">
        {media}
        <div class="card__body">
          <div class="btns" style="gap:12px;align-items:center"><span class="tag">{n['tag']}</span><span class="card__meta">{n['when']}</span></div>
          <h3>{n['title']}</h3>
          <p>{n['text']}</p>
          <a class="arrow card__link" href="{ctx.url(n['href'])}">Läs mer</a>
        </div>
      </article>''')
    return '<div class="rail" data-rail>' + ''.join(out) + '</div>'


def rail_nav():
    svg = lambda d: f'<svg viewBox="0 0 18 18" aria-hidden="true"><path d="{d}" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
    return (f'<div class="rail__nav"><button class="rail__btn" type="button" data-rail-prev aria-label="Föregående">{svg("M11 4 6 9l5 5")}</button>'
            f'<button class="rail__btn" type="button" data-rail-next aria-label="Nästa">{svg("M7 4l5 5-5 5")}</button></div>')


def p_railnav(ctx, arg=''):
    return rail_nav()


def p_cta(ctx, arg=''):
    if arg == 'skada':
        img, title, text = 'skada-kontor', 'Har du råkat ut för en skada?', 'Anmäl skadan till ditt försäkringsbolag, meddela att AMT Bygg hanterar återställningen och kontakta oss. Du kan höra av dig även om vi inte har ramavtal med ditt försäkringsbolag.'
        btns = f'<a class="btn btn--white" href="{ctx.url("anmal-skada/")}">Anmäl skada</a><a class="btn btn--outline" href="tel:{COMPANY["phone_href"]}">Ring {COMPANY["phone"]}</a>'
        contact = f'<span>Telefontid måndag–fredag 09.00–15.00</span><a href="mailto:{COMPANY["email"]}">{COMPANY["email"]}</a>'
    else:
        img, title, text = 'hero-goteborg', 'Låt oss bygga det tillsammans.', 'Berätta om ert projekt, er lokal eller ert skadeärende så återkommer vi med ett tydligt nästa steg.'
        btns = f'<a class="btn btn--white" href="{ctx.url("kontakt/")}">Kontakta oss</a><a class="btn btn--outline" href="{ctx.url("anmal-skada/")}">Anmäl skada</a>'
        contact = f'<a href="tel:{COMPANY["phone_href"]}">{COMPANY["phone"]}</a><a href="mailto:{COMPANY["email"]}">{COMPANY["email"]}</a><span>{COMPANY["street"]}, {COMPANY["city"]}</span>'
    return f'''
<section class="cta" aria-label="{title}">
  <div class="cta__img">{pic(ctx, img, '', '100vw')}</div>
  <div class="cta__text">
    <h2>{title}</h2>
    <p>{text}</p>
    <div class="btns">{btns}</div>
    <div class="cta__contact">{contact}</div>
  </div>
</section>'''


PARTIALS = {
    'paths': p_paths, 'areas': p_areas, 'news': p_news, 'logowall': p_logowall, 'crestwall': p_crestwall,
    'agreements': p_agreements, 'clients': p_clients, 'partners': p_partners, 'cta': p_cta,
    'areanav': p_areanav, 'stick': p_stick, 'railnav': p_railnav, 'contactform': p_contactform, 'damageform': p_damageform,
}


# ---------------------------------------------------------------------------
# Sidmall
# ---------------------------------------------------------------------------
def header(ctx, active):
    area_links = ''.join(f'<a href="{ctx.url(a["slug"])}">{a["title"]}</a>' for a in AREAS)
    company_links = ''.join(f'<a href="{ctx.url(c["href"])}">{c["title"]}</a>' for c in COMPANY_LINKS[1:])
    main = [
        ('affarsomraden/', 'Affärsområden', area_links),
        ('om-oss/', 'Om oss', company_links),
        ('klienter/', 'Klienter', ''),
        ('partners/', 'Partners', ''),
        ('kontakt/', 'Kontakt', ''),
    ]
    items = ''.join(
        f'<li><a href="{ctx.url(h)}"{" aria-current=\"page\"" if ctx.path == h else ""}>{t}</a>'
        + (f'<div class="menu__sub">{sub}</div>' if sub else '') + '</li>'
        for h, t, sub in main)
    return f'''
<a class="skip-link" href="#main">Hoppa till innehållet</a>
<header class="header">
  <div class="wrap">
    <a class="brand" href="{ctx.url('')}"><img src="{ctx.asset('brand/amt-bygg-logo-white.svg')}" alt="AMT Bygg – till startsidan" width="200" height="26"></a>
    <a class="header__phone" href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a>
    <a class="btn btn--white btn--sm header__cta" href="{ctx.url('anmal-skada/')}">Anmäl skada</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu"><span data-menu-label>Meny</span><span class="menu-btn__icon" aria-hidden="true"></span></button>
  </div>
</header>
<div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="Meny" hidden>
  <div class="texture"></div>
  <div class="wrap menu__inner">
    <nav aria-label="Huvudmeny"><ul class="menu__main"><li><a href="{ctx.url('')}">Start</a></li>{items}</ul></nav>
    <div class="menu__side">
      <a class="menu__card" href="{ctx.url('anmal-skada/')}">{pic(ctx, 'skada-kontor', '', '480px')}<div><strong>Har du råkat ut för en skada?</strong><span class="arrow">Anmäl skada</span></div></a>
      <div class="menu__contact">
        <a href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a><br>
        <a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a><br>
        {COMPANY['street']}, {COMPANY['zip']} {COMPANY['city']}<br>
        <a href="{ctx.url('karriar/')}">Karriär – vi söker servicesnickare</a>
      </div>
    </div>
  </div>
</div>'''


def footer(ctx):
    areas = ''.join(f'<li><a href="{ctx.url(a["slug"])}">{a["title"]}</a></li>' for a in AREAS)
    return f'''
<footer class="footer">
  <div class="wrap footer__top">
    <div>
      <p class="footer__lead">Ett modernt byggbolag med starka traditioner.</p>
      <div class="footer__badges">
        <a href="https://www.di.se/amnen/di-gasell/" target="_blank" rel="noopener"><img src="{ctx.asset('logos/gasell-2025.png')}" alt="Di Gasell 2025" loading="lazy"></a>
        <a href="{ctx.url('om-oss/ledningssystem/')}"><img src="{ctx.asset('logos/povel.png')}" alt="Certifierade i Povel" loading="lazy"></a>
      </div>
    </div>
    <div><h2>Affärsområden</h2><ul class="list">{areas}<li><a href="{ctx.url('anmal-skada/')}">Anmäl skada</a></li></ul></div>
    <div><h2>Företaget</h2><ul class="list">
      <li><a href="{ctx.url('om-oss/')}">Om oss</a></li><li><a href="{ctx.url('om-oss/ledningssystem/')}">Ledningssystem</a></li>
      <li><a href="{ctx.url('klienter/')}">Klienter</a></li><li><a href="{ctx.url('partners/')}">Partners</a></li><li><a href="{ctx.url('karriar/')}">Karriär</a></li>
    </ul></div>
    <div><h2>Kontakt</h2><address>
      <a href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a><br><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a><br><br>
      <a href="{COMPANY['maps']}" target="_blank" rel="noopener">{COMPANY['street']}<br>{COMPANY['zip']} {COMPANY['city']}</a>
    </address></div>
    <div><h2>Fakturering</h2><address>{COMPANY['legal']}<br>Org.nr {COMPANY['orgnr']}<br><a href="mailto:{COMPANY['invoice_email']}">{COMPANY['invoice_email']}</a></address></div>
  </div>
  <div class="wrap footer__mark" aria-hidden="true">
    <img src="{ctx.asset('brand/amt-bygg-logo-white.svg')}" alt="" width="1400" height="182" loading="lazy">
    <div class="tagline"><span>T</span><span>I</span><span>L</span><span>L</span><span>S</span><span>A</span><span>M</span><span>M</span><span>A</span><span>N</span><span>S</span></div>
  </div>
  <div class="footer__bottom">
    <div class="wrap">
      <span>© <span data-year>{date.today().year}</span> {COMPANY['legal']}</span>
      <ul class="list">
        <li><a href="{ctx.url('integritetspolicy/')}">Integritetspolicy</a></li>
        <li><a href="https://se.trustpilot.com/review/amtgroup.se" target="_blank" rel="noopener">Omdömen på Trustpilot</a></li>
        <li><a href="{ctx.asset('files/AMT-Bygg.vcf')}" download>Spara som kontakt</a></li>
      </ul>
    </div>
  </div>
{ELEVATE_CREDIT}</footer>'''


def jsonld(meta):
    org = {
        '@context': 'https://schema.org',
        '@type': 'GeneralContractor',
        '@id': SITE_URL + '/#organisation',
        'name': 'AMT Bygg',
        'legalName': COMPANY['legal'],
        'url': SITE_URL + '/',
        'logo': SITE_URL + '/assets/brand/icon-512.png',
        'image': SITE_URL + '/assets/img/hero-goteborg-1920.jpg',
        'telephone': COMPANY['phone_href'],
        'email': COMPANY['email'],
        'foundingDate': '2019',
        'taxID': COMPANY['orgnr'],
        'slogan': 'AMT Bygg – Tillsammans.',
        'address': {'@type': 'PostalAddress', 'streetAddress': COMPANY['street'], 'postalCode': COMPANY['zip'].replace(' ', ''),
                    'addressLocality': COMPANY['city'], 'addressRegion': COMPANY['region'], 'addressCountry': 'SE'},
        'areaServed': 'Göteborgsregionen',
        'award': 'Di Gasell 2025',
        'knowsAbout': ['Skadereparationer', 'Lokalanpassningar', 'Byggentreprenad', 'Totalentreprenad', 'Delentreprenad'],
    }
    return json.dumps(org, ensure_ascii=False)


def layout(meta, body_html):
    ctx = Ctx(meta['path'], meta.get('absolute', False))
    title = meta['title']
    full_title = title if meta.get('full_title') else f'{title} | AMT Bygg'
    canonical = SITE_URL + '/' + meta['path']
    body_cls = ''
    og_img = SITE_URL + '/assets/img/' + meta.get('og', 'hero-goteborg') + '-1280.jpg'
    robots = '<meta name="robots" content="noindex">' if meta.get('noindex') else ''
    ld = f'<script type="application/ld+json">{jsonld(meta)}</script>' if meta['path'] == '' else ''
    return f'''<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<script>document.documentElement.className="js"</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full_title)}</title>
<meta name="description" content="{escape(meta['description'])}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:locale" content="sv_SE">
<meta property="og:site_name" content="AMT Bygg">
<meta property="og:title" content="{escape(full_title)}">
<meta property="og:description" content="{escape(meta['description'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0a1022">
<link rel="icon" href="{ctx.asset('brand/favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{ctx.asset('brand/favicon-32.png')}" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{ctx.asset('brand/apple-touch-icon.png')}">
<link rel="preload" href="{ctx.asset('fonts/Unbounded.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{ctx.asset('fonts/Geist.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{ctx.asset('css/fonts.css')}">
<link rel="stylesheet" href="{ctx.asset('css/main.css')}">
{ld}
</head>
<body{body_cls}>
{header(ctx, meta.get('nav', ''))}
<main id="main">
{body_html}
</main>
{footer(ctx)}
<script src="{ctx.asset('js/main.js')}" defer></script>
</body>
</html>
'''


def render_tokens(ctx, html):
    def r_pic(m):
        parts = [p.strip() for p in m.group(1).split('|')]
        parts += [''] * (5 - len(parts))
        name, alt, sizes, cls, eager = parts[:5]
        return pic(ctx, name, alt, sizes or '100vw', cls, eager == 'eager')

    def r_partial(m):
        name, _, arg = m.group(1).strip().partition(' ')
        if name not in PARTIALS:
            raise SystemExit(f'Okänd partial: {name}')
        return PARTIALS[name](ctx, arg.strip())

    html = re.sub(r'\{\{>\s*([^}]+)\}\}', r_partial, html)
    html = re.sub(r'\{\{pic\s+([^}]+)\}\}', r_pic, html)
    html = re.sub(r'\{\{url\s*([^}]*)\}\}', lambda m: ctx.url(m.group(1).strip()), html)
    html = re.sub(r'\{\{asset\s+([^}]+)\}\}', lambda m: ctx.asset(m.group(1).strip()), html)
    for k, v in COMPANY.items():
        html = html.replace('{{' + k + '}}', v)
    if '{{' in html:
        left = re.findall(r'\{\{[^}]*\}\}', html)
        raise SystemExit(f'Oersatta taggar: {left[:5]}')
    return html


def build():
    pages = sorted(f for f in os.listdir(os.path.join(SRC, 'pages')) if f.endswith('.html'))
    sitemap = []
    for f in pages:
        raw = open(os.path.join(SRC, 'pages', f), encoding='utf-8').read()
        m = re.match(r'\s*<!--meta\s+(\{.*?\})\s*-->', raw, re.S)
        if not m:
            raise SystemExit(f'Metadata saknas i {f}')
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        ctx = Ctx(meta['path'], meta.get('absolute', False))
        html = layout(meta, render_tokens(ctx, body))
        out = meta.get('out') or (meta['path'] + 'index.html')
        dest = os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(dest) or ROOT, exist_ok=True)
        open(dest, 'w', encoding='utf-8').write(html)
        if not meta.get('noindex'):
            sitemap.append(SITE_URL + '/' + meta['path'])
        print('  ', out)
    today = date.today().isoformat()
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>' for u in sitemap]
    xml.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('\n'.join(xml) + '\n')
    # Gamla Wix-adressen /skadereparation pekade på skadeanmälan – behåll länkar och sökträffar.
    os.makedirs(os.path.join(ROOT, 'skadereparation'), exist_ok=True)
    target = '../anmal-skada/' + ('index.html' if EXPLICIT else '')
    open(os.path.join(ROOT, 'skadereparation', 'index.html'), 'w').write(
        f'<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Anmäl skada | AMT Bygg</title>'
        f'<link rel="canonical" href="{SITE_URL}/anmal-skada/"><meta name="robots" content="noindex">'
        f'<meta http-equiv="refresh" content="0; url={target}"></head>'
        f'<body><p><a href="{target}">Anmäl skada</a></p></body></html>\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')


if __name__ == '__main__':
    build()
