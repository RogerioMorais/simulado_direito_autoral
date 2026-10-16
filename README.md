# Investigação de propriedade intelectual — demonstração local

Aplicação web em Python para experimentar automações relacionadas à investigação de propriedade intelectual. Funciona em container, com arquivos de exemplo fictícios e código comentado em português.

## Executar

Requisitos: Docker com Docker Compose, acesso à internet para preparar a imagem e baixar os modelos, alguns GB de disco e memória disponível para um container de até 4 GB. Não exige chave de API nem placa de vídeo.

No terminal, dentro da pasta deste repositório:

```bash
docker compose up --build -d
```

Abra **http://localhost:8091**. A porta é acessível apenas no computador local. Se já houver uma instância da aplicação nessa porta, encerre-a antes ou altere a porta à esquerda em `compose.yaml`.

O primeiro uso de uma atividade com IA baixa seu modelo para `cache/`. Esse preparo pode levar alguns minutos. Depois, as análises usam o container local. Os arquivos enviados não são encaminhados a uma API externa de análise.

```bash
# Acompanhar mensagens; Ctrl+C encerra apenas o acompanhamento.
docker compose logs -f demonstracao

# Encerrar os containers.
docker compose down
```

## Funcionalidades

| Atividade | Entrada | Resultado e método |
|---|---|---|
| Imagens semelhantes | Referência e candidatas PNG/JPG/WEBP | Ordenação por similaridade com CLIP. |
| Processo de criação — logs | Logs TXT/MD enviados pelo usuário | Citações de decisões, delegações e aspectos sem detalhe localizado, por regras de padrões. Não utiliza modelo de linguagem. |
| Processo de criação — imagens | Versões visuais e registros | Imagens lado a lado, mapa matemático de pixels alterados e cronologia auxiliar. |
| Licença de uso | Licença e uso pretendido | Trechos próximos ao pedido com MiniLM e destaques por palavras. |
| Inventário de evidências | TXT/MD e imagens | Texto extraído, OCR, hashes SHA-256 e agrupamento de bytes idênticos. |
| Comparação de textos | Texto de referência e texto a comparar | Proximidade de sentido com MiniLM. |

Os escores não são porcentagens de plágio. Diferenças visuais não identificam quem editou. Detalhamento de prompts não garante autoria. Nenhuma atividade emite decisão jurídica ou autentica identidade, datas e origem dos documentos.

## Usar os arquivos de exemplo

Os recursos ficam em `recursos_exemplo/`. A interface também permite baixar o pacote ZIP. Extraia-o antes de selecionar arquivos.

### Logs de prompts

1. Abra **Processo de criação** e mantenha o modo **Logs de prompts**.
2. Envie `recursos_exemplo/logs/01_generico.txt` pelo seletor normal de arquivos e execute.
3. Limpe a lista e repita com `02_direcao_de_cena.txt` e `03_detalhado_iterativo.txt`, ou envie os três juntos.
4. Examine os trechos atribuídos às mensagens do usuário e o que foi delegado à IA.

Para arquivos próprios, use TXT/MD em UTF-8, até 20.000 caracteres por log. Identifique as mensagens assim:

```text
USUÁRIO:
Escreva uma cena...
IA:
Minha proposta...
USUÁRIO:
Modifique o desfecho...
```

Sem marcadores, o arquivo inteiro é tratado como prompt fornecido, com aviso. Os papéis são declarações do arquivo, sem autenticação. As regras podem deixar decisões sem destaque ou perder contexto; confira o log integral. Nas interações seguintes, as instruções novas são localizadas por comparação literal.

### Comparações de imagens

Na aba **Imagens semelhantes**, selecione a referência e as candidatas de `recursos_exemplo/imagens/`.

Para comparar versões do cartaz, abra **Processo de criação**, selecione **Comparação de imagens** e envie os PNG de `recursos_exemplo/criacao/`. Selecione versões anterior e posterior e execute. O projeto editável está em `criacao/fontes/cartaz_editavel.svg`. O mapa marca diferenças acima de 24 níveis por canal RGB; dimensões diferentes não geram mapa.

### Licença, inventário e comparação textual

- **Licença:** experimente os TXT de `recursos_exemplo/licencas/` e descreva o uso pretendido. Os documentos são fictícios, não autorizações reais. Até 12.000 caracteres na licença e 1.000 no pedido.
- **Inventário:** envie os arquivos de `recursos_exemplo/evidencias/`. Os dois TXT são cópias exatas; as imagens PNG e JPG têm o mesmo conteúdo aparente, mas hashes diferentes. Confira o OCR com os originais.
- **Textos:** preencha os dois campos, com até 2.000 caracteres cada. O exemplo inicial está em `dados/cenario.json`.

Seleções sucessivas acrescentam arquivos à lista. Use **Remover** ou **Limpar lista de arquivos**. Limites gerais: 12 arquivos, 2 MB por arquivo, 16 milhões de pixels por imagem. Não há upload de PDF, áudio, vídeo ou ZIP. Os originais enviados não são arquivados: preserve-os separadamente.

Todos os materiais são simulados. Os desenhos e versões visuais foram feitos por código; a suposta saída de IA do cartaz não é uma geração real.

## Relatórios e cache

Os relatórios JSON são gravados em `resultados/` e podem ser baixados pela tela. Incluem textos processados e podem conter informações fornecidas pelo usuário. `cache/` guarda os modelos. Ambos estão excluídos do versionamento, exceto pelos arquivos vazios `.gitkeep`.

Após executar com sucesso as atividades CLIP e MiniLM online, pode-se forçar o uso do cache:

```bash
docker compose -f compose.yaml -f compose.offline.yaml up -d --force-recreate
```

O modo impede downloads pelas bibliotecas de modelos, mas não isola toda a rede do container. Se faltar um arquivo do modelo, a atividade falha. Para voltar: `docker compose up -d --force-recreate`.

## Estrutura do código

- `demo.py`: servidor HTTP, modelos e relatórios.
- `atividades.py`: comparação visual, licenças, inventário e encaminhamento da análise de criação.
- `analise_prompts.py`: leitura de logs por padrões com citações.
- `autoria_textual.py`: comparação de versões textuais mantida para compatibilidade da API.
- `web/index.html`: interface e upload de arquivos.
- `dados/`: cenário textual inicial.
- `recursos_exemplo/`: arquivos de entrada fictícios necessários às demonstrações e testes.
- `gerar_recursos.py`, `gerar_cartaz.py`, `gerar_livro.py`: geração dos recursos visuais e textuais. Requerem Pillow; os arquivos já vêm prontos. Logs são arquivos estáticos.
- `verificar_demo.py`: verificação funcional via HTTP.
- `Dockerfile`, `compose.yaml`, `compose.offline.yaml`, `requirements.txt`: ambiente de execução.

## Verificação funcional

Com o serviço ligado e Python 3 disponível no computador:

```bash
python3 verificar_demo.py
```

O script usa os arquivos fictícios para verificar OCR, duplicatas, comparação visual e textual, licenças e logs. Pode baixar os modelos no primeiro uso e gera relatórios de teste. Não exige bibliotecas Python adicionais no computador.

## Criar o repositório no GitHub

Esta pasta contém a cópia independente do projeto. Na raiz dela:

```bash
git init -b main
git add .
git commit -m "Adiciona demonstração de investigação de propriedade intelectual"
```

Crie um repositório vazio na sua conta do GitHub. Depois, substitua `SEU_USUARIO` e `SEU_REPOSITORIO`:

```bash
git remote add origin https://github.com/RogerioMorais/simulado_direito_autoral.git
git push -u origin main
```

## Referências técnicas

- [CLIP / Sentence Transformers](https://huggingface.co/sentence-transformers/clip-ViT-B-32).
- [MiniLM multilíngue](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).
