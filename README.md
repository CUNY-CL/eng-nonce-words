The lexicon is from [CityLex](https://github.com/kylebgorman/citylex).

To use, run:

```
pip install -r requirements.txt
citylex --wikipron_us && rm -f citylex.tsv
./generate.py
# Annotate for lexicality.
./stratify.py
```
