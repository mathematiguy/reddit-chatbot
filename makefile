IMAGE := docker.dragonfly.co.nz/reddit-chatbot
RUN ?= docker run $(INTERACT) --rm -v $$(pwd):/work -w /work -u $(UID):$(GID) $(IMAGE)
UID ?= $(shell id -u)
GID ?= $(shell id -g)
INTERACT ?= 
GIT_TAG ?= $(shell git log --oneline | head -n1 | awk '{print $$1}')

.PHONY: docker
docker:
	docker build --tag $(IMAGE):$(GIT_TAG) .
	docker tag $(IMAGE):$(GIT_TAG) $(IMAGE):latest
