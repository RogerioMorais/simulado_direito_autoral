"""Verificação funcional das atividades com os recursos da aula.

Com o container ligado, execute: python3 verificar_demo.py
Este roteiro chama a interface HTTP de verdade, baixa modelos se necessário
 e gera relatórios de teste em resultados/. Não precisa de bibliotecas extras.
"""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ADDRESS = 'http://127.0.0.1:8091'


def post(route, payload):
    request = urllib.request.Request(ADDRESS + '/api/' + route,
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=900) as response:
        return json.load(response)


def files(folder):
    return {'arquivos': [{'nome': p.name, 'conteudo': base64.b64encode(p.read_bytes()).decode()}
                        for p in sorted((BASE / 'recursos_exemplo' / folder).iterdir()) if p.is_file()]}


def main():
    # Verifica os materiais servidos pela mesma aplicação usada pelos alunos.
    with urllib.request.urlopen(ADDRESS + '/') as response:
        assert 'Processo de criação' in response.read().decode()
    with urllib.request.urlopen(ADDRESS + '/recursos/recursos_para_aula.zip') as response:
        assert response.read(2) == b'PK'
    print('Página e pacote de recursos: OK', flush=True)

    result = post('criacao', files('criacao'))
    assert len(result['cronologia']) == 5
    assert result['cronologia'][0]['data_declarada'] == '2026-03-01'
    assert result['cronologia'][-1]['data_declarada'] is None
    assert len(result['versoes_visuais']) == 4
    assert result['comparacao']['mapa_alteracoes'].startswith('data:image/png;base64,')
    # Confere a mudança conhecida: de personagem pronta para cartaz com título.
    payload = files('criacao')
    names = [f['nome'] for f in payload['arquivos']]
    payload.update(antes=names.index('03_versao_personagem.png'), depois=names.index('04_cartaz_final.png'))
    visual = post('criacao', payload)['comparacao']
    assert visual['pixels_alterados'] > 0
    assert visual['retangulo_alteracoes'] == [40, 45, 681, 231]
    payload['antes'] = payload['depois']
    identical_versions = post('criacao', payload)['comparacao']
    assert identical_versions['pixels_alterados'] == 0
    print('Criação: ordem cronológica e documento sem data OK', flush=True)

    # Um livro pode ser investigado sem nenhuma imagem: mudanças, declaração e final.
    book = files('livro')
    names = [row['nome'] for row in book['arquivos']]
    book.update(modo='texto', anterior=names.index('03_saida_ia_simulada.txt'),
                revisada=names.index('04_versao_revisada.txt'), final=names.index('05_manuscrito_final.txt'),
                registro=names.index('06_registro_revisao.txt'))
    result = post('criacao', book)
    assert not result['versoes_visuais']
    analysis = result['analise_textual']
    assert 'indícios' in analysis['resposta']
    checks = [item for change in analysis['alteracoes'] for item in change['conferencia_final']]
    assert any(item['presente_literalmente'] for item in checks)
    assert any(not item['presente_literalmente'] for item in checks)
    book['revisada'] = None
    assert 'insuficiente' in post('criacao', book)['resposta']
    print('Livro: revisão sem imagens, permanência parcial e documentos insuficientes OK', flush=True)

    # O exercício ativo usa logs e separa escolhas do usuário das mensagens da IA.
    logs = files('logs')
    logs['modo'] = 'prompts'
    result = post('criacao', logs)
    assert len(result['analise_logs']) == 3
    assert result['modelo'].startswith('Qwen/')
    assert all(log['uso_tokens']['completion_tokens'] > 0 for log in result['analise_logs'])
    assert all(log['analise_modelo']['texto'] for log in result['analise_logs'])
    print('Logs: três níveis, delegação expressa e revisão posterior OK', flush=True)

    result = post('inventario', files('evidencias'))
    assert len(result['arquivos']) == 4
    assert len(result['duplicatas_identicas']) == 1
    assert len(result['duplicatas_identicas'][0]) == 2
    images = [row for row in result['arquivos'] if row['arquivo'].endswith(('.jpg', '.png'))]
    assert images[0]['sha256'] != images[1]['sha256']
    assert all('Curso Olhar na Rua' in row['texto_extraido'] for row in images)
    print('Inventário: duplicatas, hashes diferentes e OCR das duas imagens OK', flush=True)

    for name in ['01_comercial_com_credito.txt', '02_nao_comercial.txt']:
        text = (BASE / 'recursos_exemplo/licencas' / name).read_text()
        result = post('licenca', {'licenca': text, 'uso': 'Quero usar a imagem em anúncio comercial.'})
        assert result['modelo'].endswith('MiniLM-L12-v2')
        assert result['clausulas'][0]['trechos']
        assert all(row['trecho'] in text for row in result['trechos_por_proximidade'])
        if name.startswith('02'):
            assert any('proibido' in row.lower() for row in result['clausulas'][0]['trechos'])
    print('Licenças: cláusulas reais destacadas nas duas versões, incluindo proibição OK', flush=True)

    data = json.loads((BASE / 'dados/cenario.json').read_text())
    result = post('analisar', data)
    identical = post('analisar', {'referencia': data['referencia'], 'texto_comparado': data['referencia']})
    assert identical['similaridade'] > 0.99
    print('Textos: comparação preservada e identidade reconhecida OK', flush=True)

    # A referência é seguida por suas variantes. Acrescenta uma cópia exata para
    # verificar a comparação real do modelo sem pressupor a ordem das variantes.
    payload = files('imagens')
    payload['arquivos'].append({**payload['arquivos'][0], 'nome': 'copia_exata.png'})
    result = post('imagens', payload)
    copy = next(row for row in result['resultados'] if row['arquivo'] == 'copia_exata.png')
    assert copy['identica_em_bytes'] and copy['similaridade'] > 0.99
    print('Imagens: CLIP executado; cópia exata reconhecida OK', flush=True)
    print('Ordem visual:', [(r['arquivo'], r['similaridade']) for r in result['resultados']], flush=True)

    # Verifica que entrada imprópria é recusada em vez de produzir um relatório.
    try:
        post('inventario', {'arquivos': [{'nome': 'invalido.exe', 'conteudo': 'YQ=='}]})
    except urllib.error.HTTPError as error:
        assert error.code == 400
    else:
        raise AssertionError('Arquivo não permitido foi aceito.')
    print('Entrada inválida recusada: OK', flush=True)


if __name__ == '__main__':
    main()
