
Run Ollama locally and interact through OpenWebUI service. Nice!

Set up poetry, the package management tool.
```
pyenv install 3.11.5
python3 -m pip install pipx
python3 -m pipx install poetry 

```
Set up Pulumi and local K8 cluster following the instructions [here](https://www.pulumi.com/docs/get-started/). 

Get the service up and running.
```
poetry run pulumi up
```


Pull the desired model; call the local ollama service.
```
export PORT = xxx
curl http://127.0.0.1:{$PORT}/api/pull -d '{ 
  "name": "phi3"
}'
```
confirm that the model is pulled
```
curl http://127.0.0.1:{$PORT}/api/tags
```

Interact with the OpenWebUI service. 

g