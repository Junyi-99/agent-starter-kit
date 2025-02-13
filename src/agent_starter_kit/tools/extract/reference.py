import argparse
import logging
import re
from collections import Counter
from enum import Enum

import pymupdf


class ReferenceType(Enum):
    NUMBERED = (re.compile(r"\[\d+\].*(19|20)\d{2}(:?\.)"), "Numbered reference with year")
    AUTHOR_YEAR = (re.compile(r"^([A-Z][a-z]*.*)((19|20)\d{2}[a-z]?(:?\.)(:?\sdoi:.*\.)?|https?:\/\/\S+\.)"), "Author-year style")

    def __init__(self, pattern: re.Pattern, description: str):
        self.pattern = pattern
        self.description = description


r"""
^([A-Z][a-z]*.*) # Match author name starting with a capital letter
(19|20)\d{2}(:?\.)(:?\sdoi:.*\.)? # Match year/doi ending
|
https?:\/\/\S+\. # Match http ending
"""


def classify_reference_type(block_text: str) -> ReferenceType | None:
    """
    Determine the reference style of a block of text

    Args:
        block_text: str. The text to analyze

    Returns:
        ReferenceType | None. The reference type if found, None otherwise
    """
    block_text = block_text.replace("\n", " ").replace("- ", "").strip()
    for ref_type in ReferenceType:
        if ref_type.pattern.match(block_text):
            return ref_type
    return None


def is_ref_block(block_text: str):
    """
    Check if a block of text is a reference block (e.g. "参考文献", "Reference", "Bibliography")

    Args:
        block_text: str. The text to analyze

    Returns:
        bool. True if the block is a reference block, False otherwise
    """
    block_text = re.sub(r"\s+", "", block_text.lower())
    refbreak = re.compile(r"(\u53c2\u8003\u6587\u732e|reference|bibliography)")
    if len(block_text) > 20:
        return False
    ret = re.match(refbreak, block_text)
    return ret is not None


def get_ref_page(doc: pymupdf.Document):

    reference_page = -1

    for page in doc:

        blist = page.get_text("blocks")

        for block in blist:
            block_text = block[4]
            color = (1, 0, 0)
            rect = pymupdf.Rect(block[:4])

            page.draw_rect(rect, color=color)
            page.insert_textbox(rect=rect, buffer="Block", color=color, fontsize=5)

            if is_ref_block(block_text):
                reference_page = max(reference_page, page.number)

    return reference_page


def mark_and_collect_references(page: pymupdf.Page, hit_ref_block=False):
    blist = page.get_text("blocks", delimiters=None)  # make the word list
    refs = []
    for b in blist:  # scan through all words on page
        block_text = b[4].replace("\n", " ").replace("- ", "").strip()
        rect = pymupdf.Rect(b[:4])

        if not hit_ref_block:
            if is_ref_block(block_text):
                hit_ref_block = True
            page.draw_rect(rect, color=(0, 0, 1))
            continue

        if classify_reference_type(block_text) is None:  # Non reference
            page.draw_rect(rect, color=(0, 0, 1))
        else:  # Reference
            page.draw_rect(rect, color=(1, 0, 1))
            refs.append(block_text.strip().replace("\n", " ").replace("- ", "").replace("/ ", "/"))

    return hit_ref_block, refs


def count_references_on_page(page: pymupdf.Page, type: ReferenceType):
    """ """
    counter = 0
    for block in page.get_text("blocks"):
        block_text = block[4].replace("\n", " ").replace("- ", "")  # Block: (x,y,w,h,text,...,...)
        if type.pattern.match(block_text):
            counter += 1
    return counter


def get_all_refs(pdf_filepath: str, save_marked_pdf: bool = False) -> list[str] | None:
    """
    Extracts all references from a PDF file.
    This function processes a PDF file to identify and extract references from it. It identifies the reference section,
    determines the major reference type, and collects all references. Optionally, it can save a marked version of the PDF.
    Args:
        pdf_filepath (str): The path to the PDF file.
        save_marked_pdf (bool, optional): If True, saves a marked version of the PDF with references highlighted. Defaults to False.
    Returns:
        list[str] | None: A list of extracted references if found, otherwise None.
    """

    doc = pymupdf.open(pdf_filepath)

    ref_page_begin = get_ref_page(doc)
    if ref_page_begin == -1:
        print("No reference page found")
        return None

    hit_ref_block = False
    ref_counter: Counter = Counter()
    for page in doc[ref_page_begin : ref_page_begin + 2]:  # noqa: E203
        blist = page.get_text("blocks")
        for block in blist:
            if not hit_ref_block:
                if not is_ref_block(block[4]):
                    continue
                hit_ref_block = True

            block_text = block[4].replace("\n", " ").replace("- ", "")
            matches = [ref_type for ref_type in ReferenceType if ref_type.pattern.match(block_text)]
            ref_counter = ref_counter + Counter(matches)

    major_ref_type, _ = ref_counter.most_common(1)[0]

    hit_ref_block = False
    ref_page_end = -1
    all_refs = []
    for page in doc[ref_page_begin:]:
        refcnt = count_references_on_page(page, major_ref_type)
        logging.debug(f"Page {page.number+1} with refcnt {refcnt}")
        if refcnt == 0 and ref_page_end != -1:
            ref_page_end = max(ref_page_begin, page.number - 1)
            break
        if refcnt != 0:
            ref_page_end = page.number

        hit_ref_block, refs = mark_and_collect_references(page, hit_ref_block)  # mark the page's words

        blockcnt = len(page.get_text("blocks"))
        if refcnt / blockcnt < 0.05:
            continue

        all_refs.extend(refs)

    print(f"Major Reference type: {major_ref_type}")
    print(f"Reference page range: {ref_page_begin+1} - {ref_page_end+1}")

    if save_marked_pdf:
        doc.save("marked-" + doc.name)

    all_refs_finegrained = []  # Sometimes [] references stick together and need further splitting
    if major_ref_type == ReferenceType.NUMBERED:
        for ref in all_refs:
            refs = ref.split("[")  # split by [ and add back the [
            for r in refs:
                if r.strip():
                    all_refs_finegrained.append("[" + r.strip())
    else:
        all_refs_finegrained = all_refs

    return all_refs_finegrained


if __name__ == "__main__":
    """
    Usage: python extract_reference.py filename.pdf
    """
    parser = argparse.ArgumentParser(description="Mark blocks in a PDF file")
    parser.add_argument("filename", help="PDF file to process")
    parser.add_argument("--begin", type=int, help="Start page", default=0)
    parser.add_argument("--end", type=int, help="End page", default=-1)
    args = parser.parse_args()

    refs = get_all_refs(args.filename)
    if refs is None:
        print("No references found, please check the PDF file")
        exit(1)
    print(f"Extracted {len(refs)} references")
    print(refs)
