import os
import random
from pathlib import Path

import pandas as pd
import numpy as np
from PIL import Image
from tqdm.auto import tqdm
import torch
from torch.utils.data import Dataset, DataLoader
from torch.utils.data import DataLoader
from scipy.spatial.distance import cosine
from transformers import ViTFeatureExtractor, ViTModel

extractor = 'google/vit-base-patch16-384'  # фичи экстрактор
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'  # пока пусть так будет, нужно сделать не так явно
torch.manual_seed(0)
random.seed(0)
np.random.seed(0)

THRESHOLD = 0.6


class NN:
    def __init__(self, model_path='model', base_file_path="./full_base_file.csv"):
        module_path = Path(__file__).parent
        self.model = str((module_path / model_path).absolute())  # путь до обученной модели
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(extractor)
        self.model = ViTModel.from_pretrained(self.model)

        self.df = pd.read_csv(
            str((module_path / base_file_path).absolute()))  # считываем csv со средними эмбеддингами для каждого класса
        self.base = self.df.values.T
        self.model.to(device)

    def get_metric_prediction(self, model, device, base, img):
        img.to(device)

        # инференс модели и получение предикта
        model.eval()
        with torch.no_grad():
            prediction = model(**img).pooler_output
            prediction = prediction[0].cpu().detach().numpy()

        dist = []
        for emb in base:
            dist.append(cosine(emb, prediction))  # считаем косинусное расстояние

        class_idx = np.argmin(np.array(dist))  # берем индекс наименьшего расстояния - близжайший класс

        return class_idx, np.array(dist).min()  # correct_class

    def seed_everything(self, seed=1234):
        random.seed(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True

    class TestDataset(Dataset):

        def __init__(self, meta, root_dir, f_extractor):
            self.meta = meta
            self.root_dir = root_dir
            self.feature_extractor = f_extractor

        def __len__(self):
            return len(self.meta)

        def __getitem__(self, idx):
            if torch.is_tensor(idx):
                idx = idx.tolist()

            img_name = os.path.join(
                self.root_dir,
                self.meta['filename'].iloc[idx]
            )
            # print(img_name)
            image = self.get_masked_image(img_name)
            image = self.feature_extractor(images=image, return_tensors="pt")
            return image

        def get_masked_image(self, path):
            mask = (np.array(Image.open(path[:-3] + "png").convert('RGB')) / 255).astype(np.uint8)
            img = np.array(Image.open(path[:-3] + "jpg"))
            return Image.fromarray(np.multiply(mask, img))

    def folder_with_images(self, path_to_folder_with_images):
        filename = []
        whale_folders = []
        for i in os.listdir(path_to_folder_with_images):
            if i.endswith('.jpg'):
                path_to_image = os.path.join(path_to_folder_with_images, i)
                filename.append(path_to_image)
                whale_folders.append(i)
        data = pd.DataFrame({"filename": filename, "whale_folder": whale_folders})
        dataset = NN.TestDataset(meta=data, root_dir="", f_extractor=self.feature_extractor)
        infer_dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=4)
        with torch.no_grad():
            for idx, batch in enumerate(tqdm(infer_dataloader)):
                for i in batch:
                    batch[i] = batch[i][:, 0].to(device)
                prediction = self.model(**batch).pooler_output
                prediction = prediction[0].cpu().detach().numpy()

                dist = []
                for emb in self.base:
                    dist.append(cosine(emb, prediction))
                class_idx = np.argmin(np.array(dist))
                # print(int(class_idx), dist[class_idx])
                if dist[class_idx] < THRESHOLD:
                    data.loc[idx, 'class'] = class_idx + 1
                else:
                    data.loc[idx, 'class'] = int(0)
        data = data.iloc[:, 1:]
        data['class'] = data["class"].astype("int64")
        return data

    def folderinfolder(self, path_to_folder_with_folders):
        foldernames = []
        r1 = []
        r2 = []
        r3 = []
        r4 = []
        r5 = []
        for i in os.listdir(path_to_folder_with_folders):
            rez = self.for_one_folder(os.path.join(path_to_folder_with_folders, i))
            r1.append(rez[0])
            r2.append(rez[1])
            r3.append(rez[2])
            r4.append(rez[3])
            r5.append(rez[4])
            foldernames.append(i)
        return pd.DataFrame({'folder': foldernames, 'r1': r1, 'r2': r2, "r3": r3, 'r4': r4, "r5": r5})

    def for_one_folder(self, folder_path):
        filename = []
        whale_folders = []

        for i in os.listdir(folder_path):
            if i.endswith('.jpg'):
                path_to_image = os.path.join(folder_path, i)
                filename.append(path_to_image)
                whale_folders.append(i)
        data = pd.DataFrame({"filename": filename, "whale_folder": whale_folders})
        total = 0
        predictions = np.array([0 for i in range(768)]).astype('float64')
        dataset = NN.TestDataset(meta=data, root_dir="", f_extractor=self.feature_extractor)
        infer_dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=4)
        with torch.no_grad():
            for idx, batch in enumerate(tqdm(infer_dataloader)):
                for i in batch:
                    batch[i] = batch[i][:, 0].to(device)
                prediction = self.model(**batch).pooler_output
                prediction = prediction[0].cpu().detach().numpy()
                predictions += prediction
                total += 1
            prediction = predictions / total
            dist = []
            for emb in self.base:
                dist.append(cosine(emb, prediction))
            # class_idx = np.argmin(np.array(dist))
            dist = sorted([(dist[i], i) for i in range(len(dist))])[:5]

            # print(dist)
            ans = []
            for distancia, class_idx in dist:
                if distancia < THRESHOLD:
                    ans.append(int(class_idx) + 1)
                else:
                    ans.append(int(0))
            return ans

    def get_result_of_image_by_path(self, path):
        dataset = NN.TestDataset(pd.DataFrame({"filename": [path], "whale_folder": ['no']}), '', self.feature_extractor)
        class_idx, distance_of_im = self.get_metric_prediction(self.model, device, self.base, dataset[0])
        if distance_of_im < THRESHOLD:
            class_idx = class_idx + 1
        else:
            class_idx = int(0)
        return class_idx


if __name__ == '__main__':
    # folder_with_images("Whale ReId 2_mm/3/crop1_DJI_02227").to_csv("1.csv", index=False)
    # folderinfolder("test").to_csv("2.csv", index=False)
    n = NN()
    print(n.get_result_of_image_by_path(
        "D:\\Users\\Sergey\\Downloads\\TEMP\\digital-breakthrough\\tests\\A\\1\\crop1_DJI_0002\\crop1_DJI_0002_1.jpg"))
