# Moldura v7 — 16/10/2026

O problema era o armazenamento simultâneo de todos os originais decodificados. Cada exemplo enviado tem 30.105.600 pixels; seis fotografias RGB já ultrapassavam a contagem anterior de 512 MiB. O tamanho comprimido do JPG não representa seu consumo após a abertura.

## Implementação

- Arquivos originais conservados byte a byte em pastas temporárias locais, sem alterar os arquivos do usuário.
- Fontes interativas de até 1800 px e miniaturas de 128 px. Navegador conserva até três fontes de edição decodificadas.
- Cache do servidor de 160 MiB, separado em cotas para originais e versões leves. Remoção das referências ao original anterior antes de decodificar o seguinte; processamento pesado serializado.
- Prévia definitiva do editor e JPG final calculados a partir do original completo. Prévias das folhas usam versões leves.
- ZIP enviado em blocos, com armazenamento temporário para arquivos maiores que 8 MiB.
- Referências aos arquivos mantidas durante exportações já iniciadas, mesmo se uma foto for removida. Limpeza automática quando a última operação libera a foto e no encerramento normal.
- Removido o bloqueio por soma de pixels do lote. Limites: 100 fotos, 50 MiB/60 MP por foto e 4 GiB de arquivos originais temporários, com verificação de espaço livre.

## Evidências

24 testes automatizados aprovados: API, exportação concorrente com remoção, dimensões, reflexos, cor, EXIF/transparência, quatro gabaritos, cache limitado, liberação antes da próxima decodificação e limpeza dos temporários.

Quatro roteiros de navegador aprovados no executável: edição/recuperação, modelos/ZIP, refinamentos/abas/responsividade e download individual/setas. O refinamento final da liberação de memória foi validado pelos 24 testes e pelo teste de carga direcionado no executável recompilado.

Teste de carga final com as três fotos fornecidas, repetidas quatro vezes, no Microsoft Edge:

| Medida | Resultado nesta máquina |
|---|---:|
| Fotos importadas | 12 de aproximadamente 30 MP |
| Tempo de importação | 21,34 s |
| Amostras de RAM entre blocos de importação | 62,8 / 59,5 / 61,3 / 62,0 MiB |
| Pico de RAM do processo durante todo o teste | 324,1 MiB |
| Intervalo mediano entre quadros durante arraste | 16,7 ms |
| Percentil 95 entre quadros durante arraste | 16,8 ms |
| Desenhos no canvas durante arraste | 155 |
| Pedidos de prévia ao servidor durante arraste | 0 |
| Folhas exportadas | 6, todas 1795 × 1205 px a 300 DPI |
| Exportação com zoom 4,25× | Pixels idênticos ao JPG calculado diretamente do original |
| Erros JavaScript do aplicativo | 0 |

As amostras entre blocos não representam toda a memória de edição; o pico inclui decodificação, prévia definitiva e exportação. Desempenho depende do computador, disco, formato e tamanho das imagens. O orçamento do cache não é um limite absoluto para a RAM do processo.

Bandeja nativa, segunda abertura reutilizando a instância e encerramento com remoção dos metadados também aprovados. Nenhuma fotografia pessoal ou exportação foi gravada na pasta de artefatos dos testes; downloads de teste ficaram no contexto temporário do navegador. Versões anteriores preservadas.

Visual, medidas da v6, áreas visíveis/seguras, capacidades por folha, JPG qualidade 100, cor 4:4:4 e perfil sRGB preservados. Distribuição em `dist/Moldura-v7.exe`.
