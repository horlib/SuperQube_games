# PTM Visualization Dashboard

Streamlit dashboard pro vizualizaci výsledků Pricing Truth Machine analýz.

## Instalace

Nainstalujte závislosti pro vizualizaci:

```bash
pip install -e ".[viz]"
```

Nebo ručně:

```bash
pip install streamlit plotly pandas
```

## Spuštění

Spusťte Streamlit dashboard:

```bash
streamlit run app.py
```

Dashboard se otevře v prohlížeči na `http://localhost:8501`.

## Použití

1. **Nahrajte report.json**: Použijte sidebar k nahrání souboru `report.json` vygenerovaného PTM analýzou
2. **Nebo použijte defaultní report**: Pokud máte `output/report.json`, klikněte na "Load Default Report"
3. **Prohlížejte vizualizace**:
   - **Verdict Panel**: Status a důvěra analýzy
   - **Price Comparison Chart**: Grafické srovnání ceny vašeho produktu vs konkurentů
   - **Evidence Table**: Detailní tabulka s důkazy, zdrojovými URL a verbatim citacemi
   - **Gaps & Limitations**: Seznam datových mezer
   - **Citations**: Seznam všech zdrojů použitých v analýze

## Komponenty

- `app.py` - Hlavní Streamlit aplikace
- `src/ptm_viz/loader.py` - Načítání a validace JSON reportů
- `src/ptm_viz/transforms.py` - Transformace dat pro grafy
- `src/ptm_viz/charts.py` - Generování grafů (Plotly)
- `src/ptm_viz/components.py` - Znovupoužitelné UI komponenty

## Specifikace

Vizualizace je implementována podle `ptm_visualization_spec.md`.
