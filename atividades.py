"""Quatro atividades didáticas de investigação em propriedade intelectual.

Cada função recebe dados e devolve um relatório que pode ser revisto por pessoas.
Há IA na comparação visual (CLIP) e na localização semântica de cláusulas (MiniLM).
Cronologia, hashes, regras e OCR são automações específicas, não pareceres jurídicos.
"""
import analise_prompts
import autoria_textual
import base64
import hashlib
import io
import re
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps, ImageChops, ImageDraw, UnidentifiedImageError

# Limites mantêm a demonstração leve. Não se aceitam programas, ZIPs ou PDFs.
MAX_FILES = 12
MAX_BYTES = 2 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 16_000_000
IMAGE_TYPES = {'.png', '.jpg', '.jpeg', '.webp'}
TEXT_TYPES = {'.txt', '.md'}


def read_files(data):
    """Lê arquivos enviados como base64 (uma forma de transportar bytes em JSON)."""
    files = data.get('arquivos', [])
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise ValueError('Selecione entre 1 e 12 arquivos.')
    clean = []
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get('conteudo'), str):
            raise ValueError('Arquivo inválido.')
        name = Path(str(item.get('nome', 'arquivo'))).name[:160]
        suffix = Path(name).suffix.lower()
        if suffix not in IMAGE_TYPES | TEXT_TYPES:
            raise ValueError(f'{name}: use TXT, MD, PNG, JPG ou WEBP.')
        # Checa o tamanho antes e depois de decodificar, sem executar o conteúdo.
        if len(item['conteudo']) > MAX_BYTES * 4 // 3 + 8:
            raise ValueError('Cada arquivo deve ter até 2 MB.')
        try:
            raw = base64.b64decode(item['conteudo'], validate=True)
        except ValueError as exc:
            raise ValueError('Conteúdo de arquivo inválido.') from exc
        if not raw or len(raw) > MAX_BYTES:
            raise ValueError('Arquivo vazio ou maior que 2 MB.')
        clean.append({'nome': name, 'bytes': raw, 'extensao': suffix})
    return clean


def open_image(raw):
    """Converte imagens para o mesmo formato de cor e corrige orientação EXIF."""
    try:
        image = Image.open(io.BytesIO(raw))
        if image.width * image.height > 16_000_000:
            raise ValueError('Use imagens com até 16 milhões de pixels.')
        return ImageOps.exif_transpose(image).convert('RGB')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('Não foi possível ler uma imagem.') from exc


def extract_text(file):
    """Lê texto UTF-8 ou reconhece letras de uma imagem com Tesseract (OCR)."""
    if file['extensao'] in TEXT_TYPES:
        try:
            return file['bytes'].decode('utf-8-sig'), 'Texto UTF-8'
        except UnicodeDecodeError as exc:
            raise ValueError(f"Salve {file['nome']} como texto UTF-8.") from exc
    image = open_image(file['bytes'])
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    # stdin/stdout permitem trabalhar na memória, sem criar um arquivo temporário.
    # O OCR pode errar: seu resultado sempre precisa de conferência com a imagem.
    try:
        run = subprocess.run(['tesseract', 'stdin', 'stdout', '-l', 'por+eng'],
                             input=buffer.getvalue(), capture_output=True, timeout=30, check=True)
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        raise ValueError('Falha no OCR. Confira a imagem e a instalação do Tesseract.') from exc
    return run.stdout.decode('utf-8').strip(), 'OCR Tesseract (português e inglês)'


def images(data, load_model):
    """Ordena candidatos pela semelhança com a primeira imagem (referência)."""
    files = read_files(data)
    if len(files) < 2 or any(f['extensao'] not in IMAGE_TYPES for f in files):
        raise ValueError('Envie a referência e pelo menos uma candidata, todas imagens.')
    model = load_model('visual')
    vectors = model.encode([open_image(f['bytes']) for f in files], normalize_embeddings=True)
    rows = []
    for i, file in enumerate(files[1:], 1):
        # Produto de vetores normalizados = similaridade cosseno.
        # O CLIP pode aproximar imagens do mesmo tema sem que uma copie a outra.
        rows.append({'arquivo': file['nome'], 'similaridade': round(float(vectors[i] @ vectors[0]), 4),
                     'identica_em_bytes': file['bytes'] == files[0]['bytes'],
                     'sha256': hashlib.sha256(file['bytes']).hexdigest()})
    rows.sort(key=lambda row: row['similaridade'], reverse=True)
    return {'referencia': files[0]['nome'],
            'sha256_referencia': hashlib.sha256(files[0]['bytes']).hexdigest(),
            'metodo': 'Similaridade cosseno entre embeddings visuais CLIP normalizados.',
            'resultados': rows,
            'limite': 'Semelhança visual não comprova reprodução, autoria ou infração. Recortes e cores podem alterar a ordem.'}


# A cronologia encontra vestígios documentados, sem declarar que são suficientes.
CATEGORIES = {
    'Roteiro / narrativa': r'roteiro|diálogo|narrativa',
    'Esboço / personagem': r'esboço|personagem|desenho',
    'Instruções à IA': r'prompt|instruções à ia',
    'Direção / enquadramento': r'enquadramento|iluminação|direção',
    'Edição / montagem': r'edição|montagem|corte|correção de cor',
}


def chronology(data):
    """Organiza datas declaradas e trechos relevantes; não autentica os documentos."""
    files = read_files(data)
    if data.get('modo') == 'prompts':
        return analise_prompts.analyze(data, files)
    rows, found, visual = [], set(), []
    for index, file in enumerate(files):
        # Imagens são versões para confronto visual. Não confundimos letras do
        # cartaz (OCR) com datas ou registros da história de sua produção.
        if file['extensao'] in IMAGE_TYPES:
            visual.append({'indice': index, 'arquivo': file['nome'],
                           'sha256': hashlib.sha256(file['bytes']).hexdigest()})
            continue
        text, method = extract_text(file)
        dates = []
        # Só aceita datas válidas AAAA-MM-DD. Não usa a data do upload como criação.
        for value in re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text):
            try:
                date.fromisoformat(value)
                dates.append(value)
            except ValueError:
                pass
        evidence = []
        for label, pattern in CATEGORIES.items():
            line = next((line.strip() for line in text.splitlines() if re.search(pattern, line, re.I)), None)
            if line:
                found.add(label)
                evidence.append({'categoria': label, 'trecho': line[:600]})
        rows.append({'arquivo': file['nome'], 'sha256': hashlib.sha256(file['bytes']).hexdigest(),
                     'data_declarada': min(dates) if dates else None,
                     'outras_datas_encontradas': sorted(set(dates)), 'extracao': method, 'indicios': evidence})
    rows.sort(key=lambda row: row['data_declarada'] or '9999')
    mode = data.get('modo', 'imagem')
    if mode not in ['texto', 'imagem']:
        raise ValueError('Escolha processo textual ou visual.')
    textual = autoria_textual.investigate(data, files) if mode == 'texto' else None
    comparison = None
    if mode == 'imagem' and len(visual) >= 2:
        # O aluno escolhe os pares; a posição é na lista de arquivos recebida.
        before = data.get('antes', visual[0]['indice'])
        after = data.get('depois', visual[-1]['indice'])
        allowed = {row['indice'] for row in visual}
        if type(before) is not int or type(after) is not int or before not in allowed or after not in allowed:
            raise ValueError('Escolha duas versões de imagem válidas.')
        comparison = compare_versions(files[before], files[after])
    return {'modo': mode, 'analise_textual': textual,
            'resposta': textual['resposta'] if textual else ('Há alterações visuais entre as versões; os registros precisam sustentar sua atribuição a uma pessoa.' if comparison and comparison.get('pixels_alterados', 0) else 'Os materiais não permitem confirmar intervenção humana automaticamente.'),
            'cronologia': rows, 'versoes_visuais': visual, 'comparacao': comparison,
            'categorias_sem_mencao': sorted(set(CATEGORIES) - found),
            'perguntas': ['A mudança observada corresponde ao relato de edição?',
                          'Quais escolhas documentadas aparecem na versão final da obra?',
                          'Há arquivo editável e histórico que sustentem a atribuição à pessoa?',
                          'Quais partes permanecem sem documentação de origem?'],
            'limite': 'Diferenças mostram alterações entre arquivos, não quem as fez nem se há autoria suficiente. Datas e relatos não são autenticados. Os exemplos são simulados; diferenças e relatos não constituem reconhecimento jurídico de autoria.'}


def compare_versions(before_file, after_file):
    """Confronta pixels alinhados e marca mudanças; não atribui autoria humana."""
    before, after = open_image(before_file['bytes']), open_image(after_file['bytes'])
    result = {'antes': before_file['nome'], 'depois': after_file['nome'],
              'sha256_antes': hashlib.sha256(before_file['bytes']).hexdigest(),
              'sha256_depois': hashlib.sha256(after_file['bytes']).hexdigest()}

    def preview(image):
        # Prévias menores deixam a interface e o relatório mais leves.
        image = image.copy()
        image.thumbnail((800, 900))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()

    result['imagem_antes'] = preview(before)
    result['imagem_depois'] = preview(after)
    if before.size != after.size:
        # Não deformamos uma versão para encaixar na outra: isso fabricaria diferenças.
        result['aviso'] = 'As dimensões são diferentes. Confira recorte, escala e alinhamento antes de comparar pixels. Não foi gerado mapa de alterações.'
        return result
    difference = ImageChops.difference(before, after)
    red, green, blue = difference.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    # Desconsidera mudanças de até 24 níveis (escala 0 a 255) por canal de cor.
    # É um parâmetro didático, não um critério jurídico. JPEG pode gerar ruído.
    mask = maximum.point(lambda value: 255 if value > 24 else 0)
    count = mask.histogram()[255]
    overlay = Image.composite(Image.blend(after, Image.new('RGB', after.size, '#ff2255'), .65), after, mask)
    box = mask.getbbox()
    if box:
        ImageDraw.Draw(overlay).rectangle(box, outline='#ff2255', width=4)
    result.update({'mapa_alteracoes': preview(overlay), 'pixels_alterados': count,
                   'pixels_totais': before.width * before.height, 'limiar_por_canal': 24,
                   'retangulo_alteracoes': list(box) if box else None,
                   'aviso': 'Rosa indica pixels alterados acima do limiar. Movimento, compressão e cor também produzem diferenças. Isto não mede a participação humana nem comprova quem editou.'})
    return result


def license_review(data, load_model):
    """Localiza trechos relevantes ao uso pretendido sem dar uma autorização."""
    text, intent = data.get('licenca', ''), data.get('uso', '')
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 12000:
        raise ValueError('Cole uma licença com até 12.000 caracteres.')
    if not isinstance(intent, str) or not 1 <= len(intent.strip()) <= 1000:
        raise ValueError('Descreva o uso pretendido em até 1.000 caracteres.')
    # Linhas e frases são divididas em trechos curtos para não exceder o modelo.
    pieces = []
    for line in text.splitlines():
        for part in re.split(r'(?<=[.!?;])\s+', line.strip()):
            words = part.split()
            pieces.extend(' '.join(words[i:i+45]) for i in range(0, len(words), 45))
    if not pieces:
        raise ValueError('Não foi possível encontrar texto na licença.')
    model = load_model('texto')
    vectors = model.encode(pieces, normalize_embeddings=True)
    query = model.encode(intent, normalize_embeddings=True)
    scores = vectors @ query
    order = sorted(range(len(pieces)), key=lambda i: float(scores[i]), reverse=True)[:4]
    topics = {'Uso comercial': r'comerci|anúncio|publicidade',
              'Alterações': r'alter|adapt|modific|recort',
              'Créditos': r'crédito|atribui|autoria',
              'Prazo / território': r'prazo|vigência|território|país|meses|dias'}
    # Busca literal complementar: permite ver a cláusula que motivou cada destaque.
    clauses = [{'tema': title, 'trechos': [p for p in pieces if re.search(pattern, p, re.I)]}
               for title, pattern in topics.items()]
    return {'uso': intent, 'trechos_por_proximidade': [
        {'trecho': pieces[i], 'similaridade': round(float(scores[i]), 4)} for i in order],
        'clausulas': clauses,
        'limite': 'A ferramenta localiza cláusulas; não conclui se o uso está autorizado. Negação, exceções, definições e outras cláusulas exigem leitura integral. Ausência de destaque não significa ausência de regra.'}


def inventory(data):
    """Calcula hashes dos bytes originais, extrai texto e agrupa cópias idênticas."""
    rows, groups = [], {}
    for index, file in enumerate(read_files(data), 1):
        digest = hashlib.sha256(file['bytes']).hexdigest()
        groups.setdefault(digest, []).append({'item': index, 'arquivo': file['nome']})
        text, method = extract_text(file)
        rows.append({'item': index, 'arquivo': file['nome'], 'tamanho_bytes': len(file['bytes']),
                     'sha256': digest, 'extracao': method, 'texto_extraido': text[:16000],
                     'texto_limitado': len(text) > 16000})
    return {'arquivos': rows, 'duplicatas_identicas': [g for g in groups.values() if len(g) > 1],
            'limite': 'Hash igual identifica bytes iguais. Não demonstra autoria, origem ou data histórica. O OCR pode errar. Os originais não são arquivados por este sistema: preserve-os separadamente.'}
