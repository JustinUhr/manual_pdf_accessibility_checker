import pikepdf

def create_bad_encoding_pdf(output_path):
    """Create a test PDF with a font missing ToUnicode and standard encoding."""
    pdf = pikepdf.Pdf.new()
    
    # Add a blank page first, then modify it
    pdf.add_blank_page(page_size=(612, 792))
    page = pdf.pages[0]
    
    # Create font with no encoding info
    bad_font = pdf.make_indirect(pikepdf.Dictionary({
        "/Type": pikepdf.Name("/Font"),
        "/Subtype": pikepdf.Name("/Type1"),
        "/BaseFont": pikepdf.Name("/WeirdCustomFont"),
        # Deliberately no /Encoding or /ToUnicode
    }))
    
    # Set up resources
    page["/Resources"] = pikepdf.Dictionary({
        "/Font": pikepdf.Dictionary({
            "/F1": bad_font
        })
    })
    
    # Add content stream
    page["/Contents"] = pdf.make_stream(b"BT /F1 12 Tf 100 700 Td (Test) Tj ET")
    
    pdf.save(output_path)
    print(f"Created {output_path}")

create_bad_encoding_pdf("bad_encoding_test.pdf")