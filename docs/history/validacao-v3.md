# Moldura v3 — novos gabaritos

Data: 15/10/2026.

## Escopo

Seletor de modelo para o lote inteiro; Button Quadrado, Redondo G, M e P; guias de enquadramento visível e seguro no editor; corte circular; continuação natural da imagem na sangria, com reflexão somente fora dos limites da foto; montagem de até duas composições G/M ou seis P por folha horizontal de 15,2 × 10,2 cm.

O zoom define o diâmetro visível da foto. A sangria expande o recorte até o diâmetro de corte, aproveitando os pixels originais. A área segura é um guia visual, sem alteração automática de rostos ou textos. É utilizado o menor diâmetro das faixas indicadas: 4,8 / 3,6 / 2,6 cm.

| Modelo | Visível | Corte | Capacidade |
|---|---|---|---:|
| Quadrado | 5 × 5 cm / 591 × 591 px | 7 × 7 cm / 827 × 827 px | 2 |
| Redondo G | Ø 5,8 cm / 685 px | Ø 7 cm / 827 px | 2 |
| Redondo M | Ø 4,4 cm / 520 px | Ø 5,6 cm / 661 px | 2 |
| Redondo P | Ø 3,2 cm / 378 px | Ø 4,4 cm / 520 px | 6 |

Todos os tamanhos são calculados a 300 DPI, com arredondamento ao pixel inteiro mais próximo. Folhas de 1795 × 1205 px; JPG qualidade 100, 4:4:4 e perfil sRGB. Guias não são gravados nas folhas.

## Validação

- 20 testes automatizados de processamento, API e integração Windows passaram.
- Regressão do gabarito quadrado: reflexos, dimensões, margens e metadados continuam cobertos pelos testes anteriores.
- Continuação natural: teste com gradiente confirmou que a sangria usa pixels de fora da área visível quando disponíveis, em vez de refletir o recorte central.
- Reflexão de fallback: teste com pixels identificáveis confirmou a posição correta dos reflexos nas quatro laterais e nos cantos, preservando a área existente.
- Máscara circular: cantos brancos, borda suavizada, cores e rotação verificadas.
- Layouts: todas as quantidades de 1 a 6 para P e de 1 a 2 para G/M foram verificadas quanto a limites, ausência de sobreposição e centralização por linha.
- Exportação resiliente: os originais são capturados por referência no início; remover uma foto de outra aba durante o processamento não invalida o lote em andamento. Um teste cobre essa concorrência.
- Navegador: quatro modelos, arraste, campos precisos, mudança e recuperação do modelo, igualdade dos pixels da prévia estabilizada com o processamento de Pillow e layout móvel sem transbordamento foram testados.
- 6 fotos P: um JPG. 7 fotos P: dois JPGs em ZIP. As duas saídas foram verificadas em 1795 × 1205 px e 300 DPI.

O executável v3 passa pelos mesmos testes no navegador e pela checagem de segunda abertura e encerramento. A v3 tem identidade de execução separada das versões anteriores para que iniciar a nova versão não redirecione para uma versão antiga ainda aberta.

## Uso e limites

Escolha um modelo por lote. Os ajustes de enquadramento existentes são reaproveitados ao trocar o modelo. A recuperação da aba inclui a seleção do gabarito, mas exige o mesmo navegador/perfil e o processo ainda ativo. Não substitui salvar um projeto em disco.

Os testes usam imagens sintéticas. A dimensão física no papel ainda exige impressão em tamanho real / 100%; não foi realizada impressão física nem validação em máquina de bottons. As medidas foram implementadas conforme as referências aprovadas e podem ser ajustadas após seu teste de produção.
