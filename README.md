# AMT Bygg – webbplats

Statisk webbplats för AMT Bygg (amtgroup.se). Ingen server eller databas krävs – alla filer kan laddas upp till valfritt webbhotell (Netlify, Vercel, GitHub Pages, Loopia, One.com m.fl.).

## Bygga

```bash
python3 src/build.py           # skriver sidorna till repots rot
python3 -m http.server 8000    # förhandsvisa på http://localhost:8000
```

Kräver Python 3 med Pillow (för bildmått). `python3 src/patterns.py` genererar om mönsterbiblioteket.

## Struktur

| Sökväg | Innehåll |
| --- | --- |
| `src/pages/*.html` | Sidornas innehåll (redigera här, inte i de byggda filerna) |
| `src/build.py` | Sidmall, meny, sidfot, klienter, partners, ramavtal och kontaktuppgifter |
| `src/patterns.py` | Materialmönster i loggans färger: träådring, fiskben, regelverk, tegel, snitt, rutnät |
| `assets/` | CSS, JS, typsnitt (lokalt hostade), bilder, logotyper, vCard |

Klienter, partners och försäkringsbolag läggs till i listorna `CLIENTS`, `PARTNERS` och `INSURERS` i `src/build.py` (logotyp i `assets/logos/<id>.png`).

## Formulär

Formulären öppnar idag ett förifyllt mejl till amtbygg@amtgroup.se. För att skicka direkt från sidan, sätt `FORM_ENDPOINT_CONTACT` och `FORM_ENDPOINT_DAMAGE` i `src/build.py` till t.ex. en Formspree-URL och bygg om.

## Omdirigering

Gamla adressen `/skadereparation` pekar vidare till `/anmal-skada/`.
