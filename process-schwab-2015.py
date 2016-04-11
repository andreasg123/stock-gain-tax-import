#!/usr/bin/python

# In Fedora, pdftotext is part of the poppler-utils package.
# Take the PDF file containing Form 1099-B and run these commands:
# pdftotext -layout 1099-b.pdf 1099-b.txt
# python process-schwab-2015.py 1099-b.txt > 1099-b.csv
# python create-txf-2015.py 1099-b.csv > 1099-b.txf

import re
import sys

with open(sys.argv[1]) as f:
    content = [x.strip('\n') for x in f.readlines()]

# Start positions of the columns in the text file.
columns1 = (0, 70, 79, 113, 132, 152, 172)
columns2 = (0, 70)

def splitLine(line, columns):
    ncol = len(columns)
    entries = []
    for i in xrange(ncol):
        end = len(line) if i == ncol - 1 else columns[i + 1]
        entry = line[columns[i]:end]
        if i > 0:
            dollar = entry.find('$')
            if dollar >= 0:
                entry = entry[dollar+1:]
        elif len(columns) >= 7:
            # The position of the first two columns in the first row of a
            # transaction overlaps slightly in the conversion to text. The
            # second column only contains a single code without a space.
            entry = entry.rstrip()
            pos = entry.rfind(' ')
            if pos >= 0:
                entries.append(entry[:pos].strip())
                entry = entry[pos+1:]
        entry = entry.strip().replace(',', '')
        if entry.startswith('(') and entry.endswith(')'):
            # Schwab indicates negative numbers with parentheses.
            entry = '-' + entry[1:-1]
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
    if line.startswith('CUSIP Number / Symbol'):
        state = 1
        continue
    if line.startswith('Total ') or line.startswith('Please see the '):
        state = 0
        continue
    if not state or not line:
        continue
    if state == 1 or line.startswith('Security Subtotal'):
        state = 2
        continue
    if state == 2:
        pending = splitLine(line, columns1)
        state = 3
        continue
    records.append(pending + splitLine(line, columns2) + [box])
    state = 2

records.sort(key=lambda r: r[8])
pat = re.compile(r'([0-9.]+)(S?) .*')
pat2 = re.compile(r'/(20)\d\d ')
for r in records:
    match = re.match(pat, r[0])
    count = float(match.group(1))
    if match.group(2) == 'S':
        count = -count
    match2 = re.search(pat2, r[8])
    if match2:
        r[8] = r[8][:match2.start(1)] + r[8][match2.end(1):]
    print '%s,%g,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (r[8], count, r[2], r[9], r[3], r[4], r[5], r[6], r[7], r[10], r[1], r[0])
