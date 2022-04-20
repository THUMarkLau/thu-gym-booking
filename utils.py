import json
import requests
from io import BytesIO
from PIL import Image
from ddddocr import DdddOcr
import cv2

_ocr = DdddOcr()


def sorted_by_weights(array, weights):
    def get_id(x):
        return int(x[1:])

    return sorted(array,
                  key=lambda x: weights[get_id(x["field_name"])] if get_id(x["field_name"]) in weights.keys() else 0,
                  reverse=True)


def gen_weight_map(config):
    priority = config["priority"]
    max_weight = len(priority)
    weight_map = {}
    for id in priority:
        weight_map[id] = max_weight
        max_weight -= 1
    for i in range(1, 13):
        if i not in weight_map.keys():
            weight_map[i] = 0
    return weight_map


def get_verification_code(session):
    res = ""
    while len(res) != 4:
        re = session.get("https://50.tsinghua.edu.cn/Kaptcha.jpg")
        img = Image.open(BytesIO(re.content))
        img.save("raw.jpeg")

        img = cv2.imread('raw.jpeg')
        cropped = img[0:50, 50:200]
        cv2.imwrite('done.jpeg', cropped)

        with open("done.jpeg", 'rb') as f:
            image = f.read()
        res = _ocr.classification(image)
    return res
