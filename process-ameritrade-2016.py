#!/usr/bin/python

# In Ubuntu or Fedora, pdftotext is part of the poppler-utils package.
# Take the PDF file containing Form 1099-B and run these commands:
# pdftotext -layout 1099-b.pdf 1099-b.txt
# python process-ameritrade-2016.py 1099-b.txt > 1099-b.csv
# python create-txf-2015.py 1099-b.csv > 1099-b.txf

import re
import sys

with open(sys.argv[1]) as f:
    content = [x.strip('\n') for x in f.readlines()]

# The format for covered tax lot and noncovered tax lots is slightly different.
covered_columns = (0, 31, 58, 78, 91, 108, 133, 156)
noncovered_columns = (0, 26, 52, 78, 93, 109, 135, 160)
columns = covered_columns

def splitLine(line, columns):
    ncol = len(columns)
    entries = []
    for i in xrange(ncol):
        end = len(line) if i == ncol - 1 else columns[i + 1]
        entry = line[columns[i]:end]
        entry = entry.strip().replace(',', '')
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
    if line.find(' COVERED TAX LOTS') >= 0:
        columns = covered_columns
    elif line.find(' NONCOVERED TAX LOTS') >= 0:
        columns = noncovered_columns
    if line.startswith('1a- Description of property/CUSIP/Symbol'):
        state = 1
        continue
    if line.startswith(' Totals :') or line.startswith('* This is important tax information'):
        state = 0
        continue
    if not state or not line:
        continue
    if state < 4:
        state += 1
        continue
    if state == 4:
        if line.startswith(' '):
            continue
        #print line
        pos1 = line.index(' / CUSIP: ');
        pos2 = line.index(' / Symbol:', pos1)
        pos3 = pos2 + len(' / Symbol: ')
        symbol = line[pos3:]
        if not symbol:
            pos3 = pos1 + len(' / CUSIP: ')
            symbol = line[pos3:pos2]
        pending = [line[:pos1], symbol]
        state = 5
        continue
    # state == 5
    records.append(pending + splitLine(line, columns) + [box])
    state = 4

records.sort(key=lambda r: r[1])
pat = re.compile(r'( [PC])( [0-9.]+)0$')
for r in records:
    match = re.search(pat, r[1])
    if match:
        r[1] = r[1][:match.start(1)] + match.group(2) + match.group(1)
    net_proceeds = ''
    if r[4].endswith(' N'):
        net_proceeds = 'Net proceeds'
        r[4] = r[4][:-2]
    code = r[9]
    #print r[3]
    count = float(r[3])
    if code.lower().find('short') >= 0:
        count = -count
    # These codes do not get used elsewhere. I just set them to make the
    # Ameritrade output more similar to the Schwab output.
    if code == 'Short sale closed- option':
        code = 'BC'
    elif code == 'Option expiration short position' or code == 'Option expiration':
        code = 'X'
    adj = r[7]
    if adj == '...':
        adj = '--'
    # From the instructions of TD Ameritrade Form 1099-B:
    # Column 1f. Shows W for wash sale, C for collectibles, or D for market discount.
    # Column 1g. Shows the amount of nondeductible loss in a wash sale
    # transaction or the amount of accrued market discount. When the sale of a
    # debt instrument is a wash sale and has accrued market discount, code W
    # will be in column 1f and the amount of the wash sale loss disallowed will
    # be in column 1g. For details on wash sales and market discount, see
    # Schedule D (Form 1040) instructions and Pub. 550.
    # One of Column 1f and 1g is in "adj" but I don't know which one (no example).
    print '%s,%g,%s,%s,%s,%s,%s,%s,,,%s,%s,%s,%s' % (r[1], count, r[5], r[2], r[4], r[6], adj, r[8], r[10], code, r[0], net_proceeds)
