# Kubernetes and Kafka Consisntency Checks

## Python

```bash
# create the venv
python -m venv kube-kafka
# and active it
source kube-kafka/Scripts/activate
```

## Docker and GH packages

```bash
# docker login
echo $GITHUB_TOKEN | docker login ghcr.io -u rjmarques --password-stdin

# build local docker image (for each app)
docker build -f src/Dockerfile -t ghcr.io/rjmarques/controller:latest --build-arg 'TARGET=controller' .
docker build -f src/Dockerfile -t ghcr.io/rjmarques/worker:latest --build-arg 'TARGET=worker' .

# push to GH registry
docker push ghcr.io/rjmarques/controller:latest
docker push ghcr.io/rjmarques/worker:latest
```

## Kafka (inspecting)

```bash
# use kcat via docker
docker run -it --network=host --rm edenhill/kcat:1.7.1 -b kube.local:30092 -L

# use kcat directly
kcat -L -b mybroker
```