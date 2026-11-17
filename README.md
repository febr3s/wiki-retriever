1: generate the ids (run id-list-generator.py)
2: download via command line 

```curl -A "MyDownloaderScript/1.0 (contact@example.com)" \
  "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category%3AArtworks%20of%20Colombia%20in%20the%20Cooper%E2%80%93Hewitt%2C%20Smithsonian%20Design%20Museum&cmtype=file&cmlimit=max&format=json" \
  -o artworks.json
```
<!-- remember this solution is limited to 500 results -->
3: Print csv with API
4: Print csv with wikitext