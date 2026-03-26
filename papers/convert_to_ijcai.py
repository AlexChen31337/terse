#!/usr/bin/env python3
"""
Convert EvoClaw paper from NeurIPS 2024 to IJCAI-ECAI 2026 format
"""
import re

def convert_neurips_to_ijcai(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Replace documentclass and neurips package
    content = re.sub(
        r'\\documentclass\{article\}\s*\n\\usepackage\[preprint\]\{neurips_2024\}',
        r'\\documentclass{article}\n\\pdfpagewidth=8.5in\n\\pdfpageheight=11in\n\\usepackage{ijcai26}',
        content
    )
    
    # 2. Add required IJCAI packages after ijcai26 (before inputenc)
    content = re.sub(
        r'(\\usepackage\{ijcai26\})\s*\n(\\usepackage\[utf8\]\{inputenc\})',
        r'\1\n\\usepackage{times}\n\\usepackage[switch]{lineno}\n\2',
        content
    )
    
    # 3. Replace T1 fontenc (IJCAI uses times package instead)
    content = re.sub(r'\\usepackage\[T1\]\{fontenc\}\s*\n', '', content)
    
    # 4. Update hyperref to use hidelinks
    content = re.sub(
        r'\\usepackage\{hyperref\}',
        r'\\usepackage[hidelinks]{hyperref}',
        content
    )
    
    # 5. Replace algpseudocode with algorithmic
    content = re.sub(
        r'\\usepackage\{algpseudocode\}',
        r'\\usepackage{algorithmic}',
        content
    )
    
    # 6. Remove or update algorithm compatibility macros (algpseudocode -> algorithmic)
    # IJCAI uses \REQUIRE and \ENSURE directly, so keep those macros
    
    # 7. Convert author block to IJCAI format
    old_author = r'''\\author\{
  A. Chen\\thanks\{Equal contribution\. Correspondence: \\texttt\{bowen31337@outlook\.com\}\} \\quad A. Author\\footnotemark\[1\] \\quad Nicholas Qi\\footnotemark\[1\] \\\\\[0\.3em\]
  Independent Researchers \\\\
  \\texttt\{alex\.chen31337@gmail\.com\} \\quad \\texttt\{bowen31337@outlook\.com\} \\quad \\texttt\{nicholas68663@gmail\.com\} \\\\
  \\texttt\{github\.com/clawinfra/evoclaw\}
\}'''
    
    new_author = r'''\\author{
A. Chen$^1$
\\and
A. Author$^1$\\and
Nicholas Qi$^1$\\\\
\\affiliations
$^1$Independent Researchers\\\\
\\emails
alex.chen31337@gmail.com,
author@example.com,
coauthor@example.com
}'''
    
    content = re.sub(old_author, new_author, content, flags=re.DOTALL)
    
    # 8. Add line numbering after \begin{document}
    content = re.sub(
        r'(\\begin\{document\})',
        r'\1\n\n\\linenumbers',
        content
    )
    
    # 9. Change bibliographystyle from plain to named
    content = re.sub(
        r'\\bibliographystyle\{plain\}',
        r'\\bibliographystyle{named}',
        content
    )
    
    # 10. Update header comments
    content = re.sub(
        r'% Targeting NeurIPS 2024 format',
        r'% Targeting IJCAI-ECAI 2026 format',
        content
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Conversion complete: {input_file} -> {output_file}")

if __name__ == '__main__':
    convert_neurips_to_ijcai(
        'evoclang-expanded-50pages.tex',
        'evoclang-ijcai2026-50pages.tex'
    )
