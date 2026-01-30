import pymupdf
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

def check_pdf_accessibility_pikepdf(file_path):
    """Check if a PDF is tagged for accessibility."""
    pdf = open_pdf_pikepdf(file_path)
    # Root catalog - the jumping off point
    print(pdf.Root.keys())

    # Check for structure tree root
    if "/StructTreeRoot" in pdf.Root:
        struct_tree = pdf.Root.StructTreeRoot
        print("Structure Tree Root found:")
        print(struct_tree.keys())
        # /K contains the structure elements

    # Check for image only pages
    if "/Pages" in pdf.Root:
        pages = pdf.pages
        num_pages = len(pages)
        print(f"Number of pages: {num_pages}")
        image_only = False
        for i in range(num_pages):
            page = pages[i]
            image_only_page = check_for_image_only_content(page)
            if image_only_page:
                print(f"Page {i+1} appears to be image-only.")
                image_only = True
        if not image_only:
            print("No image-only pages detected.")

        
    # Check MarkInfo (indicates tagged PDF)
    if "/MarkInfo" in pdf.Root:
        print("MarkInfo found:")
        print(pdf.Root.MarkInfo)  # look for /Marked = true

    # Document language
    if "/Lang" in pdf.Root:
        print("Document Language:")
        print(pdf.Root.Lang)

    # Poke at a specific page's resources
    page = pdf.pages[0]
    print("First Page Keys:")
    print(page.keys())
    if "/Resources" in page:
        print("First Page Resources:")
        print(page.Resources.keys())


def main():
    # parse arguments
    parser = argparse.ArgumentParser(description="Check if a PDF is tagged for accessibility.")
    parser.add_argument("pdf_file", help="Path to the PDF file to check.")
    args = parser.parse_args()

    print(f"Checking accessibility for PDF: {args.pdf_file}")
    check_pdf_accessibility_pymupdf(args.pdf_file)
    print("\n---\n")
    check_pdf_accessibility_pikepdf(args.pdf_file)
    # if accessible:
    #     print("The PDF is tagged for accessibility.")
    # else:
    #     print("The PDF is NOT tagged for accessibility.")

if __name__ == "__main__":
    main()