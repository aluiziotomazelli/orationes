# Orationes & Officium Divinum

Compêndio de orações católicas tradicionais e horas do Ofício Divino em edição bilíngue (Latim e vernáculo).

Acesso online:
* Página principal: https://aluiziotomazelli.github.io/orationes/
* Angelus Dómini: https://aluiziotomazelli.github.io/orationes/#angelus
* Ad Completorium: https://aluiziotomazelli.github.io/orationes/#completorium

---

## Proposta

1. Textos alinhados verso a verso para facilitar o acompanhamento da oração em latim.
2. Aplicação web com suporte a múltiplos idiomas, modo escuro automático e ajuste de fonte.
3. Arquivos PDF diagramados para impressão em papel A4 e leitura em dispositivos móveis.

---

## Estrutura do repositório

```text
orationes/
├── index.html                  (Portal e aplicação web)
├── app.js                      (Motor de renderização e controle de idioma)
├── style.css                   (Folha de estilos)
│
├── data/
│   ├── latin/                  (Textos originais em latim em formato Markdown)
│   │   ├── angelus.md
│   │   └── completorium.md
│   │
│   ├── prayers/                (Dados estruturados em JS e JSON)
│   │   ├── angelus.js / angelus.json
│   │   └── completorium.js / completorium.json
│   │
│   └── bilingual/              (Textos de referência bilíngue em Markdown)
│       └── completorium.md
│
└── print/                      (Documentos PDF)
    ├── completorium_livreto_A4.pdf   (Livreto de 8 páginas A5 em 2 folhas A4 para dobra)
    ├── completorium_A5.pdf           (Páginas sequenciais em formato A5)
    └── completorium_celular.pdf      (Formato vertical para tela de celular)
```

---

## Impressão do livreto A4

O arquivo `print/completorium_livreto_A4.pdf` está configurado para gerar um livreto de 8 páginas A5 usando duas folhas de papel A4:

1. Abra o arquivo `print/completorium_livreto_A4.pdf` em um leitor de PDF.
2. Na caixa de diálogo de impressão:
   * Tamanho do papel: A4 (paisagem).
   * Escala: 100% (tamanho real).
   * Impressão: frente e verso (duplex).
   * Orientação de virada: inverter pela borda menor (borda curta).
3. Após a impressão, junte as folhas e dobre-as ao meio pela linha guia central.

---

## Fontes

* Texto em latim e rubricas: [Divinum Officium](https://www.divinumofficium.com/) (Rubricæ 1960).
