"""Cria recursos fictícios e reproduzíveis para a aula, sem imagens de terceiros.

Execute na pasta do computador: python3 gerar_recursos.py (requer Pillow).
Os desenhos são composições geométricas feitas por este código, sem IA generativa.
A pasta de exemplos precisa estar gravável para regenerar; os arquivos já vêm prontos.
"""
import shutil
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

BASE = Path(__file__).resolve().parent / 'recursos_exemplo'
for folder in ['imagens', 'criacao', 'licencas', 'evidencias']:
    (BASE / folder).mkdir(parents=True, exist_ok=True)

# Desenho geométrico de um barco: referência e variantes com alterações conhecidas.
image = Image.new('RGB', (640, 480), '#f4ead2')
draw = ImageDraw.Draw(image)
draw.ellipse((430, 35, 545, 150), fill='#e5a33f')
draw.rectangle((0, 330, 640, 480), fill='#3e8896')
draw.polygon([(160, 310), (490, 310), (425, 375), (220, 375)], fill='#8d503b')
draw.line([(320, 90), (320, 310)], fill='#302e31', width=9)
draw.polygon([(305, 105), (305, 292), (190, 292)], fill='#df5c49')
draw.polygon([(335, 130), (335, 292), (450, 292)], fill='#f7f4e8')
image.save(BASE / 'imagens/01_referencia_barco.png')
image.crop((110, 45, 560, 425)).resize((640, 480)).save(BASE / 'imagens/02_recorte_barco.png')
ImageEnhance.Color(image).enhance(0.15).save(BASE / 'imagens/03_cores_alteradas.png')
# Mesmo tema, composição diferente: serve para discutir falso indício de cópia.
other = Image.new('RGB', (640, 480), '#c5dae3')
d = ImageDraw.Draw(other)
d.rectangle((0, 240, 640, 480), fill='#244b75')
d.polygon([(55, 300), (245, 300), (200, 340), (85, 340)], fill='#f0ab40')
d.line((145, 120, 145, 300), fill='#252c30', width=5)
d.polygon([(153, 125), (153, 285), (245, 285)], fill='#eae9df')
d.ellipse((440, 50, 505, 115), fill='#fff2ad')
other.save(BASE / 'imagens/04_outro_barco.png')
unrelated = Image.new('RGB', (640, 480), '#343b30')
d = ImageDraw.Draw(unrelated)
d.rectangle((260, 245, 390, 440), fill='#8b5132')
d.ellipse((120, 30, 520, 350), fill='#73a75d')
unrelated.save(BASE / 'imagens/05_arvore.png')

# Gera o processo visual completo; todos os materiais são identificados como simulação.
import gerar_cartaz
import gerar_livro

licenses = {
 '01_comercial_com_credito.txt': '''LICENÇA FICTÍCIA PARA EXERCÍCIO — NÃO É UMA LICENÇA REAL
É permitido o uso comercial da ilustração em anúncios digitais.
É obrigatória a atribuição de crédito: Ilustração de Ana, personagem fictícia.
São permitidos recortes e alterações de cor.
É proibida a revenda do arquivo isolado.
O prazo desta autorização é de 12 meses, no território brasileiro.
''',
 '02_nao_comercial.txt': '''LICENÇA FICTÍCIA PARA EXERCÍCIO — NÃO É UMA LICENÇA REAL
É permitido compartilhar a imagem apenas para finalidade não comercial.
É proibido usar a imagem em publicidade, anúncios ou embalagens comerciais.
É obrigatória a atribuição de crédito.
Não são permitidas adaptações ou modificações.
''',
}
for name, text in licenses.items():
    (BASE / 'licencas' / name).write_text(text, encoding='utf-8')

# Evidências: duas cópias de bytes idênticos e uma imagem com texto para testar OCR.
text = 'REGISTRO FICTÍCIO\nTexto recebido em 2026-03-07.\nA descrição do curso foi reproduzida em um anúncio, segundo o relato recebido.\nA autorização e a data de publicação ainda precisam ser verificadas.\n'
(BASE / 'evidencias/01_relato.txt').write_text(text, encoding='utf-8')
shutil.copyfile(BASE / 'evidencias/01_relato.txt', BASE / 'evidencias/02_copia_relato.txt')
card = Image.new('RGB', (1200, 480), 'white')
d = ImageDraw.Draw(card)
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 30) if Path(font_path).exists() else ImageFont.load_default()
for y, line in enumerate(['EXERCICIO FICTICIO - DOCUMENTO PARA OCR',
                           'Data declarada: 2026-03-08',
                           'Curso Olhar na Rua - fotografia e narrativa visual.',
                           'Conferir licenca e autoria antes de concluir.']):
    d.text((40, 50 + y * 85), line, fill='black', font=font)
card.save(BASE / 'evidencias/03_anuncio_para_ocr.png')
# A mesma imagem com outra codificação muda os bytes e, portanto, o hash.
card.save(BASE / 'evidencias/04_mesmo_anuncio.jpg', quality=90)
# Pacote único para distribuição aos alunos; preserva a organização das subpastas.
with zipfile.ZipFile(BASE / 'recursos_para_aula.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(BASE.rglob('*')):
        if p.is_file() and p.suffix != '.zip':
            archive.write(p, p.relative_to(BASE))
print('Recursos fictícios criados em', BASE)
