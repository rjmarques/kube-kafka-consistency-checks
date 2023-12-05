# Kubernetes and Kafka Consisntency Checks

## Docker and GH packages

```bash
# docker login
echo $GITHUB_TOKEN | docker login ghcr.io -u rjmarques --password-stdin

# build local dev image
docker build --tag ghcr.io/rjmarques/httpd:dev src

# push to GH registry
docker push ghcr.io/rjmarques/httpd:dev
```

```bash
# use kcat via docker
docker run -it --network=host --rm edenhill/kcat:1.7.1 -b kube.local:30092 -L

# use kcat directly
kcat -L -b mybroker
```