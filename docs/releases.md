# Publicar uma versão

O Git começa com o snapshot da v7, registrado em `v0.7.0`. Os relatórios anteriores foram preservados como documentação; não representam commits retroativos. A primeira versão com instalador e atualizador é `v1.0.0`. Veja o [histórico de alterações](../CHANGELOG.md).

O GitHub Actions testa e compila alterações em `main` e pull requests. Para publicar uma atualização, atualize `version.py`, `CHANGELOG.md` e `RELEASE_NOTES.md`, registre o commit e envie uma tag correspondente, por exemplo `v1.0.1`. O workflow testa o EXE e a instalação no Windows, gera os arquivos, cria um rascunho de release, envia todos os assets e só então publica. Commits em desenvolvimento não são distribuídos automaticamente aos usuários.

O instalador usa um AppId e um caminho estáveis, de forma que novas versões substituem a instalação existente. Não é necessário desinstalar. A verificação ocorre 15 segundos após abrir e depois a cada seis horas; a conexão e o tempo de execução determinam quando uma versão chega a cada computador. Uma atualização já verificada pode ser aplicada ao encerrar mesmo se a internet cair.

SHA-256 verifica integridade, não substitui assinatura de código. O instalador ainda não possui certificado comercial de assinatura do Windows; baixe somente das releases deste repositório. O log de instalação das atualizações fica em `%LOCALAPPDATA%/Moldura/updates/install.log`. Arquivos de fotos e ajustes da sessão continuam temporários; exporte antes de encerrar.

## Sequência de publicação

1. Atualize `VERSION` em `version.py`, `CHANGELOG.md` e `RELEASE_NOTES.md`.
2. Atualize o endereço do botão de download no README para o novo instalador.
3. Execute os testes e registre as alterações em um commit.
4. Crie e envie a tag que corresponde exatamente à versão, como `v1.0.1`.
5. Confira o resultado do workflow e os arquivos publicados na release.

A publicação só acontece para tags. Alterações no README e na documentação não precisam de uma nova versão do aplicativo.

[Workflow de Windows](../.github/workflows/windows.yml) · [Versões publicadas](https://github.com/redlab-coder/moldura/releases)


[← Documentação](README.md) · [Moldura](../README.md)
