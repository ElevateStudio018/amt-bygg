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


def swatch(pattern, tone='blue', bg='var(--navy)', extra=''):
    return (f'<div class="swatch" style="--sw-bg:{bg}" aria-hidden="true">'
            f'<div class="pattern pat-{pattern} pat--{tone}{extra}"></div></div>')


def arrow():
    return '<span class="arr" aria-hidden="true"></span>'


# ---------------------------------------------------------------------------
# Gemensamma block (partials)
# ---------------------------------------------------------------------------
def p_areas(ctx, arg=''):
    out = ['<div class="areas">']
    for i, a in enumerate(AREAS):
        out.append(f'''
      <article class="area reveal" style="--d:{i * .08:.2f}s">
        <div class="area__media">
          {pic(ctx, a['img'], a['alt'], '(max-width: 980px) 100vw, 33vw')}
          <span class="area__num">{a['num']} / 03</span>
          <div class="area__strip">{swatch(a['pattern'], 'blue')}</div>
        </div>
        <div class="area__body">
          <h3>{a['title']}</h3>
          <p>{a['text']}</p>
          <a class="link-arrow area__link" href="{ctx.url(a['slug'])}"><span>Läs mer om {a['title'].lower()}</span>{arrow()}</a>
        </div>
      </article>''')
    out.append('</div>')
    return ''.join(out)


def p_logowall(ctx, arg=''):
    ids = arg.split(',') if arg else [c['id'] for c in CLIENTS]
    cols = 5 if len(ids) >= 9 else min(len(ids), 4)
    items = []
    for c in CLIENTS:
        if c['id'] not in ids:
            continue
        items.append(f'<a href="{c["url"]}" target="_blank" rel="noopener" aria-label="{escape(c["name"])} (öppnas i ny flik)">'
                     f'<img src="{ctx.asset("logos/" + c["id"] + ".png")}" alt="{escape(c["name"])}" loading="lazy">'
                     f'<span class="lw-name" aria-hidden="true">{escape(c["sector"])}</span></a>')
    # fyll ut sista raden med en mönsterruta så att rutnätet blir helt
    rem = (-len(items)) % cols
    for _ in range(rem):
        items.append(f'<div aria-hidden="true" style="padding:0;position:relative;overflow:hidden">'
                     f'<div class="pattern pat-hatch pat--navy" style="--pat-o:.12"></div></div>')
    return f'<div class="logo-wall reveal" style="--cols:{cols}">' + ''.join(items) + '</div>'


def p_crestwall(ctx, arg=''):
    items = []
    for p in PARTNERS:
        items.append(f'<a href="{p["url"]}" target="_blank" rel="noopener" aria-label="{escape(p["name"])} (öppnas i ny flik)">'
                     f'<img src="{ctx.asset("logos/" + p["id"] + ".png")}" alt="{escape(p["name"])}" loading="lazy">'
                     f'<span class="lw-name" aria-hidden="true">{escape(p["tier"])}</span></a>')
    return '<div class="logo-wall logo-wall--crests reveal" style="--cols:7">' + ''.join(items) + '</div>'


def p_agreements(ctx, arg=''):
    out = ['<div class="agreements reveal">']
    for x in INSURERS:
        out.append(f'<a class="agreement" href="{x["url"]}" target="_blank" rel="noopener">'
                   f'<img src="{ctx.asset("logos/" + x["id"] + ".png")}" alt="{escape(x["name"])}" loading="lazy">'
                   f'<span>Ramavtal skadereparationer · {escape(x["note"])}</span></a>')
    out.append('</div>')
    return ''.join(out)


def p_clients(ctx, arg=''):
    out = ['<div class="clients">']
    for i, c in enumerate(CLIENTS):
        host = re.sub(r'^https?://(www\.)?', '', c['url']).rstrip('/')
        sq = ' client__logo--square' if c['id'] in ('hsb',) else ''
        out.append(f'''
      <a class="client reveal" style="--d:{(i % 3) * .06:.2f}s" href="{c['url']}" target="_blank" rel="noopener">
        <div class="client__logo{sq}"><img src="{ctx.asset('logos/' + c['id'] + '.png')}" alt="" loading="lazy"></div>
        <span class="client__sector">{escape(c['sector'])}</span>
        <h3>{escape(c['name'])}</h3>
        <p>{escape(c['desc'])}</p>
        <span class="client__url">{host}<span class="visually-hidden"> (öppnas i ny flik)</span></span>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_partners(ctx, arg=''):
    featured = arg == 'featured'
    sel = [p for p in PARTNERS if bool(p.get('featured')) == featured]
    cls = 'partners partners--featured' if featured else 'partners'
    out = [f'<div class="{cls}">']
    for i, p in enumerate(sel):
        out.append(f'''
      <a class="partner reveal" style="--d:{i * .06:.2f}s" href="{p['url']}" target="_blank" rel="noopener">
        <div class="partner__crest"><img src="{ctx.asset('logos/' + p['id'] + '.png')}" alt="" loading="lazy"></div>
        <span class="partner__tier">{escape(p['tier'])} · {escape(p['sport'])}</span>
        <h3>{escape(p['name'])}</h3>
        <p>{escape(p['desc'])}</p>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_cta(ctx, arg=''):
    if arg == 'skada':
        return f'''
<section class="cta-band" aria-labelledby="cta-skada">
  <div class="pattern pat-wood pat--blue pattern--fade-l"></div>
  <div class="wrap">
    <div class="cta-band__text reveal">
      <hr class="rule-gold">
      <h2 id="cta-skada">Har du råkat ut för en skada?</h2>
      <p>Chansa inte med din skada. Anmäl den till ditt försäkringsbolag, meddela att AMT Bygg hanterar återställningen – och kontakta oss. Du kan höra av dig även om vi inte har ramavtal med ditt försäkringsbolag.</p>
    </div>
    <div class="cta-band__actions reveal" style="--d:.1s">
      <div class="btn-row">
        <a class="btn btn--gold" href="{ctx.url('anmal-skada/')}">Anmäl skada {arrow()}</a>
        <a class="btn btn--ghost" href="tel:{COMPANY['phone_href']}">Ring {COMPANY['phone']}</a>
      </div>
      <div class="cta-band__contact">Telefontid måndag–fredag 09.00–15.00<br><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a></div>
    </div>
  </div>
</section>'''
    return f'''
<section class="cta-band" aria-labelledby="cta-kontakt">
  <div class="pattern pat-wood pat--blue pattern--fade-l"></div>
  <div class="wrap">
    <div class="cta-band__text reveal">
      <hr class="rule-gold">
      <h2 id="cta-kontakt">Låt oss bygga det tillsammans.</h2>
      <p>Berätta om ert projekt, er lokal eller ert skadeärende. Vi återkommer så snart som möjligt med ett tydligt nästa steg.</p>
    </div>
    <div class="cta-band__actions reveal" style="--d:.1s">
      <div class="btn-row">
        <a class="btn btn--gold" href="{ctx.url('kontakt/')}">Kontakta oss {arrow()}</a>
        <a class="btn btn--ghost" href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a>
      </div>
      <div class="cta-band__contact">{COMPANY['street']}, {COMPANY['zip']} {COMPANY['city']}<br><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a></div>
    </div>
  </div>
</section>'''


def p_areanav(ctx, arg=''):
    """Länkar till övriga affärsområden längst ned på en affärsområdessida."""
    others = [a for a in AREAS if a['slug'] != arg]
    out = ['<div class="cells" style="--cols:2">']
    for a in others:
        out.append(f'''
      <a class="cell reveal" href="{ctx.url(a['slug'])}">
        {swatch(a['pattern'], 'blue')}
        <span class="cell__tag">Affärsområde {a['num']} · {a['material']}</span>
        <h3>{a['title']}</h3>
        <p>{a['short']}</p>
        <span class="link-arrow mt-s"><span>Läs mer</span>{arrow()}</span>
      </a>''')
    out.append('</div>')
    return ''.join(out)


def p_contactform(ctx, arg=''):
    ep = f' data-endpoint="{FORM_ENDPOINT_CONTACT}"' if FORM_ENDPOINT_CONTACT else ''
    return f'''
<form class="form" id="formular" data-form{ep} data-mailto="{COMPANY['email']}" data-subject="Kontakt via amtgroup.se"
      data-success="Tack! Vi återkommer så fort som möjligt."
      data-mailto-note="Ditt mejlprogram öppnas med meddelandet ifyllt – tryck skicka där så återkommer vi så fort som möjligt."
      action="mailto:{COMPANY['email']}" method="post" enctype="text/plain">
  <div class="form__head">
    <span class="eyebrow eyebrow--blue">Formulär</span>
    <h2 class="mt-s">Kontakta oss</h2>
    <p>Vid frågor kontakta oss på telefon, mejl eller via formuläret nedan.</p>
  </div>
  <div class="fields">
    <div class="field"><label for="k-fornamn">Förnamn <span class="req">*</span></label><input id="k-fornamn" name="fornamn" autocomplete="given-name" required></div>
    <div class="field"><label for="k-efternamn">Efternamn <span class="req">*</span></label><input id="k-efternamn" name="efternamn" autocomplete="family-name" required></div>
    <div class="field"><label for="k-mejl">Mejladress <span class="req">*</span></label><input id="k-mejl" name="mejl" type="email" autocomplete="email" required></div>
    <div class="field"><label for="k-telefon">Telefon</label><input id="k-telefon" name="telefon" type="tel" autocomplete="tel"></div>
    <div class="field field--full"><label for="k-amne">Ämne</label>
      <select id="k-amne" name="amne">
        <option value="">Välj ämne</option>
        <option>Skadereparation</option>
        <option>Lokalanpassning</option>
        <option>Entreprenad</option>
        <option>Samarbete och partnerskap</option>
        <option>Jobb och karriär</option>
        <option>Övrigt</option>
      </select>
    </div>
    <div class="field field--full"><label for="k-meddelande">Meddelande <span class="req">*</span></label><textarea id="k-meddelande" name="meddelande" required></textarea></div>
    <label class="consent"><input type="checkbox" name="samtycke" required> <span>Jag har tagit del av hur AMT Bygg behandlar mina <a class="inline" href="{ctx.url('integritetspolicy/')}">personuppgifter</a>.</span></label>
  </div>
  <div class="form__foot">
    <p>Vi återkommer så fort som möjligt, normalt inom en arbetsdag.</p>
    <button class="btn" type="submit">Skicka {arrow()}</button>
  </div>
  <div class="form__status" role="status" tabindex="-1"></div>
</form>'''


def p_damageform(ctx, arg=''):
    ep = f' data-endpoint="{FORM_ENDPOINT_DAMAGE}"' if FORM_ENDPOINT_DAMAGE else ''
    return f'''
<form class="form" id="formular" data-form{ep} data-mailto="{COMPANY['email']}" data-subject="Skadeanmälan via amtgroup.se"
      data-success="Ditt meddelande är skickat. Vi kontaktar dig så snart som möjligt."
      data-mailto-note="Ditt mejlprogram öppnas med skadeanmälan ifylld. Bifoga gärna PDF:en från försäkringsbolaget och tryck skicka – vi kontaktar dig så snart som möjligt."
      action="mailto:{COMPANY['email']}" method="post" enctype="text/plain">
  <div class="form__head">
    <span class="eyebrow eyebrow--blue">Skadeanmälan</span>
    <h2 class="mt-s">Kontakta oss för gratis rådgivning och offert</h2>
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
    <label class="consent"><input type="checkbox" name="samtycke" required> <span>Jag har tagit del av hur AMT Bygg behandlar mina <a class="inline" href="{ctx.url('integritetspolicy/')}">personuppgifter</a>.</span></label>
  </div>
  <div class="form__foot">
    <p>Du kan kontakta oss även om vi inte har ramavtal med ditt försäkringsbolag.</p>
    <button class="btn btn--gold" type="submit">Skicka meddelande {arrow()}</button>
  </div>
  <div class="form__status" role="status" tabindex="-1"></div>
</form>'''


PARTIALS = {
    'areas': p_areas, 'logowall': p_logowall, 'crestwall': p_crestwall, 'agreements': p_agreements,
    'clients': p_clients, 'partners': p_partners, 'cta': p_cta, 'areanav': p_areanav,
    'contactform': p_contactform, 'damageform': p_damageform,
}


# ---------------------------------------------------------------------------
# Sidmall
# ---------------------------------------------------------------------------
def header(ctx, active):
    items = []
    for n in NAV:
        cur = ' aria-current="page"' if (ctx.path == n['href']) else ''
        is_active = ' is-active' if active == n['id'] else ''
        if n.get('mega') == 'areas':
            cards = ''.join(f'''
            <a class="mega__card" href="{ctx.url(a['slug'])}">
              {swatch(a['pattern'], 'blue')}
              <h3>{a['title']}</h3>
              <p>{a['short']}</p>
            </a>''' for a in AREAS)
            items.append(f'''
        <li class="nav__item nav__item--drop{is_active}">
          <a class="nav__link" href="{ctx.url(n['href'])}" aria-expanded="false" aria-haspopup="true"{cur}>{n['label']}<span class="nav__caret" aria-hidden="true"></span></a>
          <div class="mega">
            <div class="wrap mega__inner">
              <div class="mega__intro">
                <span class="eyebrow">Affärsområden</span>
                <p>Tre affärsområden med ett gemensamt ansvar: att leverera en högkvalitativ produkt till bästa möjliga pris.</p>
                <a class="link-arrow" href="{ctx.url(n['href'])}"><span>Översikt</span>{arrow()}</a>
              </div>{cards}
            </div>
          </div>
        </li>''')
        elif n.get('mega') == 'company':
            cards = ''.join(f'''
            <a class="mega__card" href="{ctx.url(c['href'])}">
              {swatch(c['pattern'], 'blue')}
              <h3>{c['title']}</h3>
              <p>{c['text']}</p>
            </a>''' for c in COMPANY_LINKS)
            items.append(f'''
        <li class="nav__item nav__item--drop{is_active}">
          <a class="nav__link" href="{ctx.url(n['href'])}" aria-expanded="false" aria-haspopup="true"{cur}>{n['label']}<span class="nav__caret" aria-hidden="true"></span></a>
          <div class="mega">
            <div class="wrap mega__inner">
              <div class="mega__intro">
                <span class="eyebrow">Företaget</span>
                <p>AMT Bygg – Tillsammans. Starka relationer och ett samarbete byggt på förtroende och respekt.</p>
                <a class="link-arrow" href="{ctx.url('kontakt/')}"><span>Kontakta oss</span>{arrow()}</a>
              </div>{cards}
            </div>
          </div>
        </li>''')
        else:
            items.append(f'<li class="nav__item{is_active}"><a class="nav__link" href="{ctx.url(n["href"])}"{cur}>{n["label"]}</a></li>')

    mobile_items = []
    for i, n in enumerate(NAV):
        mobile_items.append(f'<li><a href="{ctx.url(n["href"])}">{n["label"]}<small>{i + 1:02d}</small></a></li>')
        if n.get('mega') == 'areas':
            mobile_items.append('<li class="sub"><ul>' + ''.join(f'<li><a href="{ctx.url(a["slug"])}">{a["title"]}</a></li>' for a in AREAS) + '</ul></li>')
        if n.get('mega') == 'company':
            mobile_items.append('<li class="sub"><ul>' + ''.join(f'<li><a href="{ctx.url(c["href"])}">{c["title"]}</a></li>' for c in COMPANY_LINKS[1:]) + '</ul></li>')
    mobile_items.append(f'<li><a href="{ctx.url("anmal-skada/")}">Anmäl skada<small>{len(NAV) + 1:02d}</small></a></li>')

    return f'''
<a class="skip-link" href="#main">Hoppa till innehållet</a>
<div class="utility">
  <div class="wrap">
    <ul class="utility__list">
      <li class="utility__hide-sm">Huvudkontor {COMPANY['city']}</li>
      <li><a href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a></li>
      <li class="utility__hide-sm"><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a></li>
    </ul>
    <ul class="utility__list utility__hide-sm">
      <li><a href="{ctx.url('karriar/')}">Karriär</a></li>
      <li><a class="utility__alert" href="{ctx.url('anmal-skada/')}">Anmäl skada</a></li>
    </ul>
  </div>
</div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{ctx.url('')}" aria-label="AMT Bygg – till startsidan">
      <img class="brand__dark" src="{ctx.asset('brand/amt-bygg-logo.svg')}" alt="AMT Bygg" width="170" height="22">
      <img class="brand__light" src="{ctx.asset('brand/amt-bygg-logo-white.svg')}" alt="AMT Bygg" width="170" height="22">
    </a>
    <nav class="nav" aria-label="Huvudmeny">
      <ul class="nav__list">{''.join(items)}
      </ul>
    </nav>
    <a class="btn btn--gold btn--sm header-cta" href="{ctx.url('anmal-skada/')}">Anmäl skada</a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="Öppna meny"><span></span><span></span><span></span></button>
  </div>
</header>
<div class="mobile-nav" id="mobile-nav" aria-hidden="true" inert>
  <div class="pattern pat-wood pat--blue"></div>
  <ul>{''.join(mobile_items)}</ul>
  <div class="mobile-nav__foot">
    <a href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a><br>
    <a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a><br>
    {COMPANY['street']}, {COMPANY['zip']} {COMPANY['city']}
  </div>
</div>'''


def footer(ctx):
    areas = ''.join(f'<li><a href="{ctx.url(a["slug"])}">{a["title"]}</a></li>' for a in AREAS)
    return f'''
<footer class="site-footer">
  <div class="pattern pat-wood pat--blue pattern--fade-l" style="right:0"></div>
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-brand">
        <img src="{ctx.asset('brand/amt-bygg-logo-white.svg')}" alt="AMT Bygg" width="220" height="29" loading="lazy">
        <div class="tagline">TILLSAMMANS</div>
        <p>Ett modernt byggbolag med starka traditioner. Skadereparationer, lokalanpassningar och entreprenad i Göteborgsregionen.</p>
        <div class="footer-badges">
          <a href="https://www.di.se/amnen/di-gasell/" target="_blank" rel="noopener" aria-label="Di Gasell 2025"><img src="{ctx.asset('logos/gasell-2025.png')}" alt="Di Gasell 2025" loading="lazy"></a>
          <a href="{ctx.url('om-oss/ledningssystem/')}" aria-label="Certifierade i Povel" style="padding:6px"><img src="{ctx.asset('logos/povel.png')}" alt="Povel – processorienterad verksamhetsledning" style="height:54px" loading="lazy"></a>
        </div>
      </div>
      <div class="footer-col">
        <h2>Affärsområden</h2>
        <ul class="list">{areas}<li><a href="{ctx.url('anmal-skada/')}">Anmäl skada</a></li></ul>
      </div>
      <div class="footer-col">
        <h2>Företaget</h2>
        <ul class="list">
          <li><a href="{ctx.url('om-oss/')}">Om oss</a></li>
          <li><a href="{ctx.url('om-oss/ledningssystem/')}">Ledningssystem</a></li>
          <li><a href="{ctx.url('klienter/')}">Klienter</a></li>
          <li><a href="{ctx.url('partners/')}">Partners</a></li>
          <li><a href="{ctx.url('karriar/')}">Karriär</a></li>
        </ul>
      </div>
      <div class="footer-col footer-col--wide">
        <h2>Kontakt</h2>
        <address>
          <a href="tel:{COMPANY['phone_href']}">{COMPANY['phone']}</a><br>
          <a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a><br><br>
          <a href="{COMPANY['maps']}" target="_blank" rel="noopener">Huvudkontor<br>{COMPANY['street']}<br>{COMPANY['zip']} {COMPANY['city']}</a>
        </address>
      </div>
      <div class="footer-col">
        <h2>Fakturering</h2>
        <address>{COMPANY['legal']}<br>Org.nr {COMPANY['orgnr']}<br><a href="mailto:{COMPANY['invoice_email']}">{COMPANY['invoice_email']}</a></address>
      </div>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="wrap">
      <span>© <span data-year>{date.today().year}</span> {COMPANY['legal']}</span>
      <ul class="list">
        <li><a href="{ctx.url('integritetspolicy/')}">Integritetspolicy</a></li>
        <li><a href="https://se.trustpilot.com/review/amtgroup.se" target="_blank" rel="noopener">Omdömen på Trustpilot</a></li>
        <li><a href="{ctx.asset('files/AMT-Bygg.vcf')}" download>Spara som kontakt</a></li>
      </ul>
    </div>
  </div>
</footer>'''


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
    body_cls = ' class="has-hero"' if meta.get('hero') else ''
    og_img = SITE_URL + '/assets/img/' + meta.get('og', 'hero-goteborg') + '-1280.jpg'
    robots = '<meta name="robots" content="noindex">' if meta.get('noindex') else ''
    ld = f'<script type="application/ld+json">{jsonld(meta)}</script>' if meta['path'] == '' else ''
    return f'''<!doctype html>
<html lang="sv" class="no-js">
<head>
<meta charset="utf-8">
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
<meta name="theme-color" content="#12161f">
<link rel="icon" href="{ctx.asset('brand/favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{ctx.asset('brand/favicon-32.png')}" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{ctx.asset('brand/apple-touch-icon.png')}">
<link rel="preload" href="{ctx.asset('fonts/Sora-normal-300_700.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{ctx.asset('fonts/HankenGrotesk-normal-300_700.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{ctx.asset('css/fonts.css')}">
<link rel="stylesheet" href="{ctx.asset('css/patterns.css')}">
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
    html = re.sub(r'\{\{swatch\s+([^}]+)\}\}', lambda m: swatch(*[x.strip() for x in m.group(1).split('|')]), html)
    html = html.replace('{{arrow}}', arrow())
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
