# Guia de Implementação - Pipeline Naive RAG + MongoDB Atlas com Gemini 1.5 Flash

## Pré-requisitos

-   Python: preferencialmente a versão 3.12 ou superior;

-   Docker e Docker-Compose: Será usado para executar um container do
    banco de dados MongoDB Atlas;

-   Chave de API do Google Gemini: para usar os embeddings e o
    modelo Gemini 1.5 flash;
    - Que pode ser criada a partir deste link: <https://aistudio.google.com/app/apikey?hl=pt-br>.

-   Editor de Código: como VS Code, PyCharm ou o que você preferir;

-   Conhecimentos Básicos de Python: não precisa ser especialista, mas
    entender o básico vai ajudar;

-   Client HTTP: usado para enviar requisições, como o Postman ou o
    **Thunder Client**, que se trata de uma extensão para o VS Code;

-   Acessar o repositório do guia de implementação: disponível em
    <https://github.com/g4bzz/minicurso-rag-api>.

Para você absorver melhor o conhecimento e de fato implementar a
pipeline, recomendo que você inicialmente **não** clone o repositório do
guia. Siga o guia de acordo com as instruções.

## Configuração do ambiente

Primeiramente, crie um diretório para conter todo o código a ser escrito
(eu sei, é óbvio. Mas é bom reforçar :D).

Estando no diretório, é necessário criar um ambiente virtual com o
python para abrigar todas as dependências do projeto de forma isolada.
Logo, a partir de um terminal, execute o seguinte código:

```
    python3 -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\Activate.ps1  # Windows
```

Com isso, além de criar o ambiente, você estará também o ativando. Em
seguida, instale as dependências necessárias. Para isso, copie o arquivo
**requirements.txt** do repositório para dentro do seu projeto. Em
seguida, execute o seguinte comando para instalar as dependências:

```
    pip install -r requirements.txt
```

Agora, para as próximas etapas, trabalharemos com os seguintes arquivos:

-   **.env**: armazenará a chave da API do Gemini;

-   **config.py**: classe Config, responsável por declarar as variáveis
    globais do projeto;

-   **rag_gemini.py**: responsável por conter toda a lógica do RAG;

-   **httpserver.py**: instancia o servidor HTTP;

-   **docker-compose.yaml**: declara o container do MongoDB Atlas a ser
    usado.

Além disso, também crie uma pasta intitulada como **pdf** e insira os
seus PDFs nessa pasta e prepare-se... É hora de por a mão na massa!

## Definindo as Configurações

Uma vez criada a chave da API do Gemini, crie um arquivo **.env** com o
seguinte texto, obviamente, substituindo o **SUA-CHAVE** pela sua chave
da API.

```
GOOGLE_API_KEY='SUA-CHAVE'
```

Agora que temos as dependências instaladas e a chave da API já inserida
no **.env**, precisamos alimentar o arquivo de configuração
**config.py**. Aqui é onde você vai colocar as informações dos modelos
usados, suas credenciais do contêiner do MongoDB Atlas e também a
chamada à chave da API do Gemini.

Seguindo o padrão, copie o arquivo **config.py** do repositório para o
seu projeto. O seu arquivo deve ter exatamente essas informações.

## Criando e executando a instância do vector store

Agora, copie o arquivo **docker-compose.yaml** para o seu projeto e o
execute, para isso, rode o seguinte comando no terminal:
```
docker-compose up -d
```
Com este comando, o contêiner do MongoDB Atlas será criado e executado
na porta 27017, com um usuário root (user) e uma senha (pass) e um
volume para persistir os dados, todas essas informações estão presentes
no arquivo **docker-compose.yaml**.

Esse setup é ideal para desenvolvimento local, já que você terá um
MongoDB configurado e rodando com persistência de dados. No entanto,
atente-se que o usuário e senha escolhidos só devem ser usados nesse
ambiente de desenvolvimento, **pass** não é uma senha muito confiável...

## Criando a API para servir a pipeline

O código do arquivo **httpserver.py** cria uma API simples usando o
Quart, que é um framework web similar ao Flask, porém com suporte nativo
para operações assíncronas. Ele integra um sistema de busca semântica
utilizando o Google Gemini e MongoDB Atlas. A API recebe requisições
HTTP POST contendo uma pergunta e responde com dados processados a
partir dos PDFs indexados.

Sendo assim, copie o código do arquivo **httpserver.py** para o seu
arquivo.

O objetivo da rota **/gemini** é receber um prompt (pergunta) e usar a
função rag_gemini() para buscar respostas nos documentos PDF indexados.
O **corpo** da requisição aceito por esta rota é composto por:

-   prompt: A pergunta que será usada para buscar nos documentos;

-   stream: (opcional) Indica se a resposta deve ser enviada em pedaços
    (streaming).

A vantagem de fazer com que o streaming seja opcional é que, quando
desativado, facilita a leitura das respostas nos testes.

## Criando a pipeline RAG

Primeiramente, copie o arquivo **rag_gemini.py** para o seu arquivo.

Este código implementa uma integração para buscar documentos em uma base
de dados MongoDB Atlas, utilizando um modelo de embeddings do Gemini
para realizar buscas semânticas e fornecer respostas concisas.

A fim de facilitar a compreensão do papel de cada método presente no
arquivo, foi elaborada a seguinte listagem:

-   **load_docs_from_directory()** Carrega todos os documentos em
    formato PDF de um diretório específico (definido nas configurações).
    Usa **pymupdf4llm.to_markdown()** para converter os PDFs em texto
    Markdown. Divide o conteúdo do Markdown em fragmentos menores usando
    MarkdownTextSplitter. Retorna os documentos em forma de uma lista
    processada para facilitar o armazenamento e busca.

-   **setup_gemini_embeddings()** Inicializa o modelo de embeddings da
    Google Gemini usando a chave de API fornecida nas configurações.
    Esse modelo é usado para converter texto em embeddings (vetores) que
    podem ser utilizados para busca semântica.

-   **setup_atlas(embeddings)** Conecta-se ao MongoDB Atlas utilizando a
    URL fornecida nas configurações. Além disso, verifica se o banco de
    dados existe e, caso o banco de dados não exista, chama a função
    load_docs_from_directory() para carregar e inserir os documentos no
    MongoDB Atlas.

-   **setup_search_index_if_not_exists(atlas_collection)** Verifica se o
    índice de busca vetorial já existe no MongoDB Atlas. Se o índice não
    existir, ele é criado com as configurações apropriadas (neste caso,
    para o modelo de embedding text_embedding_004, com 768 dimensões e
    similaridade cosine).

-   **drop_database()** Exclui o banco de dados MongoDB definido nas
    configurações. Essa função é útil para redefinir o estado do banco
    de dados.

-   **check_index()** Verifica o status do índice de busca no MongoDB
    Atlas.

-   **setupGeminiModel()** Inicializa o modelo generativo Gemini para
    gerar conteúdo baseado em prompts.

-   **pdf_response(question: str, stream: bool)** Este método é responsável
    pela execução da pipeline. Se o parâmetro **stream** for True, as
    respostas são geradas de forma assíncrona (em tempo real); caso
    contrário, são retornadas de uma vez.

Com isso, agora você já tem todos os arquivos necessários para executar
a sua pipeline. Vamos para a etapa final!

## Etapa final

Agora chegou o momento mais esperado, vamos colocar a API para funcionar
e testar a pipeline! Para isso, certifique-se que os PDFs estão na
pasta, o contêiner do MongoDB Atlas está rodando e que a chave da API do
Gemini está no arquivo **.env**.

Caso esteja tudo ok, execute o arquivo **httpserver.py**, para isso,
execute o seguinte comando no terminal:

```
python httpserver.py
```

Se não houver nenhum problema com a API e as dependências, a API será
inicializada, informando que está sendo executada no endereço
**http://127.0.0.1:8000**.

Como o vector store está vazio, a primeira vez que a API receber uma
requisição, os PDFs passarão pelo processo de indexação. Logo, além de
demorar um pouco mais, a resposta referente a pergunta não será
retornada nesta primeira requisição. Além disso, uma característica do
Atlas é que, assim que um index de busca é criado, é necessário esperar
alguns segundos para que você possa de fato buscar alguma informação na
base.

Depois de alguns segundos, repita a requisição e verifique o retorno. Se
o índice de busca já estiver completamente iniciado, a pipeline irá
retornar a resposta referente à sua pergunta.

Com isso, você acaba de implementar uma API que serve uma pipeline de
RAG, utilizando um vector store robusto e um LLM via API. Sinta-se livre
para modificar a pipeline, testar outras tecnologias, transformá-la em
uma pipeline de Advanced RAG ou até mesmo integrar ela a um frontend e
desenvolver uma aplicação completa.