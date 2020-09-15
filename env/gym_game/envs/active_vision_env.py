
from gym import spaces
import numpy as np
import logging
from .pygame_env import PyGameEnv


class ActiveVisionEnv(PyGameEnv):

  metadata = {'render.modes': ['human', 'rgb_array']}

  HUMAN = 'human'
  ARRAY = 'rgb_array'

  def __init__(self, num_actions, screen_width, screen_height, frame_rate=30):
    self.fov_fraction = 0.1  # fraction of diameter, at centre of image
    self.gaze = np.array([0, 0])       # gaze position - (y, x) tuple
    self.actions_start = num_actions
    self.actions_end = num_actions + 4
    self.action_2_xy = {     # map actions (integers) to x,y gaze delta
      num_actions:   np.array([-1, 0]),
      num_actions+1: np.array([1, 0]),
      num_actions+2: np.array([0, -1]),
      num_actions+3: np.array([0, 1])
    }

    super().__init__(num_actions, screen_width, screen_height, frame_rate)

  def reset(self):
    """Reset gaze coordinates"""
    super().reset()

  def _do_step(self, action, time):
    # update the position of the fovea (fov_pos), given the action taken
    logging.debug("Received action: ", action)
    # if within action scope, modify gaze
    if self.actions_start <= action < self.actions_end:
      self.gaze = self.gaze + self.action_2_xy[action]
      logging.debug("New gaze: ", self.gaze)

  def _create_action_space(self, num_actions):
    total_actions = num_actions + self.actions_end  # Gaze control
    self.action_space = spaces.Discrete(total_actions)

  def _create_observation_space(self, screen_width, screen_height, channels=3, dtype=np.uint8):    
    full = spaces.Box(low=0, high=255, shape=(screen_height, screen_width, channels), dtype=dtype)
    fovea = spaces.Box(low=0, high=255, shape=(screen_height, screen_width, channels), dtype=dtype)
    peripheral = spaces.Box(low=0, high=255, shape=(screen_height, screen_width, channels), dtype=dtype)
    self.observation_space = spaces.Dict({
      'full': full,
      'fovea': fovea,
      'peripheral': peripheral})

  def get_observation(self):
    img = self.render(mode='rgb_array')

    # crop to fovea (centre region)
    h, w, ch = img.shape[0], img.shape[1], img.shape[2]

    pixels_h = int(h * self.fov_fraction)
    pixels_w = int(w * self.fov_fraction)

    img_fov = img[self.gaze[0]:self.gaze[0]+pixels_h,
                  self.gaze[1]:self.gaze[1]+pixels_w]

    # zero foveal region, and return as peripheral (other options are to blur or cut it up differently)
    img_periph = img.copy()
    img_periph[self.gaze[0]:self.gaze[0] + pixels_h, self.gaze[1]:self.gaze[1] + pixels_w] = 0.

    observation = {
      'full': img,
      'fovea': img_fov,
      'peripheral': img_periph}

    return observation
