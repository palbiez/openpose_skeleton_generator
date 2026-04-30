import json
import numpy as np
from pathlib import Path

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

REFERENCE_DIR = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose_files")

# --------------------------------------------------
# UTILS
# --------------------------------------------------

def reshape(kp):
    return np.array(kp).reshape(-1, 3)


def normalize(kp):

    kp = np.array(kp, dtype=np.float32)

    # FIX: harte Länge erzwingen
    if len(kp) != 51:
        return None

    kp = kp.reshape(17, 3)

    valid = kp[:, 2] > 0
    pts = kp[valid][:, :2]

    if len(pts) < 5:
        return None

    min_xy = pts.min(axis=0)
    max_xy = pts.max(axis=0)

    scale = max(max_xy - min_xy)
    if scale < 1e-5:
        return None

    kp[:, :2] = (kp[:, :2] - min_xy) / scale

    return kp.flatten()

# --------------------------------------------------
# LOAD REFERENCE
# --------------------------------------------------

def load_reference():

    vectors = []
    meta = []

    for file in REFERENCE_DIR.glob("*.json"):

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            norm = normalize(item["keypoints"])
            if norm is None:
                continue

            vectors.append(norm)
            meta.append({
                "pose": item["pose"],
                "variant": item["variant"],
                "subpose": item["subpose"],
                "attributes": item["attributes"],
                "keypoints": item["keypoints"],
                "source_file": file.name
            })

    return np.array(vectors), meta


# --------------------------------------------------
# MATCHER CLASS
# --------------------------------------------------

class PoseMatcher:

    def __init__(self):
        print("Lade Referenzdaten...")
        self.vectors, self.meta = load_reference()
        print(f"{len(self.vectors)} Referenzposen geladen")

    # --------------------------------------------------
    # LOW LEVEL (NUMPY)
    # --------------------------------------------------
    def match_indices(self, keypoints, top_k=3):

        query = normalize(keypoints)
        if query is None:
            return None, None

        dists = np.linalg.norm(self.vectors - query, axis=1)
        idx = np.argsort(dists)[:top_k]

        return idx, dists

    # --------------------------------------------------
    # HIGH LEVEL MATCH
    # --------------------------------------------------
    def match(self, keypoints, top_k=3):

        idx, dists = self.match_indices(keypoints, top_k)

        if idx is None:
            return None

        results = []
        for i in idx:
            results.append({
                "score": float(dists[i]),
                "pose": self.meta[i]["pose"],
                "variant": self.meta[i]["variant"],
                "subpose": self.meta[i]["subpose"],
                "attributes": self.meta[i]["attributes"],
                "keypoints": self.meta[i]["keypoints"],
                "source_file": self.meta[i]["source_file"]
            })

        return results

    # --------------------------------------------------
    # DIRECT SKELETON OUTPUT
    # --------------------------------------------------
    def match_best_keypoints(self, keypoints):

        result = self.match(keypoints, top_k=1)

        if not result:
            return None

        return result[0]["keypoints"]

    # --------------------------------------------------
    # BATCH MATCHER
    # --------------------------------------------------
    def match_batch(self, list_of_keypoints, top_k=1):

        outputs = []

        for kp in list_of_keypoints:
            result = self.match(kp, top_k=top_k)

            if result:
                outputs.append(result[0])  # best match
            else:
                outputs.append(None)

        return outputs

    # --------------------------------------------------
    # BATCH SKELETON ONLY
    # --------------------------------------------------
    def match_batch_keypoints(self, list_of_keypoints):

        outputs = []

        for kp in list_of_keypoints:
            best = self.match_best_keypoints(kp)
            outputs.append(best)

        return outputs


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    matcher = PoseMatcher()

    # Dummy Input (ersetzen!)
    test_kp = [0] * (17 * 3)

    print("\nSingle Match:")
    print(json.dumps(matcher.match(test_kp), indent=2))

    print("\nBest Skeleton:")
    print(matcher.match_best_keypoints(test_kp))

    print("\nBatch Match:")
    batch = [test_kp, test_kp]
    print(json.dumps(matcher.match_batch(batch), indent=2))