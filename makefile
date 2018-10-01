DOCKER_REGISTRY := mathematiguy
IMAGE_NAME := minimal-project
IMAGE := $(DOCKER_REGISTRY)/$(IMAGE_NAME)
RUN ?= docker run $(INTERACT) --rm -v $$(pwd):/work -w /work -u $(UID):$(GID) $(IMAGE)
UID ?= $(shell id -u)
GID ?= $(shell id -g)
INTERACT ?= 
GIT_TAG ?= $(shell git log --oneline | head -n1 | awk '{print $$1}')
TIMESTAMP := $(shell date "+%Y%m%d-%H%M%S")

LOG_LEVEL ?= INFO
crawl:
	(cd reddit_comments && \
		$(RUN) scrapy crawl download \
			-s JOBDIR=crawls \
			--loglevel $(LOG_LEVEL) | \
			tee logs/reddit_comments-$(TIMESTAMP).log)

.PHONY: docker
docker:
	docker build --tag $(IMAGE):$(GIT_TAG) .
	docker tag $(IMAGE):$(GIT_TAG) $(IMAGE):latest

.PHONY: docker-push
docker-push:
	docker push $(IMAGE):$(GIT_TAG) && \
	docker push $(IMAGE):latest

.PHONY: enter
enter: INTERACT=-it
enter:
	$(RUN) bash

.PHONY: enter-root
enter-root: INTERACT=-it
enter-root: UID=root
enter-root: GID=root
enter-root:
	$(RUN) bash

.PHONY: inspect-variables
inspect-variables:
	@echo IMAGE:    $(IMAGE)
	@echo RUN:      $(RUN)
	@echo UID:      $(UID)
	@echo GID:      $(GID)
	@echo INTERACT: $(INTERACT)
	@echo GIT_TAG:  $(GIT_TAG)
