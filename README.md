# DryOut Shield – Forecast-driven replenishment for fuel retail outlets

SCA group project · GIM PGDM-BDA 2026-27, Term 5 · Sector: **Fuel**

Team: Sakshi Malwanker (B2025159), Harisankar M (B2025139), George K Manuel (B2025138), Aswin R Nair (B2025129)

**Live app:** https://harisankar2112m-sca-appstreamlit-app-zk5y0h.streamlit.app/  
**Source code:** https://github.com/harisankar2112m/sca

**DryOut Shield** is a decision-support web app for an oil-company depot manager. It:
- forecasts each outlet's daily petrol and diesel demand using a model built and validated in **JMP**;
- converts the forecast, its uncertainty and current stock into days of cover, dry-out risk, reorder points and order quantities in 4 kL compartments;
- allocates the depot's limited tank trucks to the most urgent outlets.

## Repository layout
| Folder | Contents |
|---|---|
| `app/` | **Streamlit app**. Entry point: `app/streamlit_app.py`. Bundled data is in `app/data/` |
| `data/` | Real PPAC data, synthetic outlet data, data dictionary, upload templates |
| `jmp/` | JMP model script (`DryOut_Forecast_Model.jsl`), JMP data table, and JMP outputs in `out/` |
| `model/` | Validation results and the production forecast exported from JMP |
| `src/` | Python scripts: PPAC download, synthetic data generator, JMP input preparation, holdout scoring |
| `MODEL_README.md` | Model method and results |

## Run locally
```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

## Deploy (Streamlit Community Cloud, free public URL)
1. Push this folder to a **public GitHub repository**.
2. Go to **share.streamlit.io** and sign in with GitHub. Click **Create app** → **Deploy a public app from GitHub**.
3. Choose the repository and branch, and set **Main file path** to `app/streamlit_app.py`.
4. Under **Advanced settings**, choose Python **3.13**, then click **Deploy**. The first build takes 2–4 minutes.
5. Share the URL, e.g. `https://dryout-shield.streamlit.app`.

Keep the app online until results are declared. Free apps sleep after several days without visits; opening the URL wakes them.

## Rebuild data and model
```bash
python src/fetch_ppac.py              # real PPAC monthly MS/HSD consumption
python src/generate_outlet_data.py    # synthetic outlets (seed 2026)
python src/prepare_jmp_input.py       # modelling table for JMP
```

Then run `jmp/DryOut_Forecast_Model.jsl` in JMP, and score the forecasts:
```bash
python src/evaluate_jmp_model.py      # holdout scoring -> model/
```

Finally, copy the files from `model/` and `jmp/out/` into `app/data/` and `app/assets/`.

## Disclosure
- Outlet-level data is synthetic and calibrated to real PPAC consumption. See `data/DATA_DICTIONARY.md`.
- AI assistance (Claude) was used for coding and drafting. It is disclosed in the report appendix.
