"""Cria um pequeno livro SIMULADO com versões que podem ser confrontadas.
Nenhum arquivo é uma resposta real de IA ou prova de escrita por uma pessoa.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent / 'recursos_exemplo/livro'
ROOT.mkdir(parents=True, exist_ok=True)
old = 'Lia chegou ao porto ao amanhecer.\nEla encontrou uma carta e decidiu voltar para casa.\n'
new = 'Lia chegou ao porto ao amanhecer.\n— Não vim buscar a carta, disse Lia. Vim devolver a resposta.\nO vento apagou as pegadas na areia.\n'
final = 'Lia chegou ao porto ao amanhecer.\n— Não vim buscar a carta, disse Lia. Vim devolver a resposta.\n'
records = {
 '01_planejamento.txt': 'Data declarada: 2026-03-01\nSIMULAÇÃO DIDÁTICA: todos os materiais foram escritos para o exercício.\nConceito narrativo atribuído à pessoa: Lia volta ao porto para encerrar uma despedida.\nA intenção criativa precisa ser confrontada com sua expressão no livro final.\n',
 '02_prompt.txt': 'Data declarada: 2026-03-02\nPrompt fictício: escreva uma cena breve com Lia no porto, uma carta e um retorno para casa.\nA saída é representada em 03_saida_ia_simulada.txt; não houve execução real de IA.\n',
 '03_saida_ia_simulada.txt': old,
 '04_versao_revisada.txt': new,
 '05_manuscrito_final.txt': final,
 '06_registro_revisao.txt': 'Data declarada: 2026-03-03\nSIMULAÇÃO: registro atribuído à personagem fictícia Ana.\nEu reescrevi o desfecho e escrevi o diálogo: Não vim buscar a carta / Vim devolver a resposta.\nNa revisão, acrescentei a frase sobre o vento.\nNa edição final, retirei a frase sobre o vento e mantive o diálogo.\nNão há histórico autenticado que comprove quem efetuou as alterações.\n',
}
for name, text in records.items():
    (ROOT / name).write_text(text, encoding='utf-8')
print('Livro simulado criado em', ROOT)
