"""One-time import of this Markdown table format; never alters the source."""
import json, re, sys
from datetime import datetime, timedelta
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).read_text()
(root/'data/source-logbook.md').write_text(source)
coffees, shots = [], []
as_of = re.search(r'\bas of (\d{1,2} [A-Za-z]+ \d{4})\b', source, re.I)
history_end = datetime.strptime(as_of.group(1), '%d %B %Y').date() if as_of else datetime.now().date()
for section in source.split('\n## ')[1:]:
    title, _, body = section.partition('\n')
    if '| Dose |' not in body: continue
    cid = f'coffee-{len(coffees)+1}'
    roast = re.search(r'Roast date: (.+?)\.', body)
    notes = '\n'.join(line for line in body.splitlines() if not line.startswith('|')).strip()
    coffees.append(dict(id=cid, name=title, notes=notes, roast_date=roast.group(1) if roast else '', revision=1))
    section_shots = []
    for line in body.splitlines():
        if not line.startswith('|') or '| Dose |' in line or '| ---' in line: continue
        cells = [x.strip().replace('**','') for x in line.strip('|').split('|')]
        if len(cells)==6 and cells[0]=='Next optional test': cells = cells[1:]
        if len(cells)!=5: continue
        dose, grind, paper, temp, note = cells
        planned = note.startswith('Next') or 'Next optional test' in line
        def num(pattern, text):
            m=re.search(pattern,text)
            return float(m.group(1)) if m else None
        # Only extract unambiguous measurements. Full source wording remains alongside them.
        section_shots.append(dict(id=f'import-{len(shots)+len(section_shots)+1}',coffee_id=cid,revision=1,date='',
            dose=num(r'^(\d+(?:\.\d+)?) g$',dose),grind='' if grind=='—' else grind,
            paper={'Yes':'yes','No':'no'}.get(paper,'unknown'),temp=temp if temp in ['0','I','II'] else '',
            yield_g=num(r'/ (\d+(?:\.\d+)?) g out',note) if not planned else None,
            seconds=num(r'^~?(\d+(?:\.\d+)?) s',note) if not planned else None,
            first_drip=None,pressure='',basket='IMS double',puck_screen='unknown',
            status='planned' if planned else 'logged',reference=('reference' in note or 'locked, ideal' in note) and not planned,
            taste=note,source=line))
    # The source tables are chronological but lack per-shot dates. Give their
    # records consecutive dates ending at the source's stated snapshot date.
    for offset, shot in enumerate(section_shots):
        shot['date'] = str(history_end - timedelta(days=len(section_shots)-offset-1))
    shots.extend(section_shots)
(root/'data/seed.json').write_text(json.dumps(dict(coffees=coffees,shots=shots),ensure_ascii=False,indent=2))
print(f'Imported {len(coffees)} coffees, {sum(s["status"]=="logged" for s in shots)} logged entries, {sum(s["status"]=="planned" for s in shots)} planned tests.')
