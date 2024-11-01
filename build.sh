#!/usr/bin/env bash
# build.sh

# Atualiza o pip
pip install --upgrade pip

# Instala as dependências do projeto
pip install -r requirements.txt

# Se você estiver usando Poetry, pode usar este comando em vez do pip
# poetry install

# Você pode adicionar outros comandos necessários para a preparação do seu ambiente
# Por exemplo, criar diretórios necessários:
mkdir -p downloads

# Não inclua comandos que tentem modificar partes do sistema que são somente leitura
# como apt-get update ou apt-get install