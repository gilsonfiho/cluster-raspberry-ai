#!/bin/bash
watch -n 2 'docker stack ps llm-cluster && echo && docker service ls'
