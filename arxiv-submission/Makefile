# Makefile for ClawChain arXiv submission
# Usage: make pdf | make clean | make arxiv

MAIN = main
LATEX = pdflatex
BIBTEX = bibtex

.PHONY: pdf clean arxiv quick

# Full build (2 pdflatex + bibtex + 2 pdflatex)
pdf: $(MAIN).tex
	$(LATEX) $(MAIN)
	$(BIBTEX) $(MAIN)
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

# Quick build (single pass, no bibliography)
quick: $(MAIN).tex
	$(LATEX) $(MAIN)

# Clean auxiliary files
clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out \
	      $(MAIN).toc $(MAIN).lof $(MAIN).lot $(MAIN).fls $(MAIN).fdb_latexmk \
	      $(MAIN).synctex.gz $(MAIN).nav $(MAIN).snm $(MAIN).vrb \
	      *.aux

# Clean everything including PDF
distclean: clean
	rm -f $(MAIN).pdf

# Package for arXiv upload
arxiv: pdf
	mkdir -p arxiv-package
	cp $(MAIN).tex abstract.tex introduction.tex architecture.tex \
	   tokenomics.tex governance.tex usecases.tex security.tex \
	   roadmap.tex conclusion.tex references.bib $(MAIN).bbl \
	   arxiv-package/
	cp -r figures/ arxiv-package/figures/ 2>/dev/null || true
	cd arxiv-package && tar czf ../clawchain-arxiv.tar.gz *
	rm -rf arxiv-package
	@echo "Created clawchain-arxiv.tar.gz for arXiv upload"
