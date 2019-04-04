#! /usr/local/bin/python3
import sys, os 
import argparse
import PyPDF2
from PyPDF2 import PdfFileWriter, PdfFileReader
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

__VERSION__ = '0.1'

def collate_scan(file_odds, file_evens):
    output = PdfFileWriter()

    odd_input = PdfFileReader(open(file_odds, "rb"))
    even_input = PdfFileReader(open(file_evens, "rb"))

    pages = min(odd_input.getNumPages(), even_input.getNumPages())

    for i in range(pages):
        output.addPage(odd_input.getPage(i))
        output.addPage(even_input.getPage(i))

    # Write to an output PDF document
    outputStream = open("merge-output.pdf", "wb")
    output.write(outputStream)

def insert_blank_pages(input_file, index, output_file=None):
    input_pdf = PdfFileReader(open(input_file,'rb'))
    output_pdf = PdfFileWriter()
    for i in range(input_pdf.numPages):
        output_pdf.addPage(input_pdf.pages[i])

    if not isinstance(index, list):
        index = [index]
    for idx in index:
        if idx is None:
            output_pdf.addBlankPage()
        else:
            output_pdf.insertBlankPage(index=idx)

    if output_file is None:
        output_file = input_file
    output_pdf.write(open(output_file, 'wb'))


def blank_page_pad(input_file, pad_multiple):
    input_pdf = PdfFileReader(open(input_file,'rb'))
    N = input_pdf.getNumPages()
    pages_to_add = [None]*(pad_multiple - N%pad_multiple)
    if len(pages_to_add) == pad_multiple:
        pages_to_add = []
    print('{:2} + {:1} = {:2} for {}'.format(N, len(pages_to_add), N+len(pages_to_add), input_file))
    new_file = input_file[:-4]+'_pad.pdf'
    insert_blank_pages(input_file, pages_to_add, new_file)
    return new_file

def concatenate_pdfs(infiles):
    output = PdfFileWriter()
    page_defined = False
    add_blank_beginning = False
    for infile in infiles:
        if infile == 'blank':
            if page_defined:
                output.addBlankPage()
            else:
                add_blank_beginning = True
        else:
            page_defined = True
            input_pdf = PdfFileReader(open(infile,'rb'))
            for i in range(input_pdf.numPages):
                output.addPage(input_pdf.pages[i])
    if add_blank_beginning:
        output.insertBlankPage(index=0)
    output.write(open('concat_result.pdf','wb'))

def extract(infile, start, end):
    start = int(start)
    end = int(end)
    output = PdfFileWriter()
    input_pdf = PdfFileReader(open(infile,'rb'))
    for i in range(start-1,end):
        output.addPage(input_pdf.pages[i])
    output.write(open( f"{infile[:-4]}_{start}_{end}.pdf",'wb'))

def quarter_page_book_pad(infiles):
    pad_files = [blank_page_pad(infile,8) for infile in infiles]
    concatenate_pdfs(pad_files)
    for file in pad_files:
        os.remove(file)


def half_page_bookify(input_file, output_file, add_back=False):
    """ Rearanges the pages of a PDF so that when it is printed
    double sided with two pages to a side, the print can just be
    cut in half or folded over.

    If the original pdf has pages 0 ... N-1, then we want to order
    the pages such that the output has pages
        N-1, 0, 1, N-2, N-3, 2, 3, N-4, N-5 ...  N/2
    """
    # =  (N-1)-0, 0, 1, (N-1)-1, (N-1)-2, 2, 3, (N-1)-3, (N-1)-4 ...  N/2
    # =     [-1],   [0],    [1],    [-2], |    [-3],    [2],    [3],    [-4], | [-5] ...  N/2
    # =  [-(0+1)], [0+0], [0+1], [-(0+2)],|  [-(2+1)], [2+0], [2+1], [-(2+2)],|
    # =  [-(i+1)], [i+0], [i+1], [-(i+2)] ... N/2

    input_pdf = PdfFileReader(open(input_file,'rb'))
    N = input_pdf.getNumPages()
    pages_to_add = [None]*(4 - N%4)
    if len(pages_to_add) == 4:
        pages_to_add = []
    if add_back:
        if len(pages_to_add) == 0:
            pages_to_add = [None]*4
        pages_to_add[0] = 1
    insert_blank_pages(input_file, pages_to_add, 'tmp.pdf')

    input_pdf = PdfFileReader(open('tmp.pdf','rb'))
    N = input_pdf.getNumPages()
    
    output_pdf = PdfFileWriter()
    pages = N//2
    for i in range(0,pages,2):
        output_pdf.addPage(input_pdf.getPage(N-(i+1)))
        output_pdf.addPage(input_pdf.getPage(  (i+0)))
        output_pdf.addPage(input_pdf.getPage(  (i+1)))
        output_pdf.addPage(input_pdf.getPage(N-(i+2)))

    outputStream = open(output_file, "wb")
    output_pdf.write(outputStream)
    os.remove('tmp.pdf')

def download_pdfs(index):
    req = requests.get(index)
    soup = BeautifulSoup(req.text, 'html.parser')

    for link in soup.find_all('a'):
        if '.pdf' in link.get('href').lower():
            full_link = urljoin(index,link.get('href'))
            r = requests.get(full_link)
            with open(link.get('href'), 'wb') as f:
                f.write(r.content)

def cut_margins(input_file, output_file):
    input_pdf = PdfFileReader(open(input_file,'rb'))
    output_pdf = PdfFileWriter()
    for i in range(input_pdf.numPages):
        page = input_pdf.pages[i]
        lowleft = page.cropBox.lowerLeft
        topright = page.cropBox.upperRight
        width = topright[0] - lowleft[0]
        height = topright[1] - lowleft[1]
        margin_percent = 0.07
        w_margin_left = lowleft[0] + margin_percent*width
        w_margin_right = topright[0] - margin_percent*width
        h_margin_low = lowleft[1] + (margin_percent+0.03)*width
        h_margin_top = topright[1] - (margin_percent)*width
        dims = PyPDF2.generic.RectangleObject([w_margin_left, h_margin_low, w_margin_right, h_margin_top])
        page.artBox = dims
        page.trimBox = dims
        page.mediaBox = dims
        page.cropBox = dims
        output_pdf.addPage(page)

    outputStream = open(output_file, "wb")
    output_pdf.write(outputStream)


def stripify(input_file, output_file):
    input_pdf = PdfFileReader(open(input_file,'rb'))
    input_pdf2 = PdfFileReader(open(input_file,'rb'))
    output_pdf = PdfFileWriter()
    for i in range(input_pdf.numPages):
        page = input_pdf.pages[i]
        # print(f'crop={page.cropBox},{page.cropBox.lowerLeft},{page.cropBox.lowerRight},{page.cropBox.upperLeft},{page.cropBox.upperRight}')
        lowleft = page.cropBox.lowerLeft
        topright = page.cropBox.upperRight
        w_center = (topright[0] + lowleft[0])/2
        
        dims1 = PyPDF2.generic.RectangleObject([*lowleft, w_center, topright[1] ])
        dims2 = PyPDF2.generic.RectangleObject([w_center, lowleft[1], *topright ])
        page.artBox = dims1
        page.trimBox = dims1
        page.mediaBox = dims1
        page.cropBox = dims1
        output_pdf.addPage(page)

        page = input_pdf2.pages[i]
        page.artBox = dims2
        page.trimBox = dims2
        page.mediaBox = dims2
        page.cropBox = dims2
        output_pdf.addPage(page)

    outputStream = open(output_file, "wb")
    output_pdf.write(outputStream)

def main():
    parser = argparse.ArgumentParser(description='Some useful PDF tools.')
    parser.add_argument('-V','--version', action="version", version=__VERSION__)

    parser.add_argument('-b','--bookify', type=str, nargs=2, metavar=('input','output'),
                        help='Rearange input file so it can be a little book')
    parser.add_argument('-c','--collate', type=str, nargs=2, metavar=('odd_pages','even_pages'),
                        help='Collate odd and even scanned pages')
    parser.add_argument('-q','--quarter-note', type=str, nargs='+', metavar='input_pdfs',
                        help='Rearrange input file for a quarter page book')
    parser.add_argument('-x','--concat', type=str, nargs='+', metavar='input_pdfs',
                        help='Concatenate PDFs')
    parser.add_argument('-d','--download', type=str, nargs=1, metavar='index_url',
                        help='Downloads PDFs linked to on webpage')
    parser.add_argument('-e','--extract', type=str, nargs=3, metavar=('input','start','end'),
                        help='Extract pages from pdf')
    parser.add_argument('-m','--margins', type=str, nargs=2, metavar=('input','output'),
                        help='Remove margins of research paper')
    parser.add_argument('-s','--strip', type=str, nargs=2, metavar=('input','output'),
                        help='Slice pdf pages in half')
    args = parser.parse_args()
    if args.collate:
        collate_scan(*args.collate)

    if args.bookify:
        half_page_bookify(*args.bookify)

    if args.quarter_note:
        quarter_page_book_pad(args.quarter_note)

    if args.concat:
        concatenate_pdfs(args.concat)

    if args.download:
        download_pdfs(*args.download)

    if args.extract:
        extract(*args.extract)

    if args.margins:
        cut_margins(*args.margins)

    if args.strip:
        stripify(*args.strip)

if __name__ == '__main__':
    main()