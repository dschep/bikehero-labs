index.html: notebook.ipynb
	jupyter nbconvert --ExecutePreprocessor.timeout=-1 --to=html --output=index notebook.ipynb
rerun:
	jupyter nbconvert --ExecutePreprocessor.timeout=-1 --to=notebook --inplace --execute notebook.ipynb
.PHONY: rerun
