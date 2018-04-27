index.md: notebook.ipynb
	jupyter nbconvert --ExecutePreprocessor.timeout=-1 --to=markdown --output=index notebook.ipynb
rerun:
	jupyter nbconvert --ExecutePreprocessor.timeout=-1 --to=notebook --inplace --execute notebook.ipynb
.PHONY: rerun
