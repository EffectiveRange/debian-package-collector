colon := :
$(colon) := :
TAG=latest
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean package image service

clean:
	rm -rf build dist *.egg-info

package:
	sudo apt-get install -y ruby ruby-dev rubygems build-essential
	sudo gem install -N fpm
	fpm setup.py

image:
	docker build $(ROOT_DIR) --file Dockerfile --tag effectiverange/debian-package-collector$(:)$(TAG)

service:
	TAG=$(TAG) envsubst '$$TAG' < $(ROOT_DIR)/service/debian-package-collector.docker.service > $(ROOT_DIR)/dist/debian-package-collector-$(TAG:v%=%).docker.service
