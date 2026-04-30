import json
import numpy as np
import cv2
import random
import torch

class SkeletonFromJSON:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_text": ("STRING", {}),
                "width": ("INT", {"default": 768}),
                "height": ("INT", {"default": 768}),
                "num_people": ("INT", {"default": 2}),
                "random_seed": ("INT", {"default": -1})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "pose"

    # COCO Skeleton Definition
    SKELETON = [
        (5, 7), (7, 9),     # left arm
        (6, 8), (8, 10),    # right arm
        (5, 6),             # shoulders
        (5, 11), (6, 12),   # torso
        (11, 12),
        (11, 13), (13, 15), # left leg
        (12, 14), (14, 16)  # right leg
    ]

    def draw_person(self, canvas, keypoints):
        valid_points = sum(1 for i in range(0, len(keypoints), 3) if keypoints[i+2] > 0)
        print(f"[Skeleton] Valid keypoints: {valid_points}/17")
        # Punkte
        for i in range(0, len(keypoints), 3):
            x, y, v = keypoints[i], keypoints[i+1], keypoints[i+2]
            if v > 0:
                cv2.circle(canvas, (int(x), int(y)), 4, (255,255,255), -1)

        # Knochen
        for a, b in self.SKELETON:
            xa, ya, va = keypoints[a*3], keypoints[a*3+1], keypoints[a*3+2]
            xb, yb, vb = keypoints[b*3], keypoints[b*3+1], keypoints[b*3+2]

            if va > 0 and vb > 0:
                cv2.line(canvas, (int(xa), int(ya)), (int(xb), int(yb)), (255,255,255), 2)


    def place_person(self, keypoints, width, height, slot):
        # feste Layout-Slots (keine Überlappung)
        slots = [
            (width * 0.3, height * 0.5),
            (width * 0.7, height * 0.5),
            (width * 0.5, height * 0.7),
            (width * 0.5, height * 0.3),
            (width * 0.2, height * 0.3),
            (width * 0.8, height * 0.3),
        ]

        cx, cy = slots[slot % len(slots)]

        # Referenz: Hüfte
        hip_x = (keypoints[11*3] + keypoints[12*3]) / 2
        hip_y = (keypoints[11*3+1] + keypoints[12*3+1]) / 2

        dx = cx - hip_x
        dy = cy - hip_y

        new_kp = keypoints.copy()

        for i in range(0, len(new_kp), 3):
            x = new_kp[i]
            y = new_kp[i+1]
            v = new_kp[i+2]

            if v > 0:
                x += dx
                y += dy

                # clamp
                x = max(0, min(width-1, x))
                y = max(0, min(height-1, y))

                new_kp[i] = x
                new_kp[i+1] = y

        return new_kp


    def extract_person_list(self, data):
        # unterstützt verschiedene JSON-Formate
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            # grouped format: { "standing": [...] }
            persons = []
            for key in data:
                if isinstance(data[key], list):
                    persons.extend(data[key])
            return persons

        return []


    def generate(self, json_text, width, height, num_people, random_seed):
        print(f"[Skeleton] Input JSON length: {len(json_text)}")
        if random_seed >= 0:
            random.seed(random_seed)

        data = json.loads(json_text)

        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        persons = self.extract_person_list(data)

        if len(persons) == 0:
            print("[Skeleton] WARNING: No persons found in JSON")
            image = torch.from_numpy(canvas).float() / 255.0
            image = image.unsqueeze(0)

            return (image,)

        num_people = min(num_people, len(persons))
        print(f"[Skeleton] Parsed persons: {len(persons)}")
        selected = random.sample(persons, num_people)

        for i, person in enumerate(selected):
            keypoints = person["keypoints"]
            keypoints = self.place_person(keypoints, width, height, i)
            print(f"[Skeleton] Drawing {num_people} persons")
            self.draw_person(canvas, keypoints)
        image = torch.from_numpy(canvas).float() / 255.0

        # WICHTIG: Format für ComfyUI
        image = image.unsqueeze(0)  # (1, H, W, C)

        return (image,)