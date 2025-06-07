- [ ] Update the application so it first uploads the file to the Mistral API server, requests OCR processing, and then downloads the result. Follow these steps:

    1.  Upload the file to Mistral server:
    ```
    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    uploaded_file = client.files.upload(
        file={
            "file_name": "FILENAME.EXT",
            "content": open("FILENAME.EXT", "rb"),
        },
        purpose="ocr"
    ) 
    ```

    2. Get the `signed URL` of the uploaded file:

    ```
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
    ```

    3. Perform the OCR using the signed URL:

    ```
    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)
    
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )
    ```

    The `ocr_response` variable will include the signed URLs of the extracted document elements (text, tables, images, etc) to download.


