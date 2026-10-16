"""Produz um processo SIMULADO de cartaz com arquivos visuais confrontáveis.

Todos os materiais são feitos por código. A imagem chamada base_ia representa
uma saída de IA no exercício, mas NÃO foi gerada por um modelo de IA.
O SVG final é editável: separa fundo, personagem e texto em grupos identificados.
"""
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent / 'recursos_exemplo/criacao'
ROOT.mkdir(parents=True, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(size):
    return ImageFont.truetype(FONT, size)

# O mesmo tamanho permite sobrepor versões sem distorcer a composição.
base = Image.new('RGB', (720, 900), '#dce7e8')
d = ImageDraw.Draw(base)
d.ellipse((470, 100, 610, 240), fill='#edb865')
d.polygon([(0, 430), (170, 260), (370, 470), (550, 300), (720, 420), (720, 900), (0, 900)], fill='#67878b')
d.rectangle((0, 610, 720, 900), fill='#376978')
base.save(ROOT / '02_base_ia_simulada.png')

sketch = Image.new('RGB', base.size, '#fcf7e9')
d = ImageDraw.Draw(sketch)
d.rectangle((35, 35, 685, 865), outline='#555555', width=3)
d.text((65, 65), 'ESBOCO - SIMULACAO', font=font(25), fill='#444444')
d.rectangle((65, 130, 650, 245), outline='#888888', width=2)
d.text((80, 160), 'TITULO ESCRITO PELA PESSOA', font=font(22), fill='#555555')
d.line([(45, 560), (220, 330), (420, 580), (600, 400), (680, 520)], fill='#777777', width=4)
d.ellipse((310, 440, 390, 520), outline='#555555', width=4)
d.polygon([(305, 535), (395, 535), (430, 730), (280, 730)], outline='#555555')
d.text((70, 790), 'Paisagem + personagem + texto', font=font(26), fill='#555555')
sketch.save(ROOT / '01_esboco_simulado.png')

# V1 acrescenta uma figura geométrica. A paisagem permanece byte a byte igual
# nas regiões não cobertas; assim podemos localizar concretamente a intervenção.
v1 = base.copy()
d = ImageDraw.Draw(v1)
d.ellipse((310, 440, 390, 520), fill='#b87650', outline='#303e49', width=3)
d.polygon([(305, 535), (395, 535), (430, 730), (280, 730)], fill='#e6ae36', outline='#303e49')
d.line((315, 730, 310, 830), fill='#303e49', width=14)
d.line((390, 730, 400, 830), fill='#303e49', width=14)
v1.save(ROOT / '03_versao_personagem.png')
final = v1.copy()
d = ImageDraw.Draw(final)
d.rectangle((40, 45, 680, 230), fill='#152e3c')
d.text((65, 65), 'O CAMINHO DE LIA', font=font(49), fill='#fff3d7')
d.text((65, 145), 'Uma carta. Uma volta. Um novo olhar.', font=font(27), fill='#dce7e8')
final.save(ROOT / '04_cartaz_final.png')

# Este arquivo permite inspecionar e editar camadas, em vez de confiar só no relato.
# Fica em uma subpasta: não é enviado ao analisador como se fosse uma imagem raster.
source = ROOT / 'fontes'
source.mkdir(exist_ok=True)
encoded = base64.b64encode((ROOT / '02_base_ia_simulada.png').read_bytes()).decode()
(source / 'cartaz_editavel.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="900" viewBox="0 0 720 900">
<title>Cartaz didático simulado — camadas inspecionáveis</title>
<g id="fundo_simulando_saida_ia"><image width="720" height="900" href="data:image/png;base64,{encoded}"/></g>
<g id="personagem_intervencao_simulada"><circle cx="350" cy="480" r="40" fill="#b87650" stroke="#303e49" stroke-width="3"/>
<path d="M305 535H395L430 730H280Z" fill="#e6ae36" stroke="#303e49"/>
<path d="M315 730L310 830 M390 730L400 830" stroke="#303e49" stroke-width="14"/></g>
<g id="texto_e_composicao_simulados"><rect x="40" y="45" width="640" height="185" fill="#152e3c"/>
<text x="65" y="112" font-family="DejaVu Sans" font-size="49" fill="#fff3d7">O CAMINHO DE LIA</text>
<text x="65" y="178" font-family="DejaVu Sans" font-size="27" fill="#dce7e8">Uma carta. Uma volta. Um novo olhar.</text></g>
</svg>''', encoding='utf-8')

# Substituímos os antigos relatos genéricos por referências a arquivos verificáveis.
records = {
 '01_roteiro.txt': 'Data declarada: 2026-03-01\nSIMULACAO DIDATICA: todos os arquivos foram produzidos por codigo.\nConceito e narrativa atribuídos à pessoa no cenário: Lia retorna ao porto levando uma carta.\nTexto escrito no cenário: O CAMINHO DE LIA / Uma carta. Uma volta. Um novo olhar.\nConferir se as frases aparecem em 04_cartaz_final.png.\n',
 '02_personagem.txt': 'Data declarada: 2026-03-02\nEsboço: 01_esboco_simulado.png. Planeja título no alto e personagem ao centro.\nPersonagem: figura de casaco amarelo acrescentada em 03_versao_personagem.png.\nCompare com 02_base_ia_simulada.png: a paisagem não contém essa figura.\nNo cenário, o desenho é atribuído à pessoa; os arquivos reais foram feitos por código.\n',
 '03_prompt.txt': 'Data declarada: 2026-03-03\nPrompt do cenário: produzir uma paisagem de porto, montanhas, água azul e sol, sem pessoas nem letras.\nArquivo representando a saída: 02_base_ia_simulada.png.\nNão há execução de modelo, histórico de serviço ou resposta original de IA neste pacote.\n',
 '04_edicao.txt': 'Data declarada: 2026-03-05\nEdição no cenário: personagem acrescentada à base em 03_versao_personagem.png.\nComposição e texto acrescentados em 04_cartaz_final.png.\nProjeto editável: fontes/cartaz_editavel.svg, com fundo, personagem e texto em grupos separados.\nConfronte o registro com as versões; mudanças visuais não identificam quem as realizou.\n',
 '05_sem_data.txt': 'Nota sem data: não há histórico autenticado de edição, assinatura, registro do serviço de IA ou arquivo manual original.\nO SVG permite examinar elementos separados, mas não prova quem os criou.\nEste é um processo simulado para aprender a investigar, não uma prova de autoria real.\n',
}
for name, text in records.items():
    (ROOT / name).write_text(text, encoding='utf-8')
print('Cartaz simulado e versões criados em', ROOT)
