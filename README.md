# Import Stock and Option Trades into TurboTax for U.S. Tax Filing

Brokerage companies report information on stock and option trades on
[Form 1099-B](https://www.irs.gov/pub/irs-pdf/i1099b.pdf) for U.S. tax
filing.  Copying data by hand for dozens of stock or option trades is
tedious and error-prone.  TurboTax (and maybe other tax preparation
software) supports the [TXF
format](https://www.thebalance.com/what-is-txf-1293734) for [importing 
data](https://ttlc.intuit.com/questions/1899278-how-do-i-import-from-the-txf-file)
from Form 1099-B.  Unfortunately, neither Charles Schwab nor TD
Ameritrade provide a TXF file.  They only provide a PDF file
containing Form 1099-B.

## Update for 2018

There were minor layout changes in the PDF files.  For TD Ameritrade, that
required searching for spaces to get column boundaries.  Also, scripts have
been updated for Python 3.  That requires specifying UTF-8 encoding for
pdftotext.

## Update for 2017

The format of the PDF files again changed slightly from the previous year.

## Update for 2016

Charles Schwab now provides a CSV file but it doesn't refer to stocks by
symbol, my preferred way of reporting capital gains.  The format of the PDF
files changed slightly from the previous year.  Brokerage companies now report
Box 6 of Form 1099-B (net proceeds) but that doesn't seem to make a difference
for TXF files.  The TXF spec was last updated in 2011 so that there are no
changes for creating TXF.

## Convert the PDF File to CSV

First, the PDF file has to be converted to text using pdftotext (part of the
poppler-utils package in Ubuntu or Fedora).  On a Mac, you can install it with
HomeBrew:

    brew cask install pdftotext

If you use a different application, you have to verify that the columns
specified in process-schwab-2018.py are still correct.

    pdftotext -enc UTF-8 -layout 1099-b.pdf 1099-b.txt

Next, the python script for the respective brokerage company parses the text
file into comma-separated values.  Option symbols are normalized.  Negative
counts indicate short sales.

    python3 process-schwab-2018.py 1099-b.txt > 1099-b.csv
    python3 process-ameritrade-2018.py 1099-b.txt > 1099-b.csv

The CSV file can be edited with a text editor or Microsoft Excel to make
changes such as replacing a CUSID with a symbol after a merger, adding a cost
basis not provided by the brokerage company, or changing Form 8949 Box B to
Box E from short-term to long-term.

## Convert CSV to TXF

The python script converts CSV to TXF:

    python3 create-txf-2018.py 1099-b.csv > 1099-b.txf

If you have multiple accounts, you may combine the .csv files by sorting them
before creating the .txf file from the combined file.

    sort account1.csv account2.csv account3.csv > combined.csv

## Import into TurboTax

Import the .txf file into TurboTax via "File > Import > From TXF Files".  You
should see this:

These Documents Are Now Ready for Import:

- 1099-B (number of transactions)

The result **does not** look correct in in EasyView.  You can verify it like
this: "View > Go to Forms".  Open [Form
8949](https://www.irs.gov/pub/irs-pdf/i8949.pdf).  Review the transactions.  Note
that Line 1 in both Part I and II is scrollable if you have more than six
transactions.  Also, there are multiple copies of the form if more than one of
A, B, C or D, E, F is checked.  While in Forms View, you can also update the
transactions, for example, if the brokerage company did not report the cost
(Box B or E), or if you have to complete columns (f) and (g).

If you don't like what you see, you can remove the imported data via
"File > Remove Imported Data".  If you overrode any values, you should undo
that before removing the imported data because the override will affect the
next import.  Also, overrides remain by position in the form so that it is best
to undo all overrides before removing any of several imported TXF files.

## Wash sales

Wash sales are not tested because I don't have any examples for it.  However,
when attempting a different adjustment, the result was correct for a wash sale
(just not for the intended adjustment).

## Other adjustments

TurboTax ignores the sign of the adjustment in the TXF file and always
puts "W" in Box (f) if an adjustment is present.  For other types of
adjustments, e.g., "B", one has to override the values in Form 8949 in Forms
View, including the new value in Box (h).
