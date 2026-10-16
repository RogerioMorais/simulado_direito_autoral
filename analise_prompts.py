"""Leitura didática de logs: escolhas explicitadas pela pessoa e pontos em aberto.

É uma busca por padrões com citações, não um juiz de autoria. As mensagens da IA
são separadas: escolhas que aparecem só nelas não são atribuídas ao usuário.
"""
import re

# Cada tema tem indicadores explícitos. Não contamos palavras como criatividade.
TOPICS = {
 'Personagens e relações': r'rapazes|jovem|Lia|Caio|Beto|personagem.*(?:chamad|nome)|irmã|irmão',
 'Ambiente e objetos': r'drive.?in|carro vermelho|carro.*vermelh|lanchonete.*(?:noite|23)|chuva|letreiro',
 'Enquadramento e câmera': r'plano aberto|close|plano médio|câmera|enquadramento',
 'Ações e gestos': r'aperta|segura|desvia|olha|bate|abaixa|imobil|mãos|mão',
 'Tensão e intenção narrativa': r'tens[oa]|desconfort|não est[áa] [àa] vontade|não.*vontade|perceb|suspeit|agitado',
 'Montagem e duração': r'corta|corte|segundos|transição|montagem',
 'Luz, cor e som': r'ilumina|luz|silêncio|som|trilha|vermelh|azul|amarelo',
 'Diálogos escritos': r'(?:Lia|Caio|Beto|Atendente)\s*[:—]|(?:fala|diz|responde)\s*[:—]\s*[“"\']',
}
OPENING = re.compile(r'^\s*(USU[ÁA]RIO|HUMANO|IA|ASSISTENTE)\s*:\s*(.*)$', re.I)
DELEGATED = re.compile(r'a seu critério|a critério da ia|decida|invente|deixe.*(?:ia|modelo).*decidir|não (?:defina|especifique)', re.I)


def turns(text):
    """Reconhece USUÁRIO: e IA:; ignora metadados anteriores ao primeiro papel."""
    rows = []
    for line in text.splitlines():
        match = OPENING.match(line)
        if match:
            role = 'humano' if match[1].upper() in ['USUÁRIO', 'USUARIO', 'HUMANO'] else 'ia'
            rows.append({'papel': role, 'texto': match[2]})
        elif rows:
            rows[-1]['texto'] += '\n' + line
    # Um texto sem marcadores é tratado como prompt fornecido, com aviso explícito.
    return rows or [{'papel': 'humano', 'texto': text}]


def analyze(data, files):
    """Não exige imagem nem obra final: examina apenas o que o log documenta."""
    results = []
    for file in files:
        if file['extensao'] not in {'.txt', '.md'}:
            raise ValueError('No modo logs, envie arquivos TXT ou MD. Use o modo visual para imagens.')
        try:
            text = file['bytes'].decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError('Salve o log em UTF-8.') from exc
        if len(text) > 20000:
            raise ValueError('Use logs com até 20.000 caracteres por arquivo.')
        exchanges = turns(text)
        seen = set()
        human_rows = []
        for number, turn in enumerate(exchanges, 1):
            if turn['papel'] != 'humano':
                continue
            # Preservamos falas por linha, sem quebrar sua identificação de personagem.
            fragments = [part.strip() for part in re.split(r'\n+|(?<=[.!?])\s+', turn['texto']) if part.strip()]
            explicit = [part for part in fragments if not DELEGATED.search(part)]
            decisions = []
            for title, pattern in TOPICS.items():
                matches = [part for part in explicit if re.search(pattern, part, re.I)]
                if matches:
                    decisions.append({'tema': title, 'trechos': matches[:5]})
            added = [part for part in fragments if part not in seen]
            seen.update(fragments)
            human_rows.append({'mensagem': number, 'texto_usuario': turn['texto'].strip(),
                               'decisoes': decisions, 'instrucoes_novas': added[:20],
                               'delegacoes_expressas': [part for part in fragments if DELEGATED.search(part)]})
        found = {item['tema'] for row in human_rows for item in row['decisoes']}
        if not human_rows:
            reading = 'Não há mensagem do usuário identificada; decisões da IA não foram atribuídas à pessoa.'
        elif len(found) <= 1:
            reading = 'Pedido amplo: poucos dos aspectos expressivos procurados foram especificados. O desenvolvimento permanece amplamente aberto à IA.'
        else:
            reading = 'Há escolhas específicas documentadas nas mensagens do usuário. Examine as citações e o que ainda ficou aberto à IA.'
        results.append({'arquivo': file['nome'], 'leitura': reading, 'mensagens_humanas': human_rows,
                        'aspectos_sem_detalhe_localizado': sorted(set(TOPICS) - found),
                        'mensagens_ia_separadas': sum(row['papel'] == 'ia' for row in exchanges),
                        'aviso_formato': None if any(OPENING.match(line) for line in text.splitlines()) else
                        'Sem marcadores de papel: todo o arquivo foi tratado como prompt fornecido. Confira se não contém texto da IA misturado.'})
    return {'modo': 'prompts', 'analise_logs': results, 'cronologia': [], 'comparacao': None,
            'resposta': 'A análise localiza escolhas expressas nos prompts e aspectos sem detalhamento localizado. Não determina autoria nem confirma que a saída executou as instruções.',
            'perguntas': ['Quais decisões foram explicitadas pela pessoa?',
                         'O que foi delegado ou permaneceu sem detalhamento?',
                         'O que a pessoa acrescentou nas interações seguintes?',
                         'A obra gerada incorporou essas escolhas? Isso exige examinar a saída.'],
            'limite': 'Regras por palavras podem perder contexto, negações e escolhas implícitas. Ausência de destaque não prova ausência de decisão. Os papéis USUÁRIO/IA são declarações do log, sem autenticação. Mais detalhes não garantem autoria sobre o resultado.'}
