import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    from sentence_transformers import SentenceTransformer, util

    model = SentenceTransformer("multi-qa-distilbert-cos-v1", device='cpu')
    return model, util


@app.cell
def _():
    import pandas as pd 

    NEW_DATA_PATH = "data/1.5 interim/02.5_ministop_stores_geocoded_with_extra_addr.csv"
    OUTPUT_CLEANED_PATH = "data/1.5 interim/03.5_ministop_stores_geocoded_clearned.csv"
    OUTPUT_REVIEWED_PATH = "data/1.5 interim/03.5_ministop_stores_geocoded_reviewed.csv"

    data = pd.read_csv(NEW_DATA_PATH, index_col=False).drop(columns=['Unnamed: 0'])
    data
    return OUTPUT_CLEANED_PATH, OUTPUT_REVIEWED_PATH, data


@app.cell
def _(data, model):
    address_embeddings = model.encode(data['address'].tolist(), batch_size=16, show_progress_bar=True)
    extracted_address_embeddings = model.encode(data['extracted_address'].tolist(), batch_size=16, show_progress_bar=True)
    return address_embeddings, extracted_address_embeddings


@app.cell
def _(
    OUTPUT_CLEANED_PATH,
    OUTPUT_REVIEWED_PATH,
    address_embeddings,
    data,
    extracted_address_embeddings,
    util,
):
    print(address_embeddings.shape, extracted_address_embeddings.shape)
    print(util.cos_sim(address_embeddings, extracted_address_embeddings).diag())
    data['addr_cos_sim'] = util.cos_sim(address_embeddings, extracted_address_embeddings).diag()
    data[data['addr_cos_sim'] < 0.85].to_csv(OUTPUT_REVIEWED_PATH, index=False)
    data[data['addr_cos_sim'] >= 0.85].to_csv(OUTPUT_CLEANED_PATH, index=False)
    return


if __name__ == "__main__":
    app.run()
