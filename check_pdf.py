# import pymupdf
import pikepdf
import argparse
import sys


def open_pdf_pymupdf(file_path):
    try:
        return pymupdf.open(file_path)
    except Exception as e:
        print(f"Error opening PDF file: {e}")
        sys.exit(1)

def open_pdf_pikepdf(file_path):
    try:
        return pikepdf.Pdf.open(file_path)
    except Exception as e:
        print(f"Error opening PDF file: {e}")
        sys.exit(1)

def check_pdf_accessibility_pymupdf(file_path):
    """Check if a PDF is tagged for accessibility."""
    doc = open_pdf_pymupdf(file_path)
    # Check if tagged
    is_tagged = doc.is_pdf
    print(f"PDF is tagged: {is_tagged}")
    if not is_tagged:
        return False

    print("PDF Metadata:")
    print(doc.metadata)
    catalog_xref = doc.pdf_catalog()
    catalog = doc.xref_object(catalog_xref, compressed=True)
    print("PDF Catalog:")
    print(catalog)

def get_kids(page):
    """Recursively get all kids of a page."""
    kids = []
    if "/Kids" in page:
        for kid in page["/Kids"]:
            kids.append(kid)
            kid_obj = kid.get_object()
            kids.extend(get_kids(kid_obj))
    return kids

def check_for_image_only_content(page):
    """Check if a page contains only images."""
    resources = page.get("/Resources", {})
    fonts = resources.get("/Font", {})
    if not fonts:
        print("No fonts found on this page; it may be image-only.")
        return True
    return False

def check_for_image_only_pages(pdf):
    """Check all pages for image-only content."""
    if "/Pages" not in pdf.Root:
        print("No /Pages found in PDF.")
        raise ValueError("Invalid PDF structure: No /Pages found.")
    image_only_pages = []
    pages = pdf.pages
    for i, page in enumerate(pages):
        if check_for_image_only_content(page):
            image_only_pages.append(i + 1)  # Page numbers are 1-based
    if image_only_pages:
        print(f"Image-only pages found: {image_only_pages}")
        return ("fail", i + 1)
    print("No image-only pages found.")
    # We can also return the page count for other uses
    return ("pass", i + 1)

def check_markinfo(pdf):
    """Check for MarkInfo dictionary."""
    if "/MarkInfo" in pdf.Root:
        print("MarkInfo found:")
        print(pdf.Root.MarkInfo)  # look for /Marked = true
        return "pass"
    print("No MarkInfo found.")
    return "fail"

def check_document_language(pdf):
    """Check for document language specification."""
    if "/Lang" in pdf.Root:
        print("Document Language:")
        print(pdf.Root.Lang)
        return "pass"
    else:
        print("No document language specified.")
        return "fail"

"""
Claude says:
Also worth knowing: PDFs can store metadata in two places—the Info dictionary 
(older style) and XMP metadata (newer, XML-based, lives in /Metadata off the 
catalog). Some tools only populate one or the other. For a thorough check you 
might eventually want to look at both, but docinfo is the right starting 
point and what most accessibility checkers look at first.
"""
def check_document_title(pdf):
    """Check for document title in metadata."""
    if pdf.docinfo and "/Title" in pdf.docinfo:
        print("Document Title:")
        print(pdf.docinfo["/Title"])
        return "pass"
    else:
        print("No document title found.")
        return "fail"

def count_bookmarks(bookmark):
    """Recursively count bookmarks."""
    count = 1  # Count this bookmark
    if "/First" in bookmark:
        first = bookmark["/First"]
        count += count_bookmarks(first)
    if "/Next" in bookmark:
        next_bm = bookmark["/Next"]
        count += count_bookmarks(next_bm)
    return count

def check_for_bookmarks(pdf):
    """Check for bookmarks/outlines in the PDF."""
    if "/Outlines" not in pdf.Root:
        print("No outlines/bookmarks found.")
        return ("fail", 0)
    outlines = pdf.Root.Outlines
    if "/First" not in outlines:
        print("Empty bookmark structure.")
        return ("fail", 0)
    print("Bookmarks found.")
    bookmark_count = count_bookmarks(outlines.First)
    return ("pass", bookmark_count)

def get_page_number(page_ref, pdf):
    """Get the page number (1-based) for a given page reference."""
    for i, page in enumerate(pdf.pages):
        if page.objgen == page_ref.objgen:
            return i + 1
    return None

def check_page_tagging(pdf):
    """Check if all page content is tagged."""
    if "/StructTreeRoot" not in pdf.Root:
        print("No structure tree found; PDF is untagged.")
        return "fail"
    struct_root = pdf.Root.StructTreeRoot
    print("Structure Tree Root found.")
    
    print(f'{struct_root.keys() = }')
    if "/K" in struct_root:
        kids = struct_root.K
        if isinstance(kids, pikepdf.Array):
            print(f"Structure tree has {len(kids)} top-level kids.")
            for i, kid in enumerate(kids):
                print(kid.keys() if hasattr(kid, 'keys') else kid)
        else:
            print("Structure tree has a single top-level kid.")
            print(kids.keys() if hasattr(kids, 'keys') else kids)
            top_element = kids
            print(f'{type(top_element) = }')
            if "/K" in top_element:
                te_kids = top_element.K
                if isinstance(te_kids, pikepdf.Array):
                    print(f"Top element has {len(te_kids)} kids.")
                    # Look at first few kids
                    for j, te_kid in enumerate(list(te_kids)[:5]):
                        print(te_kid.keys() if hasattr(te_kid, 'keys') else te_kid)
                else:
                    print("Top element has a single kid.")
                    print(te_kids.keys() if hasattr(te_kids, 'keys') else te_kids)

    else:
        print("No /K found in StructTreeRoot; PDF is untagged.")
        return "fail"

    # max_depth = 4
    # print(f"Peeking at structure tree (max depth = {max_depth}):")
    # peek_structure_with_pages(struct_root, pdf, max_depth=max_depth)

    tagged = collect_tagged_pages(struct_root, pdf)
    all_pages = set(range(1, len(pdf.pages) + 1))
    untagged_pages = all_pages - tagged
    if untagged_pages:
        print(f"Untagged pages found: {sorted(untagged_pages)}")
        return "fail"
    print("All pages have tagged content.")
    return "pass - ROUGH CHECK ONLY"

def get_page_number(page_ref, pdf):
    """Convert a page object reference to a page number."""
    for i, page in enumerate(pdf.pages):
        if page.objgen == page_ref.objgen:
            return i + 1  # 1-indexed
    return None

# def peek_structure(element, depth=0, max_depth=3):
#     """Recursively peek at structure elements."""
#     if depth > max_depth:
#         return
    
#     indent = "  " * depth
    
#     if not hasattr(element, 'keys'):
#         # It's a content reference (MCR or OBJR), not a structure element
#         print(f"{indent}[content ref: {element}]")
#         return
    
#     tag = element.get('/S', '???')
#     page = element.get('/Pg', None)
#     page_info = f" (page ref exists)" if page else ""
#     print(f"{indent}{tag}{page_info}")
    
#     if "/K" in element:
#         kids = element.K
#         if isinstance(kids, pikepdf.Array):
#             for kid in kids:
#                 peek_structure(kid, depth + 1, max_depth)
#         else:
#             peek_structure(kids, depth + 1, max_depth)

# def peek_structure_with_pages(element, pdf, depth=0, max_depth=3):
    if depth > max_depth:
        return
    
    indent = "  " * depth
    
    if not hasattr(element, 'keys'):
        print(f"{indent}[MCID: {element}]")
        return
    
    tag = element.get('/S', '???')
    page_num = ""
    if "/Pg" in element:
        pn = get_page_number(element.Pg, pdf)
        page_num = f" [p.{pn}]"
    
    print(f"{indent}{tag}{page_num}")
    
    if "/K" in element:
        kids = element.K
        if isinstance(kids, pikepdf.Array):
            for kid in kids:
                peek_structure_with_pages(kid, pdf, depth + 1, max_depth)
        else:
            peek_structure_with_pages(kids, pdf, depth + 1, max_depth)

def collect_tagged_pages(element, pdf, tagged_pages=None):
    """Walk structure tree, collect set of page numbers that have tags."""
    if tagged_pages is None:
        tagged_pages = set()
    
    if not hasattr(element, 'keys'):
        # MCID reference, not a structure element
        return tagged_pages
    
    if "/Pg" in element:
        pn = get_page_number(element.Pg, pdf)
        if pn:
            tagged_pages.add(pn)
    
    if "/K" in element:
        kids = element.K
        if isinstance(kids, pikepdf.Array):
            for kid in kids:
                collect_tagged_pages(kid, pdf, tagged_pages)
        else:
            collect_tagged_pages(kids, pdf, tagged_pages)
    
    return tagged_pages

def check_annotations_tagged(pdf):
    """Check if all annotations are tagged."""
    if "/StructTreeRoot" not in pdf.Root:
        print("No structure tree found; PDF is untagged.")
        return "fail"
    struct_root = pdf.Root.StructTreeRoot

    # Collect all OBJR references in the structure tree
    objr_refs = set()
    _collect_objr_references(struct_root, objr_refs, pdf)

    # Check each page's annotations
    untagged_annots = []
    for page_num, page in enumerate(pdf.pages, start=1):
        if "/Annots" not in page:
            continue
        for annot_ref in page.Annots:
            annot_obj = (
                annot_ref.get_object() 
                if hasattr(annot_ref, 'get_object') 
                else annot_ref
                )
            # Check if this annotation is referenced in the structure tree
            if _get_obj_id(annot_obj, pdf) not in objr_refs:
                subtype = str(annot_obj.get("/Subtype", "Unknown"))
                untagged_annots.append((page_num, subtype))

    if not untagged_annots:
        print("All annotations are tagged.")
        return "pass"
    by_type = {}
    for page_num, subtype in untagged_annots:
        by_type.setdefault(subtype, []).append(page_num)

    details = "; ".join(
        [f"{subtype} on pages {sorted(pages)}" for subtype, pages in by_type.items()]
    )
    print(f"Untagged annotations found: {details}")
    return "fail"

def _get_obj_id(obj, pdf):
    """Get the object ID for a given PDF object."""
    if hasattr(obj, 'objgen'):
        return obj.objgen
    return id(obj) # Fallback to Python id

def _collect_objr_references(node, refs: set, pdf):
    """Recursively collect OBJR references from structure tree."""

    # Resolve if it's a reference
    if isinstance(node, pikepdf.Object):
        try:
            node = node.get_object() if hasattr(node, 'get_object') else node
        except Exception:
            return
    
    # Skip non-dictionary types (integers, strings, etc.)
    if not isinstance(node, pikepdf.Dictionary):
        return
    
    k = node.get("/K")
    if k is None:
        return
    
    # /K can be a single item or array
    if isinstance(k, pikepdf.Array):
        items = list(k)
    else:
        items = [k]
    
    for item in items:
        # Skip integers (MCIDs) and other primitives
        if isinstance(item, (int, str)) or not isinstance(item, pikepdf.Object):
            continue
        
        try:
            item_obj = item.get_object() if hasattr(item, 'get_object') else item
        except Exception:
            continue
        
        # Skip if not a dictionary
        if not isinstance(item_obj, pikepdf.Dictionary):
            continue
        
        item_type = item_obj.get("/Type")
        if item_type == pikepdf.Name("/OBJR"):
            # Object reference to an annotation
            ref_obj = item_obj.get("/Obj")
            if ref_obj is not None:
                refs.add(_get_obj_id(ref_obj, pdf))
        else:
            # Structure element—recurse into it
            _collect_objr_references(item_obj, refs, pdf)

def check_tab_order(pdf):
    """
    Check that tab order follows structure order on pages with focusable elements.
    
    WCAG 2.4.3 Focus Order: focusable components should receive focus in an
    order that preserves meaning and operability. For PDFs, this means pages
    with links or form fields should have /Tabs /S (structure order).
    """
    if "/StructTreeRoot" not in pdf.Root:
        return "fail"
    
    # Annotation subtypes that are keyboard-focusable
    FOCUSABLE_SUBTYPES = {
        pikepdf.Name("/Link"),
        pikepdf.Name("/Widget"),  # form fields
    }
    
    problem_pages = []
    pages_with_focusable = 0
    
    for page_num, page in enumerate(pdf.pages, start=1):
        # Check if page has focusable annotations
        annots = page.get("/Annots")
        if not annots:
            continue
        
        has_focusable = False
        for annot in annots:
            try:
                annot_obj = annot.get_object() if hasattr(annot, 'get_object') else annot
                if annot_obj.get("/Subtype") in FOCUSABLE_SUBTYPES:
                    has_focusable = True
                    break
            except Exception:
                continue
        
        if not has_focusable:
            continue
        
        pages_with_focusable += 1
        
        # Page has focusable elements—check tab order
        tabs = page.get("/Tabs")
        if tabs != pikepdf.Name("/S"):
            tab_value = str(tabs) if tabs else "unset"
            problem_pages.append((page_num, tab_value))
    
    if pages_with_focusable == 0:
        return "N/A (no focusable elements)"
    
    if not problem_pages:
        return "pass"
    
    # Group by tab order type
    by_type = {}
    for pg, t in problem_pages:
        by_type.setdefault(t, []).append(pg)
    
    details = "; ".join(f"{t}: pages {_summarize_pages(pgs)}" for t, pgs in by_type.items())
    print(f"Tab order not set to structure order: {details}")
    return "fail"


def _summarize_pages(pages: list) -> str:
    """Summarize page list, e.g., [1,2,3,5,6,8] -> '1-3, 5-6, 8'"""
    if not pages:
        return ""
    
    pages = sorted(set(pages))
    ranges = []
    start = end = pages[0]
    
    for p in pages[1:]:
        if p == end + 1:
            end = p
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = p
    
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges)

def check_character_encoding(pdf):
    """
    Check that fonts have reliable character encoding for text extraction.
    
    WCAG 4.1.1 Parsing / PDF/UA: Text must be extractable with correct
    Unicode values. Fonts should have /ToUnicode CMaps or use standard
    encodings so screen readers can read the content.
    """
    # Standard encodings that reliably map to Unicode
    STANDARD_ENCODINGS = {
        pikepdf.Name("/WinAnsiEncoding"),
        pikepdf.Name("/MacRomanEncoding"),
        pikepdf.Name("/MacExpertEncoding"),
        pikepdf.Name("/StandardEncoding"),
    }
    
    # Type 1 standard fonts that don't need ToUnicode
    STANDARD_TYPE1_FONTS = {
        "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
        "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
        "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
        "Symbol", "ZapfDingbats",
    }
    
    fonts_checked = 0
    problem_fonts = []
    
    for page_num, page in enumerate(pdf.pages, start=1):
        resources = page.get("/Resources")
        if not resources:
            continue
        
        font_dict = resources.get("/Font")
        if not font_dict:
            continue
        
        try:
            font_dict_obj = font_dict.get_object() if hasattr(font_dict, 'get_object') else font_dict
        except Exception:
            continue
        
        for font_name, font_ref in font_dict_obj.items():
            try:
                font = font_ref.get_object() if hasattr(font_ref, 'get_object') else font_ref
            except Exception:
                continue
            
            fonts_checked += 1
            
            # Check font type
            subtype = font.get("/Subtype")
            base_font = str(font.get("/BaseFont", "")).lstrip("/")
            
            # Standard Type1 fonts are fine
            if base_font in STANDARD_TYPE1_FONTS:
                continue
            
            # Type0 (composite) fonts should have ToUnicode
            if subtype == pikepdf.Name("/Type0"):
                if "/ToUnicode" not in font:
                    problem_fonts.append((page_num, font_name, "Type0 missing ToUnicode"))
                continue
            
            # Type1, TrueType, etc.
            has_tounicode = "/ToUnicode" in font
            encoding = font.get("/Encoding")
            has_standard_encoding = encoding in STANDARD_ENCODINGS
            
            # Also accept encoding dicts based on standard encodings
            if not has_standard_encoding and isinstance(encoding, pikepdf.Dictionary):
                base_encoding = encoding.get("/BaseEncoding")
                has_standard_encoding = base_encoding in STANDARD_ENCODINGS
            
            if not has_tounicode and not has_standard_encoding:
                problem_fonts.append((page_num, font_name, "no ToUnicode or standard encoding"))
    
    if fonts_checked == 0:
        return "N/A (no fonts found)"
    
    if not problem_fonts:
        return "pass"
    
    # Deduplicate by font name and reason
    unique_issues = {}
    for pg, name, reason in problem_fonts:
        key = (name, reason)
        unique_issues.setdefault(key, []).append(pg)
    
    details = "; ".join(f"{name} ({reason})" for (name, reason) in unique_issues.keys())
    print(f"Fonts with encoding issues: {details}")
    return "fail"

def check_pdf_accessibility_pikepdf(file_path, args):
    """Check if a PDF is tagged for accessibility."""
    checklist = {
        "document-level": {},
        "page-level": {},
        "forms": {},
        "alternate text": {},
        "tables": {},
        "lists": {},
        "headings": {},
    }

    pdf = open_pdf_pikepdf(file_path)
    # Root catalog - the jumping off point
    print(f"{pdf.Root.keys() = }")

    # Check for structure tree root
    if "/StructTreeRoot" in pdf.Root:
        struct_tree = pdf.Root.StructTreeRoot
        print("Structure Tree Root found:")
        print(struct_tree.keys())
        # /K contains the structure elements

    ## Document-level checks ================================

    # Check for image only pages, and get page count
    checklist["document-level"]["Image-only Pages"], num_pages = check_for_image_only_pages(pdf)

    # Check MarkInfo (indicates tagged PDF)
    checklist["document-level"]["Tagged"] = check_markinfo(pdf)

    # Check for Document language
    checklist["document-level"]["Language"] = check_document_language(pdf)

    # Check for Document Title
    checklist["document-level"]["Title"] = check_document_title(pdf)

    # Check for bookmarks/outlines in documents over 20 pages
    if args.force_warning:
        num_pages = 800 # just for debugging/testing
    print(f"Number of pages: {num_pages}")
    page_threshold = 20
    if num_pages > page_threshold or args.force_bookmark_check:
        checklist["document-level"]["Bookmarks"], bookmark_count = check_for_bookmarks(pdf)
        print(f"Number of bookmarks: {bookmark_count}")
        if checklist["document-level"]["Bookmarks"] == "pass":
            if  num_pages / bookmark_count > 30:
                checklist["document-level"]["Bookmarks Count"] = f"Warning (only {bookmark_count} bookmarks for {num_pages} pages)"
    else:
        checklist["document-level"]["Bookmarks"] = "N/A (under 20 pages)"
    
    ## Page-level checks ================================

    # Check that all page content is tagged
    checklist["page-level"]["Page Content Tagged"] = check_page_tagging(pdf)

    # Check that all annotations are tagged
    checklist["page-level"]["Annotations Tagged"] = check_annotations_tagged(pdf)

    # Check that tab order is consistent with structure order
    checklist["page-level"]["Tab Order"] = check_tab_order(pdf)

    # Check that character encoding is reliably specified
    checklist["page-level"]["Character Encoding"] = check_character_encoding(pdf)

    # Check that all multimedia content is tagged
    checklist["page-level"]["Multimedia Tagged"] = "Not implemented"

    # Check that page will not cause flickering
    checklist["page-level"]["Flickering"] = "Not implemented"

    # Check that there are no inaccessible scripts
    checklist["page-level"]["Inaccessible Scripts"] = "Not implemented"

    # Check that no pages require timed responses
    checklist["page-level"]["Timed Responses"] = "Not implemented"

    # Check that navigation links are not repetitive
    checklist["page-level"]["Navigation Links"] = "Not implemented"

    ## Form checks ================================

    # Check that form fields are tagged
    checklist["forms"]["Form Fields Tagged"] = "Not implemented"

    # Check that form fields have descriptions
    checklist["forms"]["Form Field Descriptions"] = "Not implemented"
    ## Alternate Text Checks ================================

    # Check that all figures have alternate text
    checklist["alternate text"]["Alternate Text"] = "Not implemented"

    # Check against nested alt text that will never be read
    checklist["alternate text"]["Nested Alternate Text"] = "Not implemented"
    # Check that alt text is associated with content
    checklist["alternate text"]["Alternate Text Association"] = "Not implemented"

    # Check that alt text does not hide annotations
    checklist["alternate text"]["Alt Text Hides Annotations"] = "Not implemented"

    # Check for other elements that require alt text
    checklist["alternate text"]["Other Alt Text Elements"] = "Not implemented"

    ## Table Checks ================================

    # Check that table rows (TR) are children of Table, THead, TBody, or TFoot
    checklist["tables"]["Table Row Structure"] = "Not implemented"

    # Check that TH and TD are children of TR
    checklist["tables"]["Table Cell Structure"] = "Not implemented"

    # Check that tables have headers
    checklist["tables"]["Table Headers"] = "Not implemented"

    # Check that tables have regular structure (same number of columns in each row)
    checklist["tables"]["Table Regularity"] = "Not implemented"

    # Check that tables have summaries
    checklist["tables"]["Table Summary"] = "Not implemented"

    ## List Checks ================================

    # Check that list items (LI) are children of List (L) or ListItem (LI)
    checklist["lists"]["List Item Structure"] = "Not implemented"

    # Check that labels (Lbl) and bodies (LBody) are children of LI
    checklist["lists"]["List Label/Body Structure"] = "Not implemented"

    ## Heading Checks ================================

    # Check for appropriate nesting
    checklist["headings"]["Heading Nesting"] = "Not implemented"

    ## Misc and Reporting ================================

    # Poke at a specific page's resources
    page = pdf.pages[0]
    print("First Page Keys:")
    print(page.keys())
    if "/Resources" in page:
        print("First Page Resources:")
        print(page.Resources.keys())

    # Color code the results
    for category, items in checklist.items():
        for item in items:
            if items[item].startswith("pass"):
                items[item] = f"\033[92m{items[item]}\033[0m"  # green
            elif items[item].startswith("fail"):
                items[item] = f"\033[91m{items[item]}\033[0m"  # red
            elif items[item].startswith("Warning"):
                items[item] = f"\033[38;5;208m{items[item]}\033[0m"  # light orange
            elif items[item].startswith("Not implemented"):
                items[item] = f"\033[95m{items[item]}\033[0m"  # light purple

    print("\n","- " * 25)
    print("Accessibility Checklist Results:")
    for category, items in checklist.items():
        print(f"{category.capitalize()}:")
        for item, result in items.items():
            print(f"  {item}: {result}")


def main():
    # parse arguments
    parser = argparse.ArgumentParser(description="Check if a PDF is tagged for accessibility.")
    parser.add_argument("pdf_file", help="Path to the PDF file to check.")
    parser.add_argument("--force-bookmark-check", action="store_true", help="Force bookmark check even for single page documents. (normally only on >20 pages)")
    parser.add_argument("--force-warning", action="store_true", help="Artificially set pages to a high number to trigger a warning for testing. Only triggers when bookmarks exist.")
    args = parser.parse_args()

    print(f"Checking accessibility for PDF: {args.pdf_file}")
    # check_pdf_accessibility_pymupdf(args.pdf_file)
    # print("\n---\n")
    check_pdf_accessibility_pikepdf(args.pdf_file, args)
    # if accessible:
    #     print("The PDF is tagged for accessibility.")
    # else:
    #     print("The PDF is NOT tagged for accessibility.")

if __name__ == "__main__":
    main()