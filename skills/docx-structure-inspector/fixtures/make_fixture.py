"""make_fixture: build the smoke-test .docx at runtime, outside the package.

Usage:
    python -I fixtures/make_fixture.py [output.docx]

Default output is a file in the system temp folder. The file is a minimal
package with two parts (word/document.xml and word/comments.xml). It is not a
complete Word file, so it is only meant for docx_inspect.py. Expected report:
6 paragraphs, 1 empty, 1 table, 0 images, 1 comment, 1 insertion, 0 deletions,
2 headings (Intro level 1, Details level 2), authors Ana and Ben.
"""

import os
import sys
import tempfile
import zipfile

NS = "http" + "://" + "schemas.openxmlformats.org/wordprocessingml/2006/main"

DOCUMENT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="' + NS + '"><w:body>'
    '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
    '<w:r><w:t>Intro</w:t></w:r></w:p>'
    '<w:p><w:r><w:t xml:space="preserve">Plain text. </w:t></w:r>'
    '<w:ins w:id="1" w:author="Ana" w:date="2026-11-01T00:00:00Z">'
    '<w:r><w:t>added</w:t></w:r></w:ins></w:p>'
    '<w:p/>'
    '<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
    '<w:r><w:t>Details</w:t></w:r></w:p>'
    '<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>Commented text</w:t></w:r>'
    '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
    '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
    '</w:body></w:document>'
)

COMMENTS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:comments xmlns:w="' + NS + '">'
    '<w:comment w:id="0" w:author="Ben" w:date="2026-11-02T00:00:00Z" w:initials="BN">'
    '<w:p><w:r><w:t>Check this</w:t></w:r></w:p></w:comment>'
    '</w:comments>'
)


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(tempfile.gettempdir(), "docx_inspect_smoke.docx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", DOCUMENT)
        zf.writestr("word/comments.xml", COMMENTS)
    sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
