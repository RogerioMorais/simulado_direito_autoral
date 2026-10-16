"""Investiga versões textuais sem confundir diferença com prova de autoria.

O aluno identifica a função de cada arquivo. O programa não adivinha quem escreveu.
Comparamos frases, localizamos trechos na versão final e mostramos declarações do
registro. Tudo é uma automação determinística, sem uma decisão jurídica por IA.
"""
import difflib
import re


def investigate(data, files):
    """Recebe os arquivos já validados e as funções escolhidas no formulário."""
    def document(role):
        index = data.get(role)
        if index is None:
            return None
        if type(index) is not int or not 0 <= index < len(files):
            raise ValueError('Selecione arquivos válidos para as funções do processo.')
        file = files[index]
        if file['extensao'] not in {'.txt', '.md'}:
            raise ValueError('Para comparação textual, use TXT ou MD em UTF-8.')
        try:
            text = file['bytes'].decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError('Salve os documentos em UTF-8.') from exc
        if len(text) > 20000:
            raise ValueError('Cada documento do processo textual deve ter até 20.000 caracteres.')
        return {'arquivo': file['nome'], 'texto': text}

    before, revised, final, record = [document(role) for role in ['anterior', 'revisada', 'final', 'registro']]
    result = {'arquivos_por_funcao': {role: doc['arquivo'] if doc else None for role, doc in
              [('anterior', before), ('revisada', revised), ('final', final), ('registro', record)]},
              'alteracoes': [], 'declaracoes': [],
              'atribuicao': 'A identidade de quem realizou as mudanças não é autenticada pelo programa.'}
    # Mostramos o trecho que sustenta a declaração, em vez de deduzir identidade.
    if record:
        result['declaracoes'] = [line.strip() for line in record['texto'].splitlines()
            if re.search(r'reescrev|escrev|revis|autoria|interven|human|diálogo', line, re.I)][:12]
    if not before or not revised:
        result['resposta'] = 'Documentação insuficiente para verificar intervenção: faltam a versão de partida e/ou a versão revisada identificadas.'
        result['incorporacao'] = 'Não foi possível confrontar alterações com o resultado final.'
        return result

    def sentences(text):
        # Trabalhamos com frases/linhas. Uma frase modificada aparece como substituição;
        # isso não significa que todas as suas palavras tenham sido criadas novamente.
        items = [re.sub(r'\s+', ' ', part).strip() for part in re.split(r'(?<=[.!?])\s+|\n+', text)]
        items = [item for item in items if item]
        if len(items) > 600:
            raise ValueError('Use documentos com até 600 frases/linhas para a demonstração.')
        return items

    old, new = sentences(before['texto']), sentences(revised['texto'])
    final_text = re.sub(r'\s+', ' ', final['texto']).strip() if final else None
    changes = []
    for tag, i, j, k, l in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        added = new[k:l]
        changes.append({'tipo': {'insert': 'Inclusão', 'delete': 'Exclusão', 'replace': 'Substituição'}[tag],
                        'antes': old[i:j], 'depois': added,
                        # Presença literal normaliza espaços, mas não reconhece paráfrases.
                        'conferencia_final': [{'trecho': text, 'presente_literalmente': text in final_text if final else None}
                                             for text in added]})
    total = len(changes)
    result['total_blocos_alterados'] = total
    result['alteracoes'] = changes[:30]
    result['exibicao_limitada'] = total > 30
    if not total:
        result['resposta'] = 'Não foram encontradas mudanças textuais entre as versões escolhidas. Isso não exclui outras formas de participação humana.'
    elif record and any(re.search(r'\b(eu|nós)\s+(reescrevi|escrevi|revisei|redigi|acrescentei|reescrevemos|escrevemos|revisamos)\b', line, re.I) for line in result['declaracoes']):
        result['resposta'] = 'Há indícios de intervenção humana declarada nos registros, acompanhados de mudanças verificáveis entre as versões. A atribuição à pessoa ainda precisa ser confirmada.'
    else:
        result['resposta'] = 'Há mudanças verificáveis, mas não foi localizada uma declaração explícita de escrita/revisão em primeira pessoa nos registros examinados. Isso não exclui intervenção humana; confira os documentos.'
    additions = [item for change in changes for item in change['conferencia_final']]
    found = sum(item['presente_literalmente'] is True for item in additions)
    result['incorporacao'] = (f'{found} de {len(additions)} frases/linhas acrescentadas ou substituídas foram localizadas literalmente no arquivo final.'
                              if final else 'Não há versão final identificada para conferir a permanência das mudanças.')
    result['metodo'] = 'Comparação de frases/linhas; conferência literal no final após normalizar espaços. Não reconhece equivalências semânticas ou autentica relatos.'
    return result
