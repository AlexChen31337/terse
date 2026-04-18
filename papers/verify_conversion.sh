#!/bin/bash
echo "=== IJCAI-ECAI 2026 Conversion Verification ==="
echo ""

echo "✓ Checking documentclass..."
grep -q "\\usepackage{ijcai26}" evoclang-ijcai2026-50pages.tex && echo "  ✅ ijcai26 package found" || echo "  ❌ MISSING"

echo "✓ Checking page size..."
grep -q "pdfpagewidth=8.5in" evoclang-ijcai2026-50pages.tex && echo "  ✅ 8.5x11 letter format set" || echo "  ❌ MISSING"

echo "✓ Checking line numbering..."
grep -q "\\usepackage\[switch\]{lineno}" evoclang-ijcai2026-50pages.tex && echo "  ✅ lineno package found" || echo "  ❌ MISSING"
grep -q "\\linenumbers" evoclang-ijcai2026-50pages.tex && echo "  ✅ linenumbers command found" || echo "  ❌ MISSING"

echo "✓ Checking author block..."
grep -q "\\affiliations" evoclang-ijcai2026-50pages.tex && echo "  ✅ IJCAI author format found" || echo "  ❌ MISSING"
grep -q "\\emails" evoclang-ijcai2026-50pages.tex && echo "  ✅ IJCAI email format found" || echo "  ❌ MISSING"

echo "✓ Checking bibliography style..."
grep -q "\\bibliographystyle{named}" evoclang-ijcai2026-50pages.tex && echo "  ✅ named style set" || echo "  ❌ MISSING"

echo "✓ Checking algorithm package..."
grep -q "\\usepackage{algorithmic}" evoclang-ijcai2026-50pages.tex && echo "  ✅ algorithmic package found" || echo "  ❌ MISSING"

echo "✓ Checking times font..."
grep -q "\\usepackage{times}" evoclang-ijcai2026-50pages.tex && echo "  ✅ times package found" || echo "  ❌ MISSING"

echo ""
echo "✓ Checking PDF output..."
if [ -f evoclang-ijcai2026-50pages.pdf ]; then
    pages=$(pdfinfo evoclang-ijcai2026-50pages.pdf | grep "^Pages:" | awk '{print $2}')
    size=$(pdfinfo evoclang-ijcai2026-50pages.pdf | grep "^Page size:" | grep -o "letter")
    echo "  ✅ PDF exists: $pages pages"
    [ "$size" = "letter" ] && echo "  ✅ Page size: letter (8.5x11)" || echo "  ⚠️  Page size not letter"
else
    echo "  ❌ PDF not found"
fi

echo ""
echo "✓ Checking preserved content..."
grep -q "definecolor{coreblue}" evoclang-ijcai2026-50pages.tex && echo "  ✅ Color definitions preserved" || echo "  ❌ MISSING"
grep -q "lstdefinestyle{rustcode}" evoclang-ijcai2026-50pages.tex && echo "  ✅ Rust listing style preserved" || echo "  ❌ MISSING"
grep -q "tikzpicture" evoclang-ijcai2026-50pages.tex && echo "  ✅ TikZ diagrams preserved" || echo "  ⚠️  No TikZ found"

echo ""
echo "=== Verification Complete ==="
