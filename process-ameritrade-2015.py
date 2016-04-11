#!/usr/bin/python

# In Fedora, pdftotext is part of the poppler-utils package.
# Take the PDF file containing Form 1099-B and run these commands:
# pdftotext -layout 1099-b.pdf 1099-b.txt
# python process-ameritrade-2015.py 1099-b.txt > 1099-b.csv
# python create-txf-2015.py 1099-b.csv > 1099-b.txf

import re
import sys

with open(sys.argv[1]) as f:
    content = [x.strip('\n') for x in f.readlines()]

columns = (0, 32, 58, 80, 93, 108, 133, 156)

def splitLine(line, columns):
    ncol = len(columns)
    entries = []
    for i in xrange(ncol):
        end = len(line) if i == ncol - 1 else columns[i + 1]
        entry = line[columns[i]:end]
        entry = entry.strip()
        entries.append(entry)
    return entries

box = 'A'
pat = re.compile(r'Box ([A-F]) checked')
records = []
state = 0
for line in content:
    match = re.search(pat, line)
    if match:
        box = match.group(1)
    if line.startswith('1a- Description of property/CUSIP/Symbol'):
        state = 1
        continue
    if line.startswith(' Totals :') or line.startswith('* This is important tax information'):
        state = 0
        continue
    if not state or not line:
        continue
    if state < 3:
        state += 1
        continue
    if state == 3:
        #print line
        pos1 = line.index(' / CUSIP: /');
        pos2 = line.index(' / Symbol: ', pos1)
        pos2 += len(' / Symbol: ')
        pending = [line[:pos1], line[pos2:]]
        state = 4
        continue
    records.append(pending + splitLine(line, columns) + [box])
    state = 3

records.sort(key=lambda r: r[1])
pat = re.compile(r'( [PC])( [0-9.]+)0$')
for r in records:
    match = re.search(pat, r[1])
    if match:
        r[1] = r[1][:match.start(1)] + match.group(2) + match.group(1)
    code = r[9]
    count = float(r[3])
    if code.lower().find('short') >= 0:
        count = -count
    if code == 'Short sale closed- option':
        code = 'BC'
    elif code == 'Option expiration short position' or code == 'Option expiration':
        code = 'X'
    adj = r[7]
    if adj == '...':
        adj = '--'
    print '%s,%g,%s,%s,%s,%s,%s,%s,,%s,%s,%s' % (r[1], count, r[5], r[2], r[4], r[6], adj, r[8], r[10], code, r[0])
