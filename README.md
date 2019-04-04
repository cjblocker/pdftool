# pdftool

A little commandline tool to do all of the common things I do to pdfs, like concatenate, collate, reorder, etc.

## Usage

```bash
$ pdftool --help
usage: pdftool [-h] [-V] [-b input output] [-c odd_pages even_pages]
               [-q input_pdfs [input_pdfs ...]]
               [-x input_pdfs [input_pdfs ...]] [-d index_url]
               [-e input start end] [-m input output] [-s input output]

Some useful PDF tools.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -b input output, --bookify input output
                        Rearange input file so it can be a little book
  -c odd_pages even_pages, --collate odd_pages even_pages
                        Collate odd and even scanned pages
  -q input_pdfs [input_pdfs ...], --quarter-note input_pdfs [input_pdfs ...]
                        Rearrange input file for a quarter page book
  -x input_pdfs [input_pdfs ...], --concat input_pdfs [input_pdfs ...]
                        Concatenate PDFs
  -d index_url, --download index_url
                        Downloads PDFs linked to on webpage
  -e input start end, --extract input start end
                        Extract pages from pdf
  -m input output, --margins input output
                        Remove margins of research paper
  -s input output, --strip input output
                        Slice pdf pages in half
```

