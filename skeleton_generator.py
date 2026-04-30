import json
import numpy as np
import cv2
import random
import torch

class SkeletonFromJSON:
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "width": ("INT", {"default": 768}),
                "height": ("INT", {"default": 768}),
                "num_people": ("INT", {"default": 2, "min": 1, "max": 10}),
            },
            "optional": {},
            "hidden": {
                "update": ("UPDATE", {}),
            }
        }
        
        # Add fixed number of pose inputs (max 10)
        for i in range(1, 11):  # 1 to 10
            inputs["optional"][f"pose_{i}"] = ("STRING", {"default": "[]", "multiline": False})
        
        return inputs

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


    def place_person_at(self, keypoints, center_x, center_y, width, height):
        # Referenz: Hüfte
        hip_x = (keypoints[11*3] + keypoints[12*3]) / 2
        hip_y = (keypoints[11*3+1] + keypoints[12*3+1]) / 2

        dx = center_x - hip_x
        dy = center_y - hip_y

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


    def generate(self, width, height, num_people, update=None, **kwargs):
        print(f"[Skeleton] Generating with {num_people} people")
        
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        persons = []
        
        # Collect pose inputs up to num_people
        for i in range(1, num_people + 1):
            pose_key = f"pose_{i}"
            if pose_key in kwargs:
                pose_json = kwargs[pose_key]
                if pose_json and pose_json != "[]":
                    try:
                        person = json.loads(pose_json)
                        if isinstance(person, dict):
                            persons.append(person)
                        elif isinstance(person, list):
                            persons.extend(person)
                    except json.JSONDecodeError:
                        print(f"[Skeleton] Invalid JSON for {pose_key}: {pose_json}")

        if len(persons) == 0:
            print("[Skeleton] WARNING: No valid persons found")
            image = torch.from_numpy(canvas).float() / 255.0
            image = image.unsqueeze(0)
            return (image,)

        print(f"[Skeleton] Drawing {len(persons)} persons")
        
        # Place persons from left to right
        spacing = width / (len(persons) + 1)
        
        for i, person in enumerate(persons):
            keypoints = person["keypoints"]
            # Center each person horizontally
            center_x = spacing * (i + 1)
            center_y = height * 0.5
            
            keypoints = self.place_person_at(keypoints, center_x, center_y, width, height)
            self.draw_person(canvas, keypoints)
        
        image = torch.from_numpy(canvas).float() / 255.0
        image = image.unsqueeze(0)

        return (image,)