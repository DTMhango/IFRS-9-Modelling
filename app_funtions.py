import numpy as np
import pandas as pd
import re
import io
import base64


def parse_content(contents, filename):
    print("Received contents:", contents)
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if '.csv' in filename:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return df.to_dict('records')
    elif '.xls' in filename:
        df = pd.read_excel(io.BytesIO(decoded))
        return df.to_dict('records')


def decode_image(image_file):
    encoded = base64.b64encode(open(image_file, 'rb').read())
    return f"data:image/png;base64,{encoded.decode()}"
