from spot import (
    Spot,
    SpotCamIds,
    image_response_to_cv2,
    scale_depth_img,
    draw_crosshair,
)
from utils import color_bbox
import cv2
import numpy as np
from collections import deque
import time

MAX_HAND_DEPTH = 3.0
MAX_HEAD_DEPTH = 10.0
DETECT_LARGEST_WHITE_OBJECT = True

from bosdyn.client.frame_helpers import BODY_FRAME_NAME, get_vision_tform_body, get_a_tform_b

def main(spot: Spot):
    window_name = "spot camera viewer"
    time_buffer = deque(maxlen=30)
    # sources = [SpotCamIds.HAND_COLOR, SpotCamIds.HAND_DEPTH_IN_HAND_COLOR_FRAME]
    # sources = [SpotCamIds.HAND_COLOR, SpotCamIds.HAND_DEPTH]
    # sources = [
    #     SpotCamIds.HAND_COLOR,
    #     SpotCamIds.HAND_DEPTH,
    #     # SpotCamIds.HAND_DEPTH_IN_HAND_COLOR_FRAME,
    # ]
    sources = [
        SpotCamIds.FRONTRIGHT_DEPTH,
        SpotCamIds.FRONTLEFT_DEPTH,
    ]
    # sources = [SpotCamIds.HAND_COLOR]
    # sources = [SpotCamIds.FRONTLEFT_DEPTH_IN_VISUAL_FRAME, SpotCamIds.HAND_COLOR]
    # sources = [SpotCamIds.FRONTRIGHT_FISHEYE, SpotCamIds.FRONTLEFT_FISHEYE]
    # sources = [SpotCamIds.HAND_DEPTH]
    try:
        while True:
            start_time = time.time()

            # Get Spot camera image
            image_responses = spot.get_image_responses(sources)
            imgs = []
            for image_response, source in zip(image_responses, sources):
                # print(source, image_response.body_T_image_sensor, image_response.body_T_image_sensor.position, image_response.body_T_image_sensor.rotation)
                body_T_image_sensor = get_a_tform_b(
                    image_response.shot.transforms_snapshot,
                    BODY_FRAME_NAME, image_response.shot.frame_name_image_sensor
                )
                print(source, body_T_image_sensor.position, body_T_image_sensor.rotation)
                img = image_response_to_cv2(image_response)
                if "depth" in source.value:
                    if "frame" not in source.value:
                        img = np.rot90(img, k=3)
                    max_depth = (
                        MAX_HAND_DEPTH if "hand" in source.value else MAX_HEAD_DEPTH
                    )
                    img = scale_depth_img(img, max_depth=max_depth, as_img=True)
                    if source is SpotCamIds.HAND_DEPTH:
                        img = np.rot90(img, k=3)
                        img = cv2.resize(img, (480, 480))
                elif source is SpotCamIds.HAND_COLOR:
                    img = draw_crosshair(img)
                    if DETECT_LARGEST_WHITE_OBJECT:
                        x, y, w, h = color_bbox(img, just_get_bbox=True)
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                imgs.append(img)

            img = np.hstack(imgs)

            cv2.imshow(window_name, img)
            cv2.waitKey(1)
            time_buffer.append(time.time() - start_time)
            print("Avg FPS:", 1 / np.mean(time_buffer))
    finally:
        cv2.destroyWindow(window_name)


if __name__ == "__main__":
    spot = Spot("ViewCamera")
    # We don't need a lease because we're passively observing images (no motor ctrl)
    main(spot)
