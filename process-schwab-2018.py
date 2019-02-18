#!/usr/bin/python3

# In Ubuntu or Fedora, pdftotext is part of the poppler-utils package.
# Take the PDF file containing Form 1099-B and run these commands:
# pdftotext -enc UTF-8 -layout 1099-b.pdf 1099-b.txt
# python3 process-schwab-2018.py 1099-b.txt > 1099-b.csv
# python3 create-txf-2015.py 1099-b.csv > 1099-b.txf
# Make sure to enter a missing cost in TurboTax in Forms view.

import re
import sys

with open(sys.argv[1]) as f:
    content = [x.strip('\n') for x in f.readlines()]

# Start positions of the columns in the text file.
# This is the earliest position where the dollar symbol may appear.
# splitLines searches for it starting there.
columns1 = (0, 70, 78, 112, 132, 149, 172)
columns2 = (0, 70, 95, 130)

def splitLine(line, columns):
    columns = list(columns)
    ncol = len(columns)
    if ncol >= 7:
        for i in range(1, ncol):
            dollar = line.find('$', columns[i], columns[i] + 7)
            if dollar < 0 and (i == 4 or i == 5):
                dollar = line.find('--', columns[i], columns[i] + 30)
            if dollar >= 0:
                columns[i] = dollar
                for j in range(1, ncol - i):
                    columns[i + j] = max(columns[i + j], columns[i] + j)
    entries = []
    for i in range(ncol):
        end = len(line) if i == ncol - 1 else columns[i + 1]
        entry = line[columns[i]:end]
        if i > 0:
            dollar = entry.find('$')
            if dollar >= 0:
                entry = entry[dollar+1:]
        elif ncol >= 7:
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
    #print(entries)
    return entries

box = 'A'
pat = re.compile(r'Box ([A-F]) checked')
records = []
state = 0
for line in content:
    #print(state, line)
    if line.startswith('YEAR-END SUMMARY INFORMATION IS NOT PROVIDED TO THE IRS'):
        break
    if line.startswith('FATCA Filing Requirement'):
        continue
    match = re.search(pat, line)
    if match:
        box = match.group(1)
    if line.startswith('CUSIP Number / Symbol') or line.startswith('Security Subtotal'):
        # Security Subtotal now has 2 lines
        state = 1
        continue
    if line.startswith('Total ') or line.startswith('Please see the '):
        state = 0
        continue
    if not state or not line:
        state = 0
        continue
    if state == 1:
        state = 2
        continue
    if state == 2:
        pending = splitLine(line, columns1)
        state = 3
        continue
    pending2 = splitLine(line, columns2)
    pos = pending2[0].find(' / ')
    if pos > 0:
        symbol = pending2[0][pos+3:]
        if symbol:
            pending2[0] = symbol
        else:
            pending2[0] = pending2[0][:pos]
    records.append(pending + pending2 + [box])
    state = 2

records.sort(key=lambda r: r[8])
pat = re.compile(r'([0-9.,]+)(S?) .*')
pat2 = re.compile(r'/(20)\d\d ')
for r in records:
    #print(r)
    match = re.match(pat, r[0])
    # Remove thousand separator
    count = float(match.group(1).replace(',', ''))
    if match.group(2) == 'S':
        count = -count
    match2 = re.search(pat2, r[8])
    if match2:
        r[8] = r[8][:match2.start(1)] + r[8][match2.end(1):]
    # From the instructions of Charles Schwab Form 1099-B:
    # Box 1f. Shows W for wash sale, C for collectibles, or D for market discount.
    # Box 1g. Shows the amount of nondeductible loss in a wash sale
    # transaction or the amount of accrued market discount. When the
    # sale of a debt instrument is a wash sale and has accrued market
    # discount, code "W" will be in box 1f and the amount of the wash
    # sale loss disallowed will be in box 1g. For details on wash
    # sales and market discount, see Scheduled D (Form 1040)
    # instructions and Pub. 550.
    # r[4] contains the content of Box 1g and r[12] contains the contents of Box 1f.
    print('%s,%g,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (r[8], count, r[2], r[9], r[3], r[4], r[5], r[6], r[7], r[11], r[12], r[1], r[0], r[10]))
