


```
poetry 

`https://github.com/ollama/ollama/blob/main/docs/api.md`
`https://github.com/open-webui/open-webui/discussions/742`


to pull an image. call the local ollama service
```
export PORT = 60942
curl http://127.0.0.1:{$PORT}/api/pull -d '{ 
  "name": "phi3"
}'
# confirm
curl http://127.0.0.1:{$PORT}/api/tags
```

