The lexicon is from [CityLex](https://github.com/kylebgorman/citylex).

To use, run:

```
pip install -r requirements.txt
citylex --wikipron-us && rm -f citylex.tsv
./generate.py --extra-lexicon first-pass-extra-lexicon.txt
./stratify.py
```
