# Manual PDF Accessibility Checker

A Python tool for checking PDF accessibility compliance. This tool analyzes PDF documents to verify they meet accessibility standards, helping ensure documents are usable by people with disabilities who rely on assistive technologies like screen readers.

## Features

The checker evaluates PDFs against multiple accessibility criteria organized into categories:

### Document-Level Checks
| Check | Status |
|-------|--------|
| Image-only Pages | ✅ Implemented |
| Tagged (MarkInfo) | ✅ Implemented |
| Document Language | ✅ Implemented |
| Document Title | ✅ Implemented |
| Bookmarks (for documents >20 pages) | ✅ Implemented |

### Page-Level Checks
| Check | Status |
|-------|--------|
| Page Content Tagged | ✅ Implemented |
| Annotations Tagged | ✅ Implemented |
| Tab Order | ✅ Implemented |
| Character Encoding | ✅ Implemented |
| Multimedia Tagged | 🚧 Not Implemented |
| Flickering | 🚧 Not Implemented |
| Inaccessible Scripts | 🚧 Not Implemented |
| Timed Responses | 🚧 Not Implemented |
| Navigation Links | 🚧 Not Implemented |

### Form Checks
| Check | Status |
|-------|--------|
| Form Fields Tagged | 🚧 Not Implemented |
| Form Field Descriptions | 🚧 Not Implemented |

### Alternate Text Checks
| Check | Status |
|-------|--------|
| Alternate Text | 🚧 Not Implemented |
| Nested Alternate Text | 🚧 Not Implemented |
| Alternate Text Association | 🚧 Not Implemented |
| Alt Text Hides Annotations | 🚧 Not Implemented |
| Other Alt Text Elements | 🚧 Not Implemented |

### Table Checks
| Check | Status |
|-------|--------|
| Table Row Structure | 🚧 Not Implemented |
| Table Cell Structure | 🚧 Not Implemented |
| Table Headers | 🚧 Not Implemented |
| Table Regularity | 🚧 Not Implemented |
| Table Summary | 🚧 Not Implemented |

### List Checks
| Check | Status |
|-------|--------|
| List Item Structure | 🚧 Not Implemented |
| List Label/Body Structure | 🚧 Not Implemented |

### Heading Checks
| Check | Status |
|-------|--------|
| Heading Nesting | 🚧 Not Implemented |

## Installation

### Requirements
- Python 3.12 or higher

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. To install and run:

```bash
uv run check_pdf.py <path_to_pdf_file>
```

This will automatically create a virtual environment and install the required dependencies.

### Using pip (Alternative)

If you prefer to use pip:

```bash
pip install pikepdf
```

## Usage

uv
```bash
uv run check_pdf.py <path_to_pdf_file> [options]
```

pip
```bash
python check_pdf.py <path_to_pdf_file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--force-bookmark-check` | Force bookmark check even for documents under 20 pages (bookmarks are normally only checked on documents >20 pages) |
| `--force-warning` | Set page count artificially high (800) to trigger bookmark count warnings for testing (only applies when bookmarks exist) |

### Example

```bash
uv run check_pdf.py ../document.pdf
```

## Output

The tool produces a color-coded checklist showing the results for each accessibility check:

- 🟢 **Green (pass)**: Check passed
- 🔴 **Red (fail)**: Check failed
- 🟠 **Orange (Warning)**: Potential issue detected
- 🟣 **Purple (Not implemented)**: Check not yet available

## Dependencies

- [pikepdf](https://github.com/pikepdf/pikepdf) - PDF manipulation library
- ~~[PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF rendering and analysis~~ (not currently used)

## License

MIT License

## Author

Justin Uhr (justin_uhr@brown.edu)
