import json


def run_etl(api_key, minio_client, etl_log, tmp_path):
    import keepa

    k = keepa.Keepa(api_key)
    data = k.product_finder({"domainId": 1})
    file_path = tmp_path / "data.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    minio_client.fput_object("bucket", "data.json", str(file_path))
    etl_log.insert({"file": str(file_path)})
    return file_path
