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

    data = pd.read_csv("data/1 interim/ministop_stores_information_geocoded_fix_url.csv", index_col=False).drop(columns=['Unnamed: 0'])
    data
    return (data,)


@app.cell
def _(data, model):
    address_embeddings = model.encode(data['address'].tolist(), batch_size=16, show_progress_bar=True)
    extracted_address_embeddings = model.encode(data['extracted_address'].tolist(), batch_size=16, show_progress_bar=True)
    return address_embeddings, extracted_address_embeddings


@app.cell
def _(address_embeddings, data, extracted_address_embeddings, util):
    print(address_embeddings.shape, extracted_address_embeddings.shape)
    print(util.cos_sim(address_embeddings, extracted_address_embeddings).diag())
    data['addr_cos_sim'] = util.cos_sim(address_embeddings, extracted_address_embeddings).diag()
    data[data['addr_cos_sim'] < 0.85].to_csv("data/1 interim/04_ministop_stores_review.csv", index=False)
    data[data['addr_cos_sim'] >= 0.85].to_csv("data/1 interim/04_ministop_stores_clean.csv", index=False)
    return


if __name__ == "__main__":
    app.run()
