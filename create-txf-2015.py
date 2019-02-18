#!/usr/bin/python

# Creates a TXF file for Form 1099-B to populate Form 8949.
# https://turbotax.intuit.com/txf/TXF042.jsp
# Look for codes 321, 711, 712, 323, 713, 714.

# python create-txf-2015.py 1099-b.csv > 1099-b.txf
# If you have multiple accounts, you may combine the .csv files by
# sorting them before creating the .txf file from the combined file.

# Import the .txf file into TurboTax via 
# "File > Import > From TXF Files".
# You should see this:
# These Documents Are Now Ready for Import:
# - 1099-B (number of transactions)

# The result DOES NOT look correct in in EasyView.  You can verify it
# like this: "View > Go to Forms". Open "Form 8949". Review the
# transactions. Note that Line 1 in both Part I and II is scrollable
# if you have more than six transactions.  Also, there are multiple
# copies of the form if more than one of A, B, C or D, E, F is
# checked.

# If you don't like what you see, you can remove the imported data via
# "File > Remove Imported Data".

import sys
import csv
import datetime

box_dict = {'A': 321, 'B': 711, 'C': 712, 'D': 323, 'E': 713, 'F': 714}
# Only two taxrefs for wash sales are documented in Section IV.  One
# of those is used in Example 2C.  Example 2G for a long-term wash
# sale uses taxref 713.
wash_box_dict = {'A': 682, 'B': 718, 'C': 712, 'D': 323, 'E': 713, 'F': 714}

print('V042')
print('Aself')
print('D', datetime.date.today().strftime('%m/%d/%y'))
print('^')

with open(sys.argv[1], 'r') as csvfile:
    for row in csv.reader(csvfile):
        symbol = row[0]
        count = row[1]
        acquired = row[2]
        disposed = row[3]
        proceeds = row[4]
        try:
            # TXF042.jsp, example 2B; may be reported as "Missing" in 1099-B.
            float(row[5])
            base = row[5]
        except ValueError:
            base = ''
        adj = row[6]
        gain = row[7]
        adj_code = row[9]
        box = row[10]
        taxref = wash_box_dict[box] if adj_code == 'W' else box_dict[box]
        prefix = ' '
        if '/' in symbol:
            prefix = ' opt '
        else:
            prefix = ' sh '
        if float(count) < 0:
            prefix = ' short' + prefix
            count = count[1:]
            # https://www.irs.gov/pub/irs-pdf/i8949.pdf
            # Column (b)-Date Acquired
            # For a short sale, enter the date you acquired the property
            # delivered to the broker or lender to close the short sale.
            acquired = disposed
        descr = count + prefix + symbol
        print('TD')
        print('N' + str(taxref))
        print('P ' + descr)
        print('D ' + acquired.replace('VARIOUS', 'Various'))
        print('D ' + disposed)
        print('$' + base)
        print('$' + proceeds)
        # TurboTax 2016 ignores the sign of the adjustment and always puts "W"
        # in Box (f) if an adjustment is present.  For other types of
        # adjustments, e.g., "B", one has to override the values in Form 8949
        # in Forms View, including the new value in Box (h).
        if adj != '--' and adj != '0.00':
            print('$' + adj)
        print('^')

