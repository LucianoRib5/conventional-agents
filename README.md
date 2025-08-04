# conventional-agents

Este projeto utiliza agentes autônomos com suporte à biblioteca `autogen`.

## Pré-requisitos

- Python 3 instalado
- Virtualenv (opcional, mas recomendado)
- Um arquivo `.env` contendo a variável de ambiente `OPENAI_API_KEY` com sua chave da API da OpenAI.

## Instalação

1. Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Obs.:** No Windows, use `.\.venv\Scriptsctivate` em vez de `source .venv/bin/activate`.

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Observações

- Certifique-se de ter um arquivo `.env` com a variável `OPENAI_API_KEY` definida.
- A biblioteca `autogen` será instalada automaticamente pelas dependências.